"""Drilling pattern contracts for PGMX synthesis."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

from ..common.depth import MillingDepthSpec, build_milling_depth_spec
from ..common.piece import _normalize_plane_name, _plane_local_dimensions
from ..common.tools import _normalize_tool_resolution
from ..common.xml import (
    DRILLING_NS,
    PATTERNS_NS,
    PGMX_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _compact_number,
    _qname,
    _set_xmlns,
)
from .single import (
    DrillingSpec,
    _HydratedDrillingSpec,
    _append_drilling_feature_payload,
    _default_drill_family,
    _drilling_bottom_condition_type,
    _hydrate_drilling_spec,
    _normalize_drilling_spec,
)

__all__ = [
    "DrillingPatternSpec",
    "build_drilling_pattern_spec",
    "_HydratedDrillingPatternSpec",
    "_build_drilling_pattern_feature",
    "_drilling_pattern_bottom_condition_type",
    "_hydrate_drilling_pattern_spec",
    "_normalize_drilling_pattern_spec",
    "_validate_drilling_pattern_center",
]


@dataclass(frozen=True)
class DrillingPatternSpec:
    """Repeticion rectangular de taladros iguales usando `ReplicateFeature`."""

    center_x: float
    center_y: float
    diameter: float
    columns: int
    rows: int
    spacing: float
    row_spacing: Optional[float] = None
    feature_name: str = "Taladrado"
    plane_name: str = "Top"
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    drill_family: str = "Flat"
    tool_resolution: str = "Auto"
    tool_id: str = "0"
    tool_name: str = ""


@dataclass(frozen=True)
class _HydratedDrillingPatternSpec:
    """Datos internos para serializar un `ReplicateFeature` de taladros."""

    spec: DrillingPatternSpec
    base_drilling: _HydratedDrillingSpec

    @property
    def center_x(self) -> float:
        return self.spec.center_x

    @property
    def center_y(self) -> float:
        return self.spec.center_y

    @property
    def diameter(self) -> float:
        return self.spec.diameter

    @property
    def columns(self) -> int:
        return self.spec.columns

    @property
    def rows(self) -> int:
        return self.spec.rows

    @property
    def spacing(self) -> float:
        return self.spec.spacing

    @property
    def row_spacing(self) -> float:
        return self.spec.row_spacing if self.spec.row_spacing is not None else self.spec.spacing

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def drill_family(self) -> str:
        return self.spec.drill_family

    @property
    def tool_resolution(self) -> str:
        return self.spec.tool_resolution

    @property
    def tool_id(self) -> str:
        return self.base_drilling.tool_id

    @property
    def tool_name(self) -> str:
        return self.base_drilling.tool_name

    @property
    def tool_object_type(self) -> str:
        return self.base_drilling.tool_object_type


def _normalize_drilling_pattern_spec(pattern: DrillingPatternSpec) -> DrillingPatternSpec:
    base_drilling = _normalize_drilling_spec(
        DrillingSpec(
            center_x=pattern.center_x,
            center_y=pattern.center_y,
            diameter=pattern.diameter,
            feature_name=pattern.feature_name,
            plane_name=pattern.plane_name,
            security_plane=pattern.security_plane,
            depth_spec=pattern.depth_spec,
            drill_family=pattern.drill_family,
            tool_resolution=pattern.tool_resolution,
            tool_id=pattern.tool_id,
            tool_name=pattern.tool_name,
        )
    )
    columns = int(pattern.columns)
    rows = int(pattern.rows)
    if columns < 1 or rows < 1:
        raise ValueError("`DrillingPatternSpec` requiere `columns` y `rows` mayores o iguales a 1.")
    if columns * rows < 2:
        raise ValueError("Para un unico taladro use `DrillingSpec`; el patron requiere al menos 2 huecos.")

    spacing = float(pattern.spacing)
    row_spacing = spacing if pattern.row_spacing is None else float(pattern.row_spacing)
    if spacing < 0.0 or row_spacing < 0.0:
        raise ValueError("Las separaciones de `DrillingPatternSpec` no pueden ser negativas.")
    if columns > 1 and spacing <= 0.0:
        raise ValueError("Un patron con mas de una columna requiere `spacing` mayor que cero.")
    if rows > 1 and row_spacing <= 0.0:
        raise ValueError("Un patron con mas de una fila requiere `row_spacing` mayor que cero.")

    return replace(
        pattern,
        center_x=base_drilling.center_x,
        center_y=base_drilling.center_y,
        diameter=base_drilling.diameter,
        columns=columns,
        rows=rows,
        spacing=spacing,
        row_spacing=row_spacing,
        feature_name=base_drilling.feature_name,
        plane_name=base_drilling.plane_name,
        security_plane=base_drilling.security_plane,
        depth_spec=base_drilling.depth_spec,
        drill_family=base_drilling.drill_family,
        tool_resolution=base_drilling.tool_resolution,
        tool_id=base_drilling.tool_id,
        tool_name=base_drilling.tool_name,
    )


def _hydrate_drilling_pattern_spec(
    pattern: DrillingPatternSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedDrillingPatternSpec:
    del source_pgmx_path
    normalized_pattern = _normalize_drilling_pattern_spec(pattern)
    base_drilling = _hydrate_drilling_spec(
        DrillingSpec(
            center_x=normalized_pattern.center_x,
            center_y=normalized_pattern.center_y,
            diameter=normalized_pattern.diameter,
            feature_name=normalized_pattern.feature_name,
            plane_name=normalized_pattern.plane_name,
            security_plane=normalized_pattern.security_plane,
            depth_spec=normalized_pattern.depth_spec,
            drill_family=normalized_pattern.drill_family,
            tool_resolution=normalized_pattern.tool_resolution,
            tool_id=normalized_pattern.tool_id,
            tool_name=normalized_pattern.tool_name,
        ),
        None,
    )
    return _HydratedDrillingPatternSpec(spec=normalized_pattern, base_drilling=base_drilling)


def _validate_drilling_pattern_center(state, spec: _HydratedDrillingPatternSpec) -> None:
    max_x, max_y = _plane_local_dimensions(state, spec.plane_name)
    last_x = spec.center_x + ((spec.columns - 1) * spec.spacing)
    last_y = spec.center_y + ((spec.rows - 1) * spec.row_spacing)
    if spec.center_x < -1e-9 or last_x > max_x + 1e-9:
        raise ValueError(
            "El patron de taladros cae fuera del eje X del plano "
            f"'{spec.plane_name}': {_compact_number(spec.center_x)}..{_compact_number(last_x)} "
            f"no pertenece a [0, {_compact_number(max_x)}]."
        )
    if spec.center_y < -1e-9 or last_y > max_y + 1e-9:
        raise ValueError(
            "El patron de taladros cae fuera del eje Y del plano "
            f"'{spec.plane_name}': {_compact_number(spec.center_y)}..{_compact_number(last_y)} "
            f"no pertenece a [0, {_compact_number(max_y)}]."
        )


def _drilling_pattern_bottom_condition_type(spec: _HydratedDrillingPatternSpec) -> str:
    return _drilling_bottom_condition_type(spec.base_drilling).replace("a:", "b:", 1)


def _build_drilling_pattern_feature(
    state,
    spec: _HydratedDrillingPatternSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:ReplicateFeature"},
    )
    _set_xmlns(feature, "a", PATTERNS_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint",
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    _append_node(feature, PGMX_NS, "BottomCondition", attrib={f"{{{XSI_NS}}}nil": "true"})

    base_feature = _append_node(
        feature,
        PATTERNS_NS,
        "BaseFeature",
        attrib={f"{{{XSI_NS}}}type": "b:RoundHole"},
    )
    _set_xmlns(base_feature, "b", DRILLING_NS)
    _append_drilling_feature_payload(
        base_feature,
        state,
        spec.base_drilling,
        feature_id,
        geometry_id,
        operation_id,
        workpiece_id,
        workpiece_object_type,
        bottom_condition_type=_drilling_pattern_bottom_condition_type(spec),
    )

    replication_pattern = _append_node(
        feature,
        PATTERNS_NS,
        "ReplicationPattern",
        attrib={f"{{{XSI_NS}}}type": "a:RectangularPattern"},
    )
    _set_xmlns(replication_pattern, "a", PATTERNS_NS)
    _append_node(replication_pattern, PATTERNS_NS, "MissingBaseFeatures", "")
    _append_node(replication_pattern, PATTERNS_NS, "NumberOfColumns", str(spec.columns))
    _append_node(replication_pattern, PATTERNS_NS, "NumberOfRows", str(spec.rows))
    _append_node(replication_pattern, PATTERNS_NS, "RotationAngle", "0")
    _append_node(replication_pattern, PATTERNS_NS, "RowLayoutAngle", "90")
    _append_node(replication_pattern, PATTERNS_NS, "RowSpacing", _compact_number(spec.row_spacing))
    _append_node(replication_pattern, PATTERNS_NS, "Spacing", _compact_number(spec.spacing))
    return feature


def build_drilling_pattern_spec(
    center_x: float,
    center_y: float,
    diameter: float,
    columns: int,
    rows: int,
    spacing: float,
    feature_name: Optional[str] = None,
    *,
    row_spacing: Optional[float] = None,
    plane_name: str = "Top",
    security_plane: Optional[float] = None,
    is_through: bool = True,
    target_depth: Optional[float] = None,
    extra_depth: float = 0.0,
    drill_family: Optional[str] = None,
    tool_resolution: str = "Auto",
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> DrillingPatternSpec:
    """Construye una repeticion rectangular Maestro (`ReplicateFeature`)."""

    normalized_plane_name = _normalize_plane_name(plane_name)
    depth_spec = build_milling_depth_spec(
        is_through=is_through,
        target_depth=target_depth,
        extra_depth=extra_depth,
    )
    effective_drill_family = _default_drill_family(
        normalized_plane_name,
        float(diameter),
        depth_spec,
        drill_family,
    )
    return _normalize_drilling_pattern_spec(
        DrillingPatternSpec(
            center_x=float(center_x),
            center_y=float(center_y),
            diameter=float(diameter),
            columns=int(columns),
            rows=int(rows),
            spacing=float(spacing),
            row_spacing=row_spacing,
            feature_name=(feature_name or "Taladrado").strip() or "Taladrado",
            plane_name=normalized_plane_name,
            security_plane=20.0 if security_plane is None else float(security_plane),
            depth_spec=depth_spec,
            drill_family=effective_drill_family,
            tool_resolution=_normalize_tool_resolution(tool_resolution or "Auto"),
            tool_id=(tool_id or "0").strip() or "0",
            tool_name=(tool_name or "").strip(),
        )
    )
