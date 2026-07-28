"""Adaptadores desde snapshots `.pgmx` hacia specs del sintetizador.

Este modulo toma la vista normalizada de `pgmx.snapshot` y decide que
parte de un archivo Maestro existente puede traducirse a la API publica del
sintetizador actual.

Objetivos:

- refactorizar casos manuales hacia `LineSpec`, `ChannelSpec`,
  `PolylineSpec`, `CircleSpec`, `ContourSpec` y
  `DrillSpec`/`DrillPatternSpec`
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
from dataclasses import dataclass, fields, is_dataclass, replace as _dc_replace
from pathlib import Path
from typing import Any, Optional

from pgmx import synthesis as sp
from pgmx.snapshot import (
    PgmxFeatureSnapshot,
    PgmxOperationSnapshot,
    PgmxSnapshot,
    PgmxWorkingStepSnapshot,
    read_pgmx_snapshot,
)

SupportedSynthesisSpec = (
    sp.LineSpec
    | sp.ChannelSpec
    | sp.ArcSpec
    | sp.PolylineSpec
    | sp.CircleSpec
    | sp.ContourSpec
    | sp.PocketSpec
    | sp.DrillSpec
    | sp.DrillPatternSpec
)

__all__ = [
    "SupportedSynthesisSpec",
    "PgmxAdaptationEntry",
    "PgmxAdaptationResult",
    "adapt_pgmx_snapshot",
    "adapt_pgmx_path",
    "adaptation_to_dict",
    "main",
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
    def lines(self) -> tuple[sp.LineSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.LineSpec)
        )

    @property
    def channels(self) -> tuple[sp.ChannelSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.ChannelSpec)
        )

    @property
    def polylines(self) -> tuple[sp.PolylineSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.PolylineSpec)
        )

    @property
    def arcs(self) -> tuple[sp.ArcSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.ArcSpec)
        )

    @property
    def circles(self) -> tuple[sp.CircleSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.CircleSpec)
        )

    @property
    def contours(self) -> tuple[sp.ContourSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.ContourSpec)
        )

    @property
    def pockets(self) -> tuple[sp.PocketSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.PocketSpec)
        )

    @property
    def drills(self) -> tuple[sp.DrillSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.DrillSpec)
        )

    @property
    def drill_patterns(self) -> tuple[sp.DrillPatternSpec, ...]:
        return tuple(
            entry.spec
            for entry in self.adapted_entries
            if isinstance(entry.spec, sp.DrillPatternSpec)
        )

    @property
    def xn(self) -> Optional[sp.XnSpec]:
        """Devuelve la ultima operacion `Xn` del workplan como spec sintetizable."""

        for step in reversed(self.snapshot.working_steps):
            if step.runtime_type == "Xn":
                return _xn_spec_from_step(step)
        return None

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
        tipo de mecanizado (`line`, `slot`, `polyline`, `circle`, `squaring`,
        `drilling`, `drilling_pattern`).
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
            lines=self.lines,
            channels=self.channels,
            polylines=self.polylines,
            arcs=self.arcs,
            circles=self.circles,
            contours=self.contours,
            pockets=self.pockets,
            drills=self.drills,
            drill_patterns=self.drill_patterns,
            xn=self.xn,
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


def _tool_diameter_from_snapshot(
    snapshot: PgmxSnapshot,
    operation: PgmxOperationSnapshot,
) -> Optional[float]:
    if operation.tool_key is None:
        return None
    for tool in snapshot.embedded_tools:
        if tool.id == operation.tool_key.id:
            return tool.diameter
    return None


def _is_horizontal_line_primitive(primitive) -> bool:
    return math.isclose(
        float(primitive.start_point[1]),
        float(primitive.end_point[1]),
        abs_tol=1e-6,
    )


def _slot_end_radius(feature: PgmxFeatureSnapshot) -> float:
    radii = [
        float(end.radius)
        for end in feature.end_conditions
        if end.radius is not None
    ]
    if not radii:
        return 60.0
    return radii[0]


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


def _xn_spec_from_step(step: PgmxWorkingStepSnapshot) -> sp.XnSpec:
    tool_ref = step.tool_ref
    return sp.build_xn_spec(
        name=step.name,
        reference=step.reference,
        speed=step.speed,
        spindle_enable=step.spindle_enable,
        x=step.x,
        y=step.y,
        tool_id=tool_ref.id if tool_ref is not None else None,
        tool_object_type=tool_ref.object_type if tool_ref is not None else None,
        tool_name=tool_ref.name if tool_ref is not None else None,
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


def _xy_points_from_curve_snapshot(curve) -> tuple[tuple[float, float], ...]:
    return tuple((float(point[0]), float(point[1])) for point in curve.sampled_points)


def _stored_trajectory_primitives(operation) -> tuple[sp.GeometryPrimitiveSpec, ...]:
    """Primitivas 3D del TrajectoryPath ALMACENADO de la operación (los strokes de la
    GeomCompositeCurve, parseados). Con ACC=false Maestro postprocesa lo almacenado tal cual
    (N046: copia, no recalcula) — el ZigZag CAD del converter lee de acá la Z de cada
    movimiento. Devuelve () si no hay composite o algún miembro no parsea (el consumidor
    decide fail-loud)."""
    for toolpath in operation.toolpaths:
        if toolpath.path_type != "TrajectoryPath" or toolpath.curve is None:
            continue
        if toolpath.curve.geometry_type != "GeomCompositeCurve":
            return ()
        primitives: list[sp.GeometryPrimitiveSpec] = []
        for text in toolpath.curve.member_serializations:
            primitive = sp._parse_geometry_primitive(text)
            if primitive is None:
                return ()
            primitives.append(primitive)
        return tuple(primitives)
    return ()


def _boss_route_seeds_from_feature(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
) -> tuple[sp.PocketBossRouteSeedSpec, ...]:
    route_seeds: list[sp.PocketBossRouteSeedSpec] = []
    for ref in feature.boss_refs:
        geometry = snapshot.geometry_by_id.get(ref.id)
        contour: tuple[tuple[float, float], ...] = ()
        if geometry is not None and geometry.profile is not None:
            try:
                contour = _polyline_points_from_profile(geometry.profile)
            except ValueError:
                contour = ()
        route_seeds.append(
            sp.build_pocket_boss_route_seed_spec(
                geometry_id=ref.id,
                object_type=ref.object_type,
                name=ref.name,
                contour_points=contour,
            )
        )
    return tuple(route_seeds)


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


def _closed_points(points: tuple[tuple[float, float], ...], tolerance: float = 1e-6) -> bool:
    if len(points) < 4:
        return False
    return (
        math.isclose(points[0][0], points[-1][0], abs_tol=tolerance)
        and math.isclose(points[0][1], points[-1][1], abs_tol=tolerance)
    )


def _point_on_interval(value: float, lower: float, upper: float, tolerance: float) -> bool:
    return lower - tolerance <= value <= upper + tolerance


def _boundary_edge_for_point(
    point: tuple[float, float],
    *,
    length: float,
    width: float,
    tolerance: float = 1e-6,
) -> Optional[str]:
    point_x, point_y = point
    if math.isclose(point_y, 0.0, abs_tol=tolerance) and _point_on_interval(
        point_x,
        0.0,
        length,
        tolerance,
    ):
        return "Bottom"
    if math.isclose(point_x, length, abs_tol=tolerance) and _point_on_interval(
        point_y,
        0.0,
        width,
        tolerance,
    ):
        return "Right"
    if math.isclose(point_y, width, abs_tol=tolerance) and _point_on_interval(
        point_x,
        0.0,
        length,
        tolerance,
    ):
        return "Top"
    if math.isclose(point_x, 0.0, abs_tol=tolerance) and _point_on_interval(
        point_y,
        0.0,
        width,
        tolerance,
    ):
        return "Left"
    return None


def _signed_area(points: tuple[tuple[float, float], ...]) -> float:
    area = 0.0
    for current_point, next_point in zip(points, points[1:]):
        area += (current_point[0] * next_point[1]) - (next_point[0] * current_point[1])
    return area / 2.0


def _detect_squaring_signature(
    snapshot: PgmxSnapshot,
    feature: PgmxFeatureSnapshot,
) -> Optional[tuple[str, str, float]]:
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
    if not profile.is_closed:
        return None
    bounding_box = profile.bounding_box
    if bounding_box is None:
        return None
    length = float(snapshot.state.length)
    width = float(snapshot.state.width)
    expected_bbox = (
        0.0,
        0.0,
        length,
        width,
    )
    if not _matches_points(
        ((bounding_box[0], bounding_box[1]), (bounding_box[2], bounding_box[3])),
        ((expected_bbox[0], expected_bbox[1]), (expected_bbox[2], expected_bbox[3])),
    ):
        return None
    points = _polyline_points_from_profile(profile)
    if not _closed_points(points):
        return None
    if any(
        _boundary_edge_for_point(point, length=length, width=width) is None
        for point in points
    ):
        return None

    expected_area = length * width
    signed_area = _signed_area(points)
    if not math.isclose(
        abs(signed_area),
        expected_area,
        abs_tol=max(1e-3, expected_area * 1e-6),
    ):
        return None

    winding = "CounterClockwise" if signed_area > 0.0 else "Clockwise"
    expected_side = "Right" if winding == "CounterClockwise" else "Left"
    if feature.side_of_feature and feature.side_of_feature != expected_side:
        return None

    start_edge = _boundary_edge_for_point(points[0], length=length, width=width)
    if start_edge is None:
        return None
    start_coordinate = points[0][0] if start_edge in {"Bottom", "Top"} else points[0][1]
    # La firma detecta la FORMA CANÓNICA de En-Juego (build_contour_spec): arranque a MITAD
    # del borde inicial (borde partido en 2 tramos). Un perímetro que arranca en otro punto
    # (los N043 arrancan en una ESQUINA) NO es esa forma: ContourSpec la re-autoraría con el
    # arranque a mitad de borde — otra geometría (el punto inicial IMPORTA) — así que va por
    # la rama polilínea, que conserva el arranque real.
    edge_length = length if start_edge in {"Bottom", "Top"} else width
    if not math.isclose(float(start_coordinate), edge_length / 2.0, abs_tol=1e-6):
        return None
    return (start_edge, winding, float(start_coordinate))


def _drill_family_from_bottom(bottom_condition_type: str,
                              bottom_is_flat: Optional[bool]) -> Optional[str]:
    """Familia de punta del taladro a partir del BottomCondition.

    En agujeros ciegos el tipo lo da el xsi:type (Conical/FlatHoleBottom). En pasantes
    el tipo es 'ThroughHoleBottom' y la punta está en IsFlat (true=plana, false=cónica);
    sin IsFlat se devuelve None y el default del builder decide.
    """
    if "ConicalHoleBottom" in bottom_condition_type:
        return "Conical"
    if "FlatHoleBottom" in bottom_condition_type:
        return "Flat"
    if "ThroughHoleBottom" in bottom_condition_type and bottom_is_flat is not None:
        return "Flat" if bottom_is_flat else "Conical"
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
    drill_family = _drill_family_from_bottom(
        feature.bottom_condition_type, feature.bottom_is_flat)

    tool_key = operation.tool_key
    tool_resolution = "None"
    tool_id = None
    tool_name = None
    if tool_key is not None and tool_key.id and tool_key.id != "0" and tool_key.object_type != "System.Object":
        tool_resolution = "Explicit"
        tool_id = tool_key.id
        tool_name = tool_key.name

    technology = operation.technology
    feedrate = float(technology.feedrate) if technology is not None else 0.0
    spindle = float(technology.spindle) if technology is not None else 0.0
    taper_height = float(feature.taper_height) if feature.taper_height is not None else 0.0

    try:
        depth_kwargs = _depth_kwargs(feature.depth_spec)
        spec = sp.build_drill_spec(
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
            feedrate=feedrate,
            spindle=spindle,
            taper_height=taper_height,
            step_number=operation.step_number,
            step_depth=operation.step_depth,
        )
    except Exception as exc:
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=[_builder_error("No se pudo construir el `DrillSpec`", exc)],
            warnings=warnings,
        )

    return _adapted_entry(
        feature,
        operation,
        step,
        order_index=order_index,
        spec_kind="drill",
        spec=spec,
        warnings=warnings,
    )


def _replicated_depth_kwargs(feature: PgmxFeatureSnapshot) -> Optional[dict[str, Any]]:
    base_feature = feature.base_feature
    if base_feature is None:
        return None
    if "ThroughHoleBottom" in base_feature.bottom_condition_type:
        return {"is_through": True, "target_depth": None, "extra_depth": 0.0}
    if base_feature.depth_end is None:
        return None
    return {"is_through": False, "target_depth": float(base_feature.depth_end), "extra_depth": 0.0}


def _adapt_drilling_pattern(
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
        reasons.append("La geometria del patron de taladros no es un punto compatible.")

    pattern = feature.replication_pattern
    if pattern is None:
        reasons.append("La feature no expone `ReplicationPattern`.")
    elif "RectangularPattern" not in pattern.pattern_type:
        reasons.append(f"El patron `{pattern.pattern_type}` no tiene adaptador publico.")
    elif not math.isclose(pattern.rotation_angle, 0.0, abs_tol=1e-9):
        reasons.append("Solo se adapta `RectangularPattern` con `RotationAngle = 0`.")
    elif not math.isclose(pattern.row_layout_angle, 90.0, abs_tol=1e-9):
        reasons.append("Solo se adapta `RectangularPattern` con `RowLayoutAngle = 90`.")

    base_feature = feature.base_feature
    if base_feature is None:
        reasons.append("La feature no expone `BaseFeature`.")
    elif "RoundHole" not in base_feature.feature_type:
        reasons.append(f"El `BaseFeature` `{base_feature.feature_type}` no es un `RoundHole`.")
    elif base_feature.diameter is None or base_feature.diameter <= 0.0:
        reasons.append("El `BaseFeature` no expone un diametro valido.")

    depth_kwargs = _replicated_depth_kwargs(feature)
    if depth_kwargs is None:
        reasons.append("La profundidad del `BaseFeature` no pudo inferirse.")
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
    assert pattern is not None
    assert base_feature is not None
    assert geometry is not None
    assert depth_kwargs is not None
    drill_family = _drill_family_from_bottom(
        base_feature.bottom_condition_type, base_feature.bottom_is_flat)

    tool_key = operation.tool_key
    tool_resolution = "None"
    tool_id = None
    tool_name = None
    if tool_key is not None and tool_key.id and tool_key.id != "0" and tool_key.object_type != "System.Object":
        tool_resolution = "Explicit"
        tool_id = tool_key.id
        tool_name = tool_key.name

    try:
        spec = sp.build_drill_pattern_spec(
            geometry.point[0],
            geometry.point[1],
            float(base_feature.diameter),
            columns=pattern.number_of_columns,
            rows=pattern.number_of_rows,
            spacing=pattern.spacing,
            row_spacing=pattern.row_spacing,
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
            reasons=[_builder_error("No se pudo construir el `DrillPatternSpec`", exc)],
            warnings=warnings,
        )

    return _adapted_entry(
        feature,
        operation,
        step,
        order_index=order_index,
        spec_kind="drill_pattern",
        spec=spec,
        warnings=warnings,
    )


def _adapt_pocket_milling(
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
    if "ClosedPocket" not in feature.feature_type:
        reasons.append("La feature no es un `ClosedPocket`.")
    if "BottomAndSideRoughMilling" not in operation.operation_type:
        reasons.append("La operacion vinculada no es un `BottomAndSideRoughMilling`.")
    if not isinstance(operation.milling_strategy, sp.ContourParallelMillingStrategySpec):
        reasons.append("La estrategia vinculada no es `ContourParallel`.")
    if _plane_name_or_default(feature) != "Top":
        reasons.append("El adaptador inicial de `Vaciado` solo soporta plano `Top`.")
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
    profile = geometry.profile
    if profile.geometry_type != "GeomCompositeCurve" or not profile.is_closed:
        reasons.append("La geometria del `ClosedPocket` no es un contorno compuesto cerrado.")
    if profile.has_arcs:
        reasons.append("El adaptador inicial de `Vaciado` todavia no representa contornos con arcos.")
    boss_contours = tuple(
        contour
        for contour in (_xy_points_from_curve_snapshot(curve) for curve in feature.boss_geometry_curves)
        if contour
    )
    if len(boss_contours) != len(feature.boss_geometry_curves):
        reasons.append("No se pudieron resolver todas las geometrias de isla del `ClosedPocket`.")
    boss_route_seeds = _boss_route_seeds_from_feature(snapshot, feature)
    if feature.depth_spec is None:
        reasons.append("La profundidad de la feature no pudo inferirse.")
    if not _same_security_plane(operation):
        reasons.append(
            "ApproachSecurityPlane y RetractSecurityPlane difieren y la API publica solo expone uno."
        )
    if not _resolved_tool(operation):
        reasons.append("La operacion no tiene una herramienta resuelta compatible.")

    warnings = _tool_warning(operation) + (
        "`PocketSpec` se adapta para lectura; la serializacion productiva con islas "
        "todavia no esta implementada.",
    )
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
    approach = operation.approach or sp.build_approach_spec()
    retract = operation.retract or sp.build_retract_spec()
    try:
        spec = sp.build_pocket_spec(
            contour_points=_polyline_points_from_profile(profile),
            feature_name=_default_name(feature, step, "Vaciado"),
            plane_name=_plane_name_or_default(feature),
            tool_id=tool_key.id,
            tool_name=tool_key.name,
            tool_width=_effective_tool_width(
                feature.tool_width,
                _tool_diameter_from_snapshot(snapshot, operation) or 18.36,
            ),
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
            allowance_bottom=operation.allowance_bottom,
            allowance_side=operation.allowance_side,
            boss_contours=boss_contours,
            boss_route_seeds=boss_route_seeds,
        )
    except Exception as exc:
        return _unsupported_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            reasons=[_builder_error("No se pudo construir el `PocketSpec`", exc)],
            warnings=warnings,
        )
    return _adapted_entry(
        feature,
        operation,
        step,
        order_index=order_index,
        spec_kind="pocket",
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
    is_slot_side = "SlotSide" in feature.feature_type or "SlotSide" in feature.object_type

    if is_slot_side:
        if profile.geometry_type != "GeomTrimmedCurve" or profile.primitive_count != 1:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=["`SlotSide` solo se adapta por ahora cuando la geometria es una recta simple."],
                warnings=warnings,
            )
        primitive = profile.primitives[0]
        if primitive.primitive_type != "Line":
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=["`SlotSide` no referencia una recta simple."],
                warnings=warnings,
            )
        if not _is_horizontal_line_primitive(primitive):
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[
                    "`SlotSide` con Sierra Vertical X requiere una recta horizontal sobre `Top`; "
                    "el recorrido vertical no es ejecutable en CNC."
                ],
                warnings=warnings,
            )
        try:
            spec = sp.build_channel_spec(
                start_x=primitive.start_point[0],
                start_y=primitive.start_point[1],
                end_x=primitive.end_point[0],
                end_y=primitive.end_point[1],
                feature_name=feature_name,
                plane_name=_plane_name_or_default(feature),
                side_of_feature=feature.side_of_feature or "Center",
                tool_id=tool_key.id,
                tool_name=tool_key.name,
                tool_width=_effective_tool_width(feature.tool_width, 3.8),
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
                material_position=feature.material_position or "Left",
                side_offset=feature.side_offset,
                end_radius=_slot_end_radius(feature),
                slot_angle=feature.slot_angle,
            )
        except Exception as exc:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[_builder_error("No se pudo construir el `ChannelSpec`", exc)],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="channel",
            spec=spec,
            warnings=warnings,
        )

    # El intercept del escuadrado SOLO cuando ContourSpec puede representar la operación:
    # ACC=true (no tiene campo de corrección CAD — el Fresado-Escuadrado CAD de N043 perdía
    # el ActivateCNCCorrection=false EN SILENCIO) y estrategia None/Uni/Bi (su allowlist).
    # Lo demás cae a la rama polilínea, que sí conserva ACC y arranque reales.
    _contour_strategy_ok = (
        operation.milling_strategy is None
        or isinstance(operation.milling_strategy,
                      (sp.UnidirectionalMillingStrategySpec, sp.BidirectionalMillingStrategySpec))
    )
    squaring_signature = (
        _detect_squaring_signature(snapshot, feature)
        if operation.activate_cnc_correction and _contour_strategy_ok
        else None
    )
    if squaring_signature is not None:
        start_edge, winding, start_coordinate = squaring_signature
        try:
            spec = sp.build_contour_spec(
                start_edge=start_edge,
                winding=winding,
                start_coordinate=start_coordinate,
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
                reasons=[_builder_error("No se pudo construir el `ContourSpec`", exc)],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="contour",
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
            spec = sp.build_line_spec(
                primitive.start_point[0],
                primitive.start_point[1],
                primitive.end_point[0],
                primitive.end_point[1],
                feature_name,
                tool_key.id,
                tool_key.name,
                _effective_tool_width(feature.tool_width, 9.52),
                float(operation.approach_security_plane),
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
            # Estrategia con "Habilitar multipaso" APAGADO ≡ SIN estrategia (N036 strat_single:
            # regenerada en Maestro, el cuerpo es idéntico al fresado plano) → se anula acá para
            # que el converter la trate igual que None.
            _strategy = operation.milling_strategy
            if (spec is not None and _strategy is not None
                    and not getattr(_strategy, "allow_multiple_passes", True)):
                spec = _dc_replace(spec, milling_strategy=None)
            # Cambios durante el recorrido (SpeedAttribute/DepthAttribute del snapshot): el builder
            # no los recibe (solo lectura); se cablean por replace sobre el spec construido.
            _tech = operation.technology
            _line_feed = float(_tech.feedrate) if _tech is not None else 0.0
            _line_spindle = float(_tech.spindle) if _tech is not None else 0.0
            if spec is not None and (
                operation.speed_changes or operation.depth_changes
                or feature.side_offset or feature.is_precise
                or operation.allowance_side or operation.allowance_bottom
                or not operation.activate_cnc_correction
                or _line_feed or _line_spindle
                or feature.is_geom_same_direction is False
            ):
                spec = _dc_replace(
                    spec,
                    speed_changes=operation.speed_changes,
                    depth_changes=operation.depth_changes,
                    side_offset=feature.side_offset or 0.0,
                    allowance_side=operation.allowance_side or 0.0,
                    allowance_bottom=operation.allowance_bottom or 0.0,
                    is_precise=bool(feature.is_precise),
                    activate_cnc_correction=bool(operation.activate_cnc_correction),
                    feedrate=_line_feed,
                    spindle=_line_spindle,
                    invert_work=feature.is_geom_same_direction is False,
                )
        except Exception as exc:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=[_builder_error("No se pudo construir el `LineSpec`", exc)],
                warnings=warnings,
            )
        if spec is None:
            return _unsupported_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                reasons=["No se pudo construir el `LineSpec`."],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="line",
            spec=spec,
            warnings=warnings,
        )

    if profile.geometry_type == "GeomCompositeCurve":
        # ARCO SUELTO (Eje B etapa 2): composite de UN miembro-arco -> ArcSpec. El
        # winding sale del signo de la normal Z (build_arc_geometry_primitive: +1 CCW / -1 CW).
        if (len(profile.primitives) == 1
                and profile.primitives[0].primitive_type == "Arc"
                and profile.primitives[0].center_point is not None):
            arc = profile.primitives[0]
            winding = ("CounterClockwise"
                       if (arc.normal_vector is None or arc.normal_vector[2] >= 0)
                       else "Clockwise")
            try:
                spec = sp.build_arc_spec(
                    start_x=arc.start_point[0], start_y=arc.start_point[1],
                    end_x=arc.end_point[0], end_y=arc.end_point[1],
                    center_x=arc.center_point[0], center_y=arc.center_point[1],
                    winding=winding,
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
                    reasons=[_builder_error("No se pudo construir el `ArcSpec`", exc)],
                    warnings=warnings,
                )
            return _adapted_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                spec_kind="arc",
                spec=spec,
                warnings=warnings,
            )
        # POLILINEA UNIFICADA: todo composite (con o sin arcos) -> una sola spec de segmentos
        # (recta = endpoint; arco = endpoint + centro + winding por signo de la normal Z).
        if True:
            try:
                segments = []
                for prim in profile.primitives:
                    if prim.primitive_type == "Arc" and prim.center_point is not None:
                        winding = ("CounterClockwise"
                                   if (prim.normal_vector is None or prim.normal_vector[2] >= 0)
                                   else "Clockwise")
                        segments.append(((prim.end_point[0], prim.end_point[1]),
                                         (prim.center_point[0], prim.center_point[1]), winding))
                    else:
                        segments.append(((prim.end_point[0], prim.end_point[1]),))
                start = (profile.primitives[0].start_point[0], profile.primitives[0].start_point[1])
                spec = sp.build_polyline_spec(
                    start=start,
                    segments=segments,
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
                    activate_cnc_correction=bool(operation.activate_cnc_correction),
                )
                # ZigZag: el render CAD necesita la trayectoria ALMACENADA (la rampa Z del
                # zigzag la genera Maestro; con ACC=false el ISO la copia — N046). Campo de
                # SOLO lectura, como speed_changes de la línea.
                if isinstance(operation.milling_strategy, sp.ZigZagMillingStrategySpec):
                    spec = _dc_replace(
                        spec, stored_trajectory=_stored_trajectory_primitives(operation))
            except Exception as exc:
                return _unsupported_entry(
                    feature,
                    operation,
                    step,
                    order_index=order_index,
                    reasons=[_builder_error("No se pudo construir el `PolylineSpec`", exc)],
                    warnings=warnings,
                )
            return _adapted_entry(
                feature,
                operation,
                step,
                order_index=order_index,
                spec_kind="polyline",
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
            spec = sp.build_circle_spec(
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
                reasons=[_builder_error("No se pudo construir el `CircleSpec`", exc)],
                warnings=warnings,
            )
        return _adapted_entry(
            feature,
            operation,
            step,
            order_index=order_index,
            spec_kind="circle",
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
    if "ReplicateFeature" in feature.feature_type:
        return _adapt_drilling_pattern(
            snapshot,
            feature,
            operation,
            step,
            order_index=order_index,
        )
    if "RoundHole" in feature.feature_type:
        return _adapt_drilling(
            snapshot,
            feature,
            operation,
            step,
            order_index=order_index,
        )
    if "ClosedPocket" in feature.feature_type:
        return _adapt_pocket_milling(
            snapshot,
            feature,
            operation,
            step,
            order_index=order_index,
        )
    # ContourFeature (Galceado/Perfilado, N043): el TIPO de feature es INVISIBLE en el ISO —
    # ContourFeature y GeneralProfileFeature con la misma geometría y el mismo ACC dan el mismo
    # byte. El ContourType (Pieza/Geometría) es comodidad de autoría: la geometría ya llega
    # resuelta en el XML y no viaja a la spec. Misma rama que el fresado de perfil.
    if ("GeneralProfileFeature" in feature.feature_type
            or "SlotSide" in feature.feature_type
            or "ContourFeature" in feature.feature_type):
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
        if feature_ref is not None and feature_ref.id:
            feature_ids_seen_in_workplan.add(feature_ref.id)
        if not step.is_enabled:
            entries.append(
                _workplan_step_entry_without_feature(
                    step,
                    order_index=order_index,
                    status="ignored",
                    feature_id=feature_ref.id if feature_ref is not None else "",
                    operation_id=step.operation_ref.id if step.operation_ref is not None else None,
                    reasons=[
                        "El working step esta deshabilitado y Maestro no lo postprocesa."
                    ],
                )
            )
            continue
        if feature_ref is None or not feature_ref.id:
            reasons = [
                "El working step no referencia una manufacturing feature y se "
                "omite del subset publico."
            ]
            if step.runtime_type == "Xn":
                reasons = [
                    "`Xn` no referencia una manufacturing feature; se omite "
                    "del subset de mecanizados y se conserva como operacion "
                    "de maquina `xn` del request."
                ]
            entries.append(
                _workplan_step_entry_without_feature(
                    step,
                    order_index=order_index,
                    status="ignored",
                    operation_id=step.operation_ref.id if step.operation_ref is not None else None,
                    reasons=reasons,
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
            "lines": len(result.lines),
            "channels": len(result.channels),
            "polylines": len(result.polylines),
            "circles": len(result.circles),
            "contours": len(result.contours),
            "pockets": len(result.pockets),
            "drills": len(result.drills),
            "drill_patterns": len(result.drill_patterns),
            "has_xn": result.xn is not None,
        },
        "xn": convert(result.xn),
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
