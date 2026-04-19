"""Adaptadores desde snapshots `.pgmx` hacia specs del sintetizador.

Este modulo toma la vista normalizada de `tools.pgmx_snapshot` y decide que
parte de un archivo Maestro existente puede traducirse a la API publica del
sintetizador actual.

Objetivos:

- refactorizar casos manuales hacia `LineMillingSpec`, `PolylineMillingSpec`,
  `CircleMillingSpec`, `SquaringMillingSpec` y `DrillingSpec`
- informar con claridad cuando una feature o working step no puede adaptarse
- construir rapido un `PgmxSynthesisRequest` con el material soportado

Regla de orden:

- la salida prioriza el orden real del workplan (`WorkingStep`)
- si hay features fuera del workplan, se agregan al final como huerfanas
- al construir el request final, la API publica del sintetizador sigue
  agrupando por familia de mecanizado; por eso no promete re-sintesis 1:1 del
  orden original entre familias distintas
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Optional

from tools import synthesize_pgmx as sp
from tools.pgmx_snapshot import (
    PgmxFeatureSnapshot,
    PgmxOperationSnapshot,
    PgmxSnapshot,
    PgmxWorkingStepSnapshot,
    read_pgmx_snapshot,
)

SupportedSynthesisSpec = (
    sp.LineMillingSpec
    | sp.PolylineMillingSpec
    | sp.CircleMillingSpec
    | sp.SquaringMillingSpec
    | sp.DrillingSpec
)

__all__ = [
    "SupportedSynthesisSpec",
    "PgmxAdaptationEntry",
    "PgmxAdaptationResult",
    "adapt_pgmx_snapshot",
    "adapt_pgmx_path",
    "adaptation_to_dict",
    "write_pgmx_adaptation_json",
]


@dataclass(frozen=True)
class PgmxAdaptationEntry:
    """Intento de adaptacion de una unidad del `.pgmx`.

    `entry_source` vale:

    - `working_step`: la entrada nace de un step del workplan
    - `feature`: la entrada nace de una feature fuera del workplan
    """

    order_index: int
    entry_source: str
    feature_id: str
    operation_id: Optional[str]
    working_step_id: Optional[str]
    feature_name: str
    working_step_name: str
    feature_type: str
    operation_type: str
    plane_name: str
    status: str
    spec_kind: Optional[str]
    spec: Optional[SupportedSynthesisSpec]
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PgmxAdaptationResult:
    """Resultado ordenado de adaptacion de un `.pgmx` existente."""

    snapshot: PgmxSnapshot
    entries: tuple[PgmxAdaptationEntry, ...]

    @property
    def adapted_entries(self) -> tuple[PgmxAdaptationEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.status == "adapted" and entry.spec is not None
        )

    @property
    def unsupported_entries(self) -> tuple[PgmxAdaptationEntry, ...]:
        return tuple(entry for entry in self.entries if entry.status == "unsupported")

    @property
    def ignored_entries(self) -> tuple[PgmxAdaptationEntry, ...]:
        return tuple(entry for entry in self.entries if entry.status == "ignored")

    @property
    def working_step_entries(self) -> tuple[PgmxAdaptationEntry, ...]:
        return tuple(entry for entry in self.entries if entry.entry_source == "working_step")

    @property
    def orphan_feature_entries(self) -> tuple[PgmxAdaptationEntry, ...]:
        return tuple(entry for entry in self.entries if entry.entry_source == "feature")

    @property
    def line_millings(self) -> tuple[sp.LineMillingSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.LineMillingSpec)
        )

    @property
    def polyline_millings(self) -> tuple[sp.PolylineMillingSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.PolylineMillingSpec)
        )

    @property
    def circle_millings(self) -> tuple[sp.CircleMillingSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.CircleMillingSpec)
        )

    @property
    def squaring_millings(self) -> tuple[sp.SquaringMillingSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.SquaringMillingSpec)
        )

    @property
    def drillings(self) -> tuple[sp.DrillingSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.DrillingSpec)
        )

    def build_synthesis_request(
        self,
        output_path: Path,
        *,
        baseline_path: Optional[Path] = None,
        source_pgmx_path: Optional[Path] = None,
        strict: bool = False,
    ) -> sp.PgmxSynthesisRequest:
        """Construye un request de sintesis con las entradas soportadas.

        Si `strict=True`, falla cuando exista al menos una entrada
        `unsupported`. Las entradas `ignored` no bloquean porque representan
        pasos administrativos fuera del subset publico.

        Nota: el request conserva el orden relativo dentro de cada familia
        soportada, pero la API publica del sintetizador sigue agrupando por
        tipo de mecanizado (`line`, `polyline`, `circle`, `squaring`, `drilling`).
        """

        if strict and self.unsupported_entries:
            messages = [
                f"{entry.feature_name or entry.feature_id}: "
                f"{'; '.join(entry.reasons or ('sin detalle',))}"
                for entry in self.unsupported_entries
            ]
            raise ValueError(
                "No se pudo construir el request porque existen entradas no adaptables:\n- "
                + "\n- ".join(messages)
            )

        return sp.build_synthesis_request(
            baseline_path=baseline_path,
            output_path=Path(output_path),
            source_pgmx_path=source_pgmx_path or self.snapshot.source_path,
            piece=self.snapshot.state,
            line_millings=self.line_millings,
            polyline_millings=self.polyline_millings,
            circle_millings=self.circle_millings,
            squaring_millings=self.squaring_millings,
            drillings=self.drillings,
        )


def _default_name(
    feature: PgmxFeatureSnapshot,
    step: Optional[PgmxWorkingStepSnapshot],
    fallback: str,
) -> str:
    if feature.name.strip():
        return feature.name.strip()
    if step is not None and step.name.strip():
        return step.name.strip()
    return fallback


def _plane_name_or_default(feature: PgmxFeatureSnapshot) -> str:
    return (feature.plane_name or "Top").strip() or "Top"


def _entry_source(step: Optional[PgmxWorkingStepSnapshot]) -> str:
    return "working_step" if step is not None else "feature"


def _linked_operation(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
    step: Optional[PgmxWorkingStepSnapshot],
) -> Optional[PgmxOperationSnapshot]:
    if step is not None and step.operation_ref is not None:
        if step.operation_ref.id:
            return snapshot.operation_by_id.get(step.operation_ref.id)
        return None
    for operation_ref in feature.operation_refs:
        operation = snapshot.operation_by_id.get(operation_ref.id)
        if operation is not None:
            return operation
    return None


def _same_security_plane(operation: PgmxOperationSnapshot) -> bool:
    return math.isclose(
        float(operation.approach_security_plane),
        float(operation.retract_security_plane),
        abs_tol=1e-6,
    )


def _resolved_tool(operation: PgmxOperationSnapshot) -> bool:
    tool = operation.tool_key
    if tool is None:
        return False
    if not tool.id or tool.id == "0":
        return False
    if tool.object_type == "System.Object":
        return False
    if not tool.name:
        return False
    return True


def _tool_warning(operation: PgmxOperationSnapshot) -> tuple[str, ...]:
    if not operation.machine_functions:
        return ()
    return (
        "La operacion contiene MachineFunctions que la API publica actual no "
        "expone; al re-sintetizarse podrian perderse.",
    )


def _builder_error(prefix: str, exc: Exception) -> str:
    detail = str(exc).strip()
    if detail:
        return f"{prefix}: {detail}"
    return prefix


def _effective_tool_width(value: Optional[float], fallback: float) -> float:
    if value is None:
        return float(fallback)
    if math.isclose(float(value), 0.0, abs_tol=1e-6):
        return float(fallback)
    return float(value)


def _unsupported_entry(
    feature: PgmxFeatureSnapshot,
    operation: Optional[PgmxOperationSnapshot],
    step: Optional[PgmxWorkingStepSnapshot],
    *,
    order_index: int,
    reasons: list[str],
    warnings: tuple[str, ...] = (),
) -> PgmxAdaptationEntry:
    return PgmxAdaptationEntry(
        order_index=order_index,
        entry_source=_entry_source(step),
        feature_id=feature.id,
        operation_id=operation.id if operation is not None else None,
        working_step_id=step.id if step is not None else None,
        feature_name=_default_name(feature, step, "Feature"),
        working_step_name=step.name if step is not None else "",
        feature_type=feature.feature_type,
        operation_type=operation.operation_type if operation is not None else "",
        plane_name=_plane_name_or_default(feature),
        status="unsupported",
        spec_kind=None,
        spec=None,
        reasons=tuple(reasons),
        warnings=warnings,
    )


def _adapted_entry(
    feature: PgmxFeatureSnapshot,
    operation: PgmxOperationSnapshot,
    step: Optional[PgmxWorkingStepSnapshot],
    *,
    order_index: int,
    spec_kind: str,
    spec: SupportedSynthesisSpec,
    warnings: tuple[str, ...] = (),
) -> PgmxAdaptationEntry:
    return PgmxAdaptationEntry(
        order_index=order_index,
        entry_source=_entry_source(step),
        feature_id=feature.id,
        operation_id=operation.id,
        working_step_id=step.id if step is not None else None,
        feature_name=_default_name(feature, step, "Feature"),
        working_step_name=step.name if step is not None else "",
        feature_type=feature.feature_type,
        operation_type=operation.operation_type,
        plane_name=_plane_name_or_default(feature),
        status="adapted",
        spec_kind=spec_kind,
        spec=spec,
        warnings=warnings,
    )


def _workplan_step_entry_without_feature(
    step: PgmxWorkingStepSnapshot,
    *,
    order_index: int,
    status: str,
    feature_id: str = "",
    operation_id: Optional[str] = None,
    reasons: list[str],
) -> PgmxAdaptationEntry:
    return PgmxAdaptationEntry(
        order_index=order_index,
        entry_source="working_step",
        feature_id=feature_id,
        operation_id=operation_id,
        working_step_id=step.id,
        feature_name=step.name.strip() or feature_id or "WorkingStep",
        working_step_name=step.name,
        feature_type="",
        operation_type="",
        plane_name="",
        status=status,
        spec_kind=None,
        spec=None,
        reasons=tuple(reasons),
        warnings=(),
    )


def _depth_kwargs(
    depth_spec: Optional[sp.MillingDepthSpec],
) -> dict[str, Optional[float] | bool]:
    if depth_spec is None:
        raise ValueError("La feature no tiene una profundidad interpretable.")
    if depth_spec.is_through:
        return {
            "is_through": True,
            "target_depth": None,
            "extra_depth": depth_spec.extra_depth,
        }
    return {
        "is_through": False,
        "target_depth": depth_spec.target_depth,
        "extra_depth": None,
    }


def _polyline_points_from_profile(
    profile: sp.GeometryProfileSpec,
) -> tuple[tuple[float, float], ...]:
    if not profile.primitives:
        raise ValueError("El perfil no tiene primitivas.")
    points: list[tuple[float, float]] = [
        (profile.primitives[0].start_point[0], profile.primitives[0].start_point[1])
    ]
    for primitive in profile.primitives:
        points.append((primitive.end_point[0], primitive.end_point[1]))
    return tuple(points)


def _matches_points(
    points_a: tuple[tuple[float, float], ...],
    points_b: tuple[tuple[float, float], ...],
    tolerance: float = 1e-6,
) -> bool:
    if len(points_a) != len(points_b):
        return False
    return all(
        math.isclose(point_a[0], point_b[0], abs_tol=tolerance)
        and math.isclose(point_a[1], point_b[1], abs_tol=tolerance)
        for point_a, point_b in zip(points_a, points_b)
    )


def _detect_squaring_signature(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
) -> Optional[tuple[str, str]]:
    geometry_ref = feature.geometry_ref
    if geometry_ref is None:
        return None
    geometry = snapshot.geometry_by_id.get(geometry_ref.id)
    if geometry is None or geometry.profile is None:
        return None
    profile = geometry.profile
    if profile.geometry_type != "GeomCompositeCurve":
        return None
    if profile.has_arcs:
        return None
    if profile.family != "ClosedPolylineMidEdgeStart":
        return None
    bounding_box = profile.bounding_box
    if bounding_box is None:
        return None
    expected_bbox = (
        0.0,
        0.0,
        float(snapshot.state.length),
        float(snapshot.state.width),
    )
    if not _matches_points(
        ((bounding_box[0], bounding_box[1]), (bounding_box[2], bounding_box[3])),
        ((expected_bbox[0], expected_bbox[1]), (expected_bbox[2], expected_bbox[3])),
    ):
        return None
    points = _polyline_points_from_profile(profile)
    for winding in ("CounterClockwise", "Clockwise"):
        expected_side = "Right" if winding == "CounterClockwise" else "Left"
        if feature.side_of_feature and feature.side_of_feature != expected_side:
            continue
        for start_edge in ("Bottom", "Right", "Top", "Left"):
            expected_points = tuple(
                (point[0], point[1])
                for point in sp._build_squaring_outline_points(
                    snapshot.state.length,
                    snapshot.state.width,
                    start_edge=start_edge,
                    winding=winding,
                )
            )
            if _matches_points(points, expected_points):
                return (start_edge, winding)
    return None


def _adapt_drilling(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
    operation: Optional[PgmxOperationSnapshot],
    step: Optional[PgmxWorkingStepSnapshot],
    *,
    order_index: int,
) -> PgmxAdaptationEntry:
    reasons: list[str] = []
    if operation is None:
        reasons.append("La feature no referencia una operacion resoluble.")
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
        )
    if "DrillingOperation" not in operation.operation_type:
        reasons.append("La operacion vinculada no es un `DrillingOperation`.")
    if feature.geometry_ref is None:
        reasons.append("La feature no referencia una geometria.")
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
        )
    geometry = snapshot.geometry_by_id.get(feature.geometry_ref.id)
    if geometry is None or geometry.point is None:
        reasons.append("La geometria del taladro no es un punto compatible.")
    if feature.diameter is None or feature.diameter <= 0.0:
        reasons.append("La feature no expone un diametro valido.")
    if feature.depth_spec is None:
        reasons.append("La profundidad de la feature no pudo inferirse.")
    if not _same_security_plane(operation):
        reasons.append(
            "ApproachSecurityPlane y RetractSecurityPlane difieren y la API "
            "publica solo expone uno."
        )
    if operation.cutting_depth is not None and not math.isclose(
        operation.cutting_depth,
        0.0,
        abs_tol=1e-6,
    ):
        reasons.append(
            "La operacion usa CuttingDepth distinto de cero y la API publica "
            "actual no lo expone."
        )
    warnings = _tool_warning(operation)
    if reasons:
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
            warnings=warnings,
        )

    plane_name = _plane_name_or_default(feature)
    bottom_condition_type = feature.bottom_condition_type
    drill_family = None
    if "ConicalHoleBottom" in bottom_condition_type:
        drill_family = "Conical"
    elif "FlatHoleBottom" in bottom_condition_type:
        drill_family = "Flat"

    tool_key = operation.tool_key
    tool_resolution = "None"
    tool_id = None
    tool_name = None
    if tool_key is not None and tool_key.id and tool_key.id != "0" and tool_key.object_type != "System.Object":
        tool_resolution = "Explicit"
        tool_id = tool_key.id
        tool_name = tool_key.name

    try:
        depth_kwargs = _depth_kwargs(feature.depth_spec)
        spec = sp.build_drilling_spec(
            center_x=geometry.point[0],
            center_y=geometry.point[1],
            diameter=float(feature.diameter),
            feature_name=_default_name(feature, step, "Taladrado"),
            plane_name=plane_name,
            security_plane=float(operation.approach_security_plane),
            is_through=bool(depth_kwargs["is_through"]),
            target_depth=depth_kwargs["target_depth"],
            extra_depth=depth_kwargs["extra_depth"],
            drill_family=drill_family,
            tool_resolution=tool_resolution,
            tool_id=tool_id,
            tool_name=tool_name,
        )
    except Exception as exc:
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=[_builder_error("No se pudo construir el `DrillingSpec`", exc)],
            warnings=warnings,
        )

    return _adapted_entry(
        feature,
        operation,
        step,
        order_index=order_index,
        spec_kind="drilling",
        spec=spec,
        warnings=warnings,
    )


def _adapt_milling(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
    operation: Optional[PgmxOperationSnapshot],
    step: Optional[PgmxWorkingStepSnapshot],
    *,
    order_index: int,
) -> PgmxAdaptationEntry:
    reasons: list[str] = []
    if operation is None:
        reasons.append("La feature no referencia una operacion resoluble.")
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
        )
    if "BottomAndSideFinishMilling" not in operation.operation_type:
        reasons.append("La operacion vinculada no es un `BottomAndSideFinishMilling`.")
    if _plane_name_or_default(feature) != "Top":
        reasons.append(
            "La API publica actual de fresado solo expone `Top` para "
            "linea/polilinea/escuadrado."
        )
    if feature.geometry_ref is None:
        reasons.append("La feature no referencia una geometria.")
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
        )
    geometry = snapshot.geometry_by_id.get(feature.geometry_ref.id)
    if geometry is None or geometry.profile is None:
        reasons.append("La geometria de la feature no pudo resolverse.")
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
        )
    if feature.depth_spec is None:
        reasons.append("La profundidad de la feature no pudo inferirse.")
    if not _same_security_plane(operation):
        reasons.append(
            "ApproachSecurityPlane y RetractSecurityPlane difieren y la API "
            "publica solo expone uno."
        )
    if not _resolved_tool(operation):
        reasons.append(
            "La operacion no tiene una herramienta resuelta compatible con la "
            "API publica de fresado."
        )
    if operation.allowance_bottom is not None and not math.isclose(
        operation.allowance_bottom,
        0.0,
        abs_tol=1e-6,
    ):
        reasons.append("AllowanceBottom es distinto de cero y la API publica actual no lo expone.")
    if operation.allowance_side is not None and not math.isclose(
        operation.allowance_side,
        0.0,
        abs_tol=1e-6,
    ):
        reasons.append("AllowanceSide es distinto de cero y la API publica actual no lo expone.")
    warnings = _tool_warning(operation)
    if reasons:
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=reasons,
            warnings=warnings,
        )

    depth_kwargs = _depth_kwargs(feature.depth_spec)
    tool_key = operation.tool_key
    feature_name = _default_name(feature, step, "Fresado")
    approach = operation.approach or sp.build_approach_spec()
    retract = operation.retract or sp.build_retract_spec()
    profile = geometry.profile

    squaring_signature = _detect_squaring_signature(snapshot, feature)
    if squaring_signature is not None:
        start_edge, winding = squaring_signature
        try:
            spec = sp.build_squaring_milling_spec(
                start_edge=start_edge,
                winding=winding,
                feature_name=feature_name,
                tool_id=tool_key.id,
                tool_name=tool_key.name,
                tool_width=_effective_tool_width(feature.tool_width, 18.36),
                security_plane=float(operation.approach_security_plane),
                is_through=bool(depth_kwargs["is_through"]),
                target_depth=depth_kwargs["target_depth"],
                extra_depth=depth_kwargs["extra_depth"],
                approach_enabled=approach.is_enabled,
                approach_type=approach.approach_type,
                approach_mode=approach.mode,
                approach_radius_multiplier=approach.radius_multiplier,
                approach_speed=approach.speed,
                approach_arc_side=approach.arc_side,
                retract_enabled=retract.is_enabled,
                retract_type=retract.retract_type,
                retract_mode=retract.mode,
                retract_radius_multiplier=retract.radius_multiplier,
                retract_speed=retract.speed,
                retract_arc_side=retract.arc_side,
                retract_overlap=retract.overlap,
                milling_strategy=operation.milling_strategy,
            )
        except Exception as exc:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[_builder_error("No se pudo construir el `SquaringMillingSpec`", exc)],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="squaring_milling",
            spec=spec,
            warnings=warnings,
        )

    if profile.geometry_type == "GeomTrimmedCurve" and profile.primitive_count == 1:
        primitive = profile.primitives[0]
        if primitive.primitive_type != "Line":
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=["La geometria lineal no corresponde a una recta simple."],
                warnings=warnings,
            )
        try:
            spec = sp.build_line_milling_spec(
                primitive.start_point[0],
                primitive.start_point[1],
                primitive.end_point[0],
                primitive.end_point[1],
                feature_name,
                tool_key.id,
                tool_key.name,
                _effective_tool_width(feature.tool_width, 9.52),
                float(operation.approach_security_plane),
                line_side_of_feature=feature.side_of_feature or "Center",
                line_is_through=bool(depth_kwargs["is_through"]),
                line_target_depth=depth_kwargs["target_depth"],
                line_extra_depth=depth_kwargs["extra_depth"],
                line_approach_enabled=approach.is_enabled,
                line_approach_type=approach.approach_type,
                line_approach_mode=approach.mode,
                line_approach_radius_multiplier=approach.radius_multiplier,
                line_approach_speed=approach.speed,
                line_approach_arc_side=approach.arc_side,
                line_retract_enabled=retract.is_enabled,
                line_retract_type=retract.retract_type,
                line_retract_mode=retract.mode,
                line_retract_radius_multiplier=retract.radius_multiplier,
                line_retract_speed=retract.speed,
                line_retract_arc_side=retract.arc_side,
                line_retract_overlap=retract.overlap,
                line_milling_strategy=operation.milling_strategy,
            )
        except Exception as exc:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[_builder_error("No se pudo construir el `LineMillingSpec`", exc)],
                warnings=warnings,
            )
        if spec is None:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=["No se pudo construir el `LineMillingSpec`."],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="line_milling",
            spec=spec,
            warnings=warnings,
        )

    if profile.geometry_type == "GeomCompositeCurve":
        if profile.has_arcs:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[
                    "La geometria contiene arcos y hoy no existe un spec "
                    "publico equivalente en el sintetizador."
                ],
                warnings=warnings,
            )
        try:
            points = _polyline_points_from_profile(profile)
            spec = sp.build_polyline_milling_spec(
                points=points,
                feature_name=feature_name,
                tool_id=tool_key.id,
                tool_name=tool_key.name,
                tool_width=_effective_tool_width(feature.tool_width, 9.52),
                security_plane=float(operation.approach_security_plane),
                side_of_feature=feature.side_of_feature or "Center",
                is_through=bool(depth_kwargs["is_through"]),
                target_depth=depth_kwargs["target_depth"],
                extra_depth=depth_kwargs["extra_depth"],
                approach_enabled=approach.is_enabled,
                approach_type=approach.approach_type,
                approach_mode=approach.mode,
                approach_radius_multiplier=approach.radius_multiplier,
                approach_speed=approach.speed,
                approach_arc_side=approach.arc_side,
                retract_enabled=retract.is_enabled,
                retract_type=retract.retract_type,
                retract_mode=retract.mode,
                retract_radius_multiplier=retract.radius_multiplier,
                retract_speed=retract.speed,
                retract_arc_side=retract.arc_side,
                retract_overlap=retract.overlap,
                milling_strategy=operation.milling_strategy,
            )
        except Exception as exc:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[_builder_error("No se pudo construir el `PolylineMillingSpec`", exc)],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="polyline_milling",
            spec=spec,
            warnings=warnings,
        )

    if profile.geometry_type == "GeomCircle":
        if profile.center_point is None or profile.radius is None:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=["La geometria circular no expone centro/radio resolubles en el snapshot."],
                warnings=warnings,
            )
        try:
            spec = sp.build_circle_milling_spec(
                center_x=profile.center_point[0],
                center_y=profile.center_point[1],
                radius=profile.radius,
                winding=profile.winding,
                feature_name=feature_name,
                tool_id=tool_key.id,
                tool_name=tool_key.name,
                tool_width=_effective_tool_width(feature.tool_width, 9.52),
                security_plane=float(operation.approach_security_plane),
                side_of_feature=feature.side_of_feature or "Center",
                is_through=bool(depth_kwargs["is_through"]),
                target_depth=depth_kwargs["target_depth"],
                extra_depth=depth_kwargs["extra_depth"],
                approach_enabled=approach.is_enabled,
                approach_type=approach.approach_type,
                approach_mode=approach.mode,
                approach_radius_multiplier=approach.radius_multiplier,
                approach_speed=approach.speed,
                approach_arc_side=approach.arc_side,
                retract_enabled=retract.is_enabled,
                retract_type=retract.retract_type,
                retract_mode=retract.mode,
                retract_radius_multiplier=retract.radius_multiplier,
                retract_speed=retract.speed,
                retract_arc_side=retract.arc_side,
                retract_overlap=retract.overlap,
                milling_strategy=operation.milling_strategy,
            )
        except Exception as exc:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[_builder_error("No se pudo construir el `CircleMillingSpec`", exc)],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="circle_milling",
            spec=spec,
            warnings=warnings,
        )

    return _unsupported_entry(
        feature,
        operation,
        step,
        order_index=order_index,
        reasons=[f"La geometria `{profile.geometry_type}` no tiene un adaptador publico disponible."],
        warnings=warnings,
    )


def _adapt_feature(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
    step: Optional[PgmxWorkingStepSnapshot],
    *,
    order_index: int,
) -> PgmxAdaptationEntry:
    operation = _linked_operation(snapshot, feature, step)
    if "RoundHole" in feature.feature_type:
        return _adapt_drilling(
            snapshot,
            feature,
            operation,
            step,
            order_index=order_index,
        )
    if "GeneralProfileFeature" in feature.feature_type:
        return _adapt_milling(
            snapshot,
            feature,
            operation,
            step,
            order_index=order_index,
        )
    return _unsupported_entry(
        feature,
        operation,
        step,
        order_index=order_index,
        reasons=[f"La feature `{feature.feature_type}` no tiene un adaptador implementado."],
        warnings=_tool_warning(operation) if operation is not None else (),
    )


def adapt_pgmx_snapshot(snapshot: PgmxSnapshot) -> PgmxAdaptationResult:
    """Adapta un snapshot al subconjunto publico del sintetizador.

    `entries` conserva primero el orden del workplan y luego agrega al final las
    features que no aparecian referenciadas por ningun `WorkingStep`.
    """

    entries: list[PgmxAdaptationEntry] = []
    feature_ids_seen_in_workplan: set[str] = set()

    for step in snapshot.working_steps:
        feature_ref = step.manufacturing_feature_ref
        order_index = len(entries)
        if feature_ref is None or not feature_ref.id:
            entries.append(
                _workplan_step_entry_without_feature(
                    step,
                    order_index=order_index,
                    status="ignored",
                    operation_id=step.operation_ref.id if step.operation_ref is not None else None,
                    reasons=[
                        "El working step no referencia una manufacturing feature y se "
                        "omite del subset publico."
                    ],
                )
            )
            continue

        feature = snapshot.feature_by_id.get(feature_ref.id)
        if feature is None:
            entries.append(
                _workplan_step_entry_without_feature(
                    step,
                    order_index=order_index,
                    status="unsupported",
                    feature_id=feature_ref.id,
                    operation_id=step.operation_ref.id if step.operation_ref is not None else None,
                    reasons=[
                        f"El working step referencia la feature `{feature_ref.id}` "
                        "pero no existe en el snapshot."
                    ],
                )
            )
            continue

        feature_ids_seen_in_workplan.add(feature.id)
        entries.append(
            _adapt_feature(
                snapshot,
                feature,
                step,
                order_index=order_index,
            )
        )

    for feature in snapshot.features:
        if feature.id in feature_ids_seen_in_workplan:
            continue
        entries.append(
            _adapt_feature(
                snapshot,
                feature,
                None,
                order_index=len(entries),
            )
        )

    return PgmxAdaptationResult(snapshot=snapshot, entries=tuple(entries))


def adapt_pgmx_path(path: Path) -> PgmxAdaptationResult:
    """Conveniencia: lee el snapshot y luego adapta sus features."""

    return adapt_pgmx_snapshot(read_pgmx_snapshot(path))


def adaptation_to_dict(result: PgmxAdaptationResult) -> dict[str, Any]:
    """Convierte el resultado de adaptacion a un diccionario JSON-friendly."""

    def convert(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if is_dataclass(value):
            return {
                field.name: convert(getattr(value, field.name))
                for field in fields(value)
                if field.name != "snapshot"
            }
        if isinstance(value, tuple):
            return [convert(item) for item in value]
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        return value

    return {
        "source_path": str(result.snapshot.source_path),
        "piece": convert(result.snapshot.state),
        "counts": {
            "entries": len(result.entries),
            "adapted": len(result.adapted_entries),
            "unsupported": len(result.unsupported_entries),
            "ignored": len(result.ignored_entries),
            "working_step_entries": len(result.working_step_entries),
            "orphan_feature_entries": len(result.orphan_feature_entries),
            "line_millings": len(result.line_millings),
            "polyline_millings": len(result.polyline_millings),
            "circle_millings": len(result.circle_millings),
            "squaring_millings": len(result.squaring_millings),
            "drillings": len(result.drillings),
        },
        "entries": convert(result.entries),
    }


def write_pgmx_adaptation_json(
    result: PgmxAdaptationResult,
    output_path: Path,
    *,
    indent: int = 2,
) -> Path:
    output_path.write_text(
        json.dumps(adaptation_to_dict(result), indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adapta un `.pgmx` existente a specs del sintetizador."
    )
    parser.add_argument("pgmx_path", help="Ruta al archivo .pgmx a adaptar.")
    parser.add_argument(
        "--output",
        help="Ruta de salida JSON. Si no se indica, imprime por stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentacion del JSON de salida.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    result = adapt_pgmx_path(Path(args.pgmx_path))
    payload = json.dumps(
        adaptation_to_dict(result),
        indent=int(args.indent),
        ensure_ascii=False,
    )
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
