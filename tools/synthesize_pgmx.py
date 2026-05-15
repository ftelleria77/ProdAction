"""Utilidades para sintetizar archivos `.pgmx` a partir de un baseline Maestro.

La API publica del modulo esta pensada para poder reutilizarla desde el flujo
principal de la aplicacion, sin depender de la CLI:

Referencia operativa recomendada:
- `docs/synthesize_pgmx_help.md`

- `read_pgmx_state(...)` lee dimensiones, nombre, origen y area desde un
    baseline Maestro (`.pgmx`, `Pieza.xml` o carpeta contenedora).
- `read_pgmx_geometries(...)` clasifica las geometrías base guardadas en `Geometries`.
- `build_synthesis_request(...)` arma una solicitud clara y reusable.
- `synthesize_request(...)` aplica la solicitud sobre un baseline Maestro y
    escribe el `.pgmx` de salida.
- `synthesize_pgmx(...)` se mantiene como wrapper de compatibilidad para los
    scripts y experimentos ya existentes.

Soporte actual de mecanizados sinteticos:
- `LineMillingSpec`: linea sobre un plano con su fresado asociado.
- `PolylineMillingSpec`: polilinea lineal abierta o cerrada con su fresado asociado.
- `CircleMillingSpec`: circulo sobre `Top` con su fresado asociado.
- `SquaringMillingSpec`: escuadrado exterior del contorno de la pieza sobre `Top`.
- `DrillingSpec`: taladro puntual sobre `Top`, `Front`, `Back`, `Right` o `Left`.
- `DrillingPatternSpec`: repeticion rectangular de taladros sobre `Top`, `Front`, `Back`,
  `Right` o `Left`.
- `XnSpec`: operacion nula final para mover la herramienta sin mecanizar.

Estado de hito:
- la API publica del sintetizador queda establecida como `v1.6`

Soporte actual de geometria base reusable:
- `build_point_geometry_profile(...)`
- `build_line_geometry_profile(...)`
- `build_circle_geometry_profile(...)`
- `build_composite_geometry_profile(...)`
- `build_compensated_toolpath_profile(...)`

Hallazgos ya volcados en la sintesis:
- `Area` de `Parametros de Maquina` usa `HG` por defecto si no se indica otro valor.
- La profundidad total del fresado se valida contra `tools/tool_catalog.csv`:
    `target_depth` en no pasante y `espesor + Extra` en pasante no pueden
    superar `sinking_length` de la herramienta elegida.
- `Approach` y `Retract` soportan `Line` y `Arc`.
- Para `Approach Line + Down` ya se sintetizo la regla observada en Maestro:
    una sola bajada oblicua desde un punto previo desplazado sobre la direccion
    opuesta al avance, sin alterar `TrajectoryPath`. La regla ya se aplica
    sobre la tangente de entrada del toolpath efectivo, sin depender de la
    familia geometrica nominal.
- Para `Retract Line + Up` ya se sintetizo la regla observada en Maestro:
    una sola subida oblicua hacia un punto final desplazado sobre la direccion
    de salida, sin alterar `TrajectoryPath`. La regla ya se aplica sobre la
    tangente de salida del toolpath efectivo, sin depender de la familia
    geometrica nominal.
- Para `Arc + Quote` ya se sintetizo la regla observada en Maestro para entrada/salida
    sobre perfiles rectos: toolpath vertical cuando la estrategia esta deshabilitada y
    `linea vertical + arco` / `arco + linea vertical` cuando esta habilitada.
    La construccion ya cuelga del toolpath efectivo y su tangente de entrada/salida.
- Para `Retract Arc + Up` ya se sintetizo la salida observada en Maestro:
    `arco en un plano vertical + linea vertical`, sin alterar `TrajectoryPath`.
    La construccion ya cuelga del toolpath efectivo y su tangente de salida.
- Por limitacion observada en Maestro, se bloquea `Retract Arc + Up` en
    polilineas abiertas de varios segmentos con estrategia multipasada `PH`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional, Sequence, Union

PGMX_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.ProjectModule"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
BASE_MODEL_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel"
MILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Milling"
DRILLING_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Drilling"
PATTERNS_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Patterns"
GEOMETRY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Geometry"
STRATEGY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Strategy"
UTILITY_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Utility"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
ARRAYS_NS = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
PARAMETRIC_NS = "http://schemas.datacontract.org/2004/07/ScmGroup.XCam.MachiningDataModel.Parametrics"
def _module_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        for bundled_tools_dir in (
            executable_dir / "tools",
            executable_dir / "_internal" / "tools",
        ):
            if bundled_tools_dir.exists():
                return bundled_tools_dir
    return Path(__file__).resolve().parent


MODULE_DIR = _module_data_dir()
DEFAULT_BASELINE_DIR = MODULE_DIR / "maestro_baselines"
DEFAULT_BASELINE_XML_PATH = DEFAULT_BASELINE_DIR / "Pieza.xml"
TOOL_CATALOG_PATH = Path(__file__).with_name("tool_catalog.csv")
SYNTHESIZER_VERSION = "1.6"

ET.register_namespace("", PGMX_NS)
ET.register_namespace("i", XSI_NS)

__all__ = [
    "DEFAULT_BASELINE_DIR",
    "DEFAULT_BASELINE_XML_PATH",
    "SYNTHESIZER_VERSION",
    "PgmxState",
    "ApproachSpec",
    "RetractSpec",
    "MillingDepthSpec",
    "UnidirectionalMillingStrategySpec",
    "BidirectionalMillingStrategySpec",
    "HelicalMillingStrategySpec",
    "ContourParallelMillingStrategySpec",
    "GeometryPrimitiveSpec",
    "GeometryProfileSpec",
    "LineMillingSpec",
    "SlotMillingSpec",
    "PolylineMillingSpec",
    "CircleMillingSpec",
    "SquaringMillingSpec",
    "DrillingSpec",
    "DrillingPatternSpec",
    "MachiningSpec",
    "XnSpec",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "build_approach_spec",
    "build_retract_spec",
    "build_milling_depth_spec",
    "build_unidirectional_milling_strategy_spec",
    "build_bidirectional_milling_strategy_spec",
    "build_helical_milling_strategy_spec",
    "build_contour_parallel_milling_strategy_spec",
    "build_line_geometry_primitive",
    "build_arc_geometry_primitive",
    "build_point_geometry_profile",
    "build_line_geometry_profile",
    "build_circle_geometry_profile",
    "build_composite_geometry_profile",
    "build_compensated_toolpath_profile",
    "build_line_milling_spec",
    "build_slot_milling_spec",
    "build_polyline_milling_spec",
    "build_circle_milling_spec",
    "build_squaring_milling_spec",
    "build_drilling_spec",
    "build_drilling_pattern_spec",
    "build_xn_spec",
    "read_pgmx_state",
    "read_pgmx_geometries",
    "build_synthesis_request",
    "synthesize_request",
    "synthesize_pgmx",
]


# ============================================================================
# Public data model
# ============================================================================

@dataclass(frozen=True)
class PgmxState:
    """Descripcion de la pieza final a sintetizar."""

    piece_name: str
    length: float
    width: float
    depth: float
    origin_x: float
    origin_y: float
    origin_z: float
    execution_fields: str = "HG"


@dataclass(frozen=True)
class ApproachSpec:
    """Configuracion reutilizable del approach de un fresado lineal."""

    is_enabled: bool = False
    approach_type: str = "Line"
    mode: str = "Down"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"


@dataclass(frozen=True)
class RetractSpec:
    """Configuracion reutilizable del retract de un fresado lineal."""

    is_enabled: bool = False
    retract_type: str = "Line"
    mode: str = "Up"
    radius_multiplier: float = 1.2
    speed: float = 0.0
    arc_side: str = "Automatic"
    overlap: float = 0.0


@dataclass(frozen=True)
class MillingDepthSpec:
    """Configuracion reutilizable de profundidad para un fresado."""

    is_through: bool = True
    target_depth: Optional[float] = None
    extra_depth: float = 0.0


@dataclass(frozen=True)
class UnidirectionalMillingStrategySpec:
    """Estrategia `Unidireccional` observada en Maestro para fresados."""

    connection_mode: str = "Automatic"
    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0


@dataclass(frozen=True)
class BidirectionalMillingStrategySpec:
    """Estrategia `Bidireccional` observada en Maestro para fresados."""

    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0


@dataclass(frozen=True)
class HelicalMillingStrategySpec:
    """Estrategia `Helicoidal` observada en Maestro para fresados circulares."""

    axial_cutting_depth: float = 0.0
    allows_finish_cutting: bool = True
    axial_finish_cutting_depth: float = 0.0


@dataclass(frozen=True)
class ContourParallelMillingStrategySpec:
    """Estrategia `Paralela al perfil/contorno` observada para vaciados."""

    rotation_direction: str = "CounterClockwise"
    stroke_connection_strategy: str = "LiftShiftPlunge"
    inside_to_outside: bool = True
    overlap: float = 0.5
    is_helic_strategy: bool = False
    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0
    cutmode: str = "Climb"
    is_internal: bool = True
    radial_cutting_depth: float = 0.0
    radial_finish_cutting_depth: float = 0.0
    allows_bidirectional: bool = False
    allows_finish_cutting: bool = False


MillingStrategySpec = (
    UnidirectionalMillingStrategySpec
    | BidirectionalMillingStrategySpec
    | HelicalMillingStrategySpec
    | ContourParallelMillingStrategySpec
)


@dataclass(frozen=True)
class GeometryPrimitiveSpec:
    """Primitiva geometrica 2D/3D reusable para perfiles Maestro."""

    primitive_type: str
    start_point: tuple[float, float, float]
    end_point: tuple[float, float, float]
    parameter_start: float = 0.0
    parameter_end: float = 0.0
    center_point: Optional[tuple[float, float, float]] = None
    radius: Optional[float] = None
    normal_vector: Optional[tuple[float, float, float]] = None
    u_vector: Optional[tuple[float, float, float]] = None
    v_vector: Optional[tuple[float, float, float]] = None
    direction_hint: Optional[tuple[float, float, float]] = None


@dataclass(frozen=True)
class GeometryProfileSpec:
    """Perfil geometrico identificado o construido para futura sintesis."""

    geometry_type: str
    family: str
    primitives: tuple[GeometryPrimitiveSpec, ...] = ()
    is_closed: bool = False
    winding: Optional[str] = None
    start_mode: Optional[str] = None
    has_arcs: bool = False
    corner_radii: tuple[float, ...] = ()
    bounding_box: Optional[tuple[float, float, float, float]] = None
    center_point: Optional[tuple[float, float, float]] = None
    radius: Optional[float] = None
    serialization: Optional[str] = None
    member_serializations: tuple[str, ...] = ()

    @property
    def classification_key(self) -> str:
        if self.winding:
            return f"{self.family}_{self.winding}"
        return self.family

    @property
    def primitive_count(self) -> int:
        return len(self.primitives)


@dataclass(frozen=True)
class LineMillingSpec:
    """Descripcion reutilizable de un fresado lineal sobre un plano."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1902"
    tool_name: str = "E003"
    tool_width: float = 9.52
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    milling_strategy: Optional[MillingStrategySpec] = None


@dataclass(frozen=True)
class SlotMillingSpec:
    """Ranura lineal `SlotSide` validada para Sierra Vertical X sobre `Top`."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    feature_name: str = "Canal"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1899"
    tool_name: str = "082"
    tool_width: float = 3.8
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(
        default_factory=lambda: MillingDepthSpec(
            is_through=False,
            target_depth=10.0,
            extra_depth=0.0,
        )
    )
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    material_position: str = "Left"
    side_offset: float = 0.0
    end_radius: float = 60.0
    slot_angle: float = 1.5707963267948966

    @property
    def milling_strategy(self) -> None:
        return None


@dataclass(frozen=True)
class PolylineMillingSpec:
    """Descripcion reutilizable de un fresado asociado a una polilinea lineal.

    Si `points` termina en el mismo punto en el que empieza, se interpreta como
    contorno cerrado.
    """

    points: tuple[tuple[float, float], ...]
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1902"
    tool_name: str = "E003"
    tool_width: float = 9.52
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    milling_strategy: Optional[MillingStrategySpec] = None


@dataclass(frozen=True)
class CircleMillingSpec:
    """Descripcion reutilizable de un fresado circular sobre el plano `Top`."""

    center_x: float
    center_y: float
    radius: float
    winding: str = "CounterClockwise"
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_id: str = "1902"
    tool_name: str = "E003"
    tool_width: float = 9.52
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    approach: ApproachSpec = field(default_factory=ApproachSpec)
    retract: RetractSpec = field(default_factory=RetractSpec)
    milling_strategy: Optional[MillingStrategySpec] = None


@dataclass(frozen=True)
class SquaringMillingSpec:
    """Escuadrado exterior del contorno de la pieza sobre el plano `Top`."""

    start_edge: str = "Bottom"
    winding: str = "CounterClockwise"
    start_coordinate: Optional[float] = None
    feature_name: str = "Fresado"
    plane_name: str = "Top"
    tool_id: str = "1900"
    tool_name: str = "E001"
    tool_width: float = 18.36
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=lambda: MillingDepthSpec(is_through=True, extra_depth=1.0))
    approach: ApproachSpec = field(
        default_factory=lambda: ApproachSpec(
            is_enabled=True,
            approach_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
        )
    )
    retract: RetractSpec = field(
        default_factory=lambda: RetractSpec(
            is_enabled=True,
            retract_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
            overlap=0.0,
        )
    )
    milling_strategy: Optional[MillingStrategySpec] = None

    @property
    def side_of_feature(self) -> str:
        normalized_winding = _normalize_geometry_winding(self.winding)
        return "Right" if normalized_winding == "CounterClockwise" else "Left"


@dataclass(frozen=True)
class DrillingSpec:
    """Descripcion reutilizable de un taladro puntual sobre una cara de la pieza."""

    center_x: float
    center_y: float
    diameter: float
    feature_name: str = "Taladrado"
    plane_name: str = "Top"
    security_plane: float = 20.0
    depth_spec: MillingDepthSpec = field(default_factory=MillingDepthSpec)
    drill_family: str = "Flat"
    tool_resolution: str = "Auto"
    tool_id: str = "0"
    tool_name: str = ""


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


MachiningSpec = Union[
    LineMillingSpec,
    SlotMillingSpec,
    PolylineMillingSpec,
    CircleMillingSpec,
    SquaringMillingSpec,
    DrillingSpec,
    DrillingPatternSpec,
]


@dataclass(frozen=True)
class XnSpec:
    """Configuracion publica de `Xn`, la operacion nula final del workplan."""

    reference: str = "Absolute"
    x: float = -3700.0
    y: Optional[float] = None


@dataclass(frozen=True)
class _CurveSpec:
    """Serializacion XML de una curva usada en geometria o toolpaths."""

    geometry_type: str = "GeomTrimmedCurve"
    serialization: Optional[str] = None
    member_keys: tuple[str, ...] = ()
    member_serializations: tuple[str, ...] = ()


@dataclass(frozen=True)
class _HydratedLineMillingSpec:
    """Datos internos de serializacion que complementan un `LineMillingSpec`."""

    spec: LineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_serialization: Optional[str] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def start_x(self) -> float:
        return self.spec.start_x

    @property
    def start_y(self) -> float:
        return self.spec.start_y

    @property
    def end_x(self) -> float:
        return self.spec.end_x

    @property
    def end_y(self) -> float:
        return self.spec.end_y

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract

    @property
    def milling_strategy(self) -> Optional[MillingStrategySpec]:
        return self.spec.milling_strategy


@dataclass(frozen=True)
class _HydratedSlotMillingSpec:
    """Datos internos de serializacion que complementan un `SlotMillingSpec`."""

    spec: SlotMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_serialization: Optional[str] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def start_x(self) -> float:
        return self.spec.start_x

    @property
    def start_y(self) -> float:
        return self.spec.start_y

    @property
    def end_x(self) -> float:
        return self.spec.end_x

    @property
    def end_y(self) -> float:
        return self.spec.end_y

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract

    @property
    def milling_strategy(self) -> None:
        return None

    @property
    def material_position(self) -> str:
        return self.spec.material_position

    @property
    def side_offset(self) -> float:
        return self.spec.side_offset

    @property
    def end_radius(self) -> float:
        return self.spec.end_radius

    @property
    def slot_angle(self) -> float:
        return self.spec.slot_angle


@dataclass(frozen=True)
class _HydratedPolylineMillingSpec:
    """Datos internos de serializacion que complementan un `PolylineMillingSpec`."""

    spec: PolylineMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def points(self) -> tuple[tuple[float, float], ...]:
        return self.spec.points

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract

    @property
    def milling_strategy(self) -> Optional[MillingStrategySpec]:
        return self.spec.milling_strategy


@dataclass(frozen=True)
class _HydratedCircleMillingSpec:
    """Datos internos de serializacion que complementan un `CircleMillingSpec`."""

    spec: CircleMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def center_x(self) -> float:
        return self.spec.center_x

    @property
    def center_y(self) -> float:
        return self.spec.center_y

    @property
    def radius(self) -> float:
        return self.spec.radius

    @property
    def winding(self) -> str:
        return self.spec.winding

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract

    @property
    def milling_strategy(self) -> Optional[MillingStrategySpec]:
        return self.spec.milling_strategy


@dataclass(frozen=True)
class _HydratedSquaringMillingSpec:
    """Datos internos de serializacion para un `SquaringMillingSpec`."""

    spec: SquaringMillingSpec
    preferred_id_start: Optional[int] = None
    geometry_curve: Optional[_CurveSpec] = None
    approach_curve: Optional[_CurveSpec] = None
    trajectory_curve: Optional[_CurveSpec] = None
    lift_curve: Optional[_CurveSpec] = None

    @property
    def start_edge(self) -> str:
        return self.spec.start_edge

    @property
    def winding(self) -> str:
        return self.spec.winding

    @property
    def feature_name(self) -> str:
        return self.spec.feature_name

    @property
    def plane_name(self) -> str:
        return self.spec.plane_name

    @property
    def side_of_feature(self) -> str:
        return self.spec.side_of_feature

    @property
    def tool_id(self) -> str:
        return self.spec.tool_id

    @property
    def tool_name(self) -> str:
        return self.spec.tool_name

    @property
    def tool_width(self) -> float:
        return self.spec.tool_width

    @property
    def security_plane(self) -> float:
        return self.spec.security_plane

    @property
    def depth_spec(self) -> MillingDepthSpec:
        return self.spec.depth_spec

    @property
    def approach(self) -> ApproachSpec:
        return self.spec.approach

    @property
    def retract(self) -> RetractSpec:
        return self.spec.retract

    @property
    def milling_strategy(self) -> Optional[MillingStrategySpec]:
        return self.spec.milling_strategy


@dataclass(frozen=True)
class _HydratedDrillingSpec:
    """Datos internos de serializacion y herramienta para `DrillingSpec`."""

    spec: DrillingSpec
    preferred_id_start: Optional[int] = None
    resolved_tool_id: str = "0"
    resolved_tool_name: str = ""
    resolved_tool_object_type: str = "System.Object"

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
        return self.resolved_tool_id

    @property
    def tool_name(self) -> str:
        return self.resolved_tool_name

    @property
    def tool_object_type(self) -> str:
        return self.resolved_tool_object_type


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


@dataclass(frozen=True)
class PgmxSynthesisRequest:
    """Solicitud completa para sintetizar un `.pgmx` reutilizable desde la app."""

    baseline_path: Path
    output_path: Path
    piece: PgmxState
    source_pgmx_path: Optional[Path] = None
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = ("line", "slot", "polyline", "circle", "squaring", "drilling", "drilling_pattern")
    xn: XnSpec = field(default_factory=XnSpec)


@dataclass(frozen=True)
class PgmxSynthesisResult:
    """Resultado de una sintesis ya escrita a disco."""

    output_path: Path
    piece: PgmxState
    sha256: str
    line_millings: tuple[LineMillingSpec, ...] = ()
    slot_millings: tuple[SlotMillingSpec, ...] = ()
    polyline_millings: tuple[PolylineMillingSpec, ...] = ()
    circle_millings: tuple[CircleMillingSpec, ...] = ()
    squaring_millings: tuple[SquaringMillingSpec, ...] = ()
    drillings: tuple[DrillingSpec, ...] = ()
    drilling_patterns: tuple[DrillingPatternSpec, ...] = ()
    ordered_machinings: tuple[MachiningSpec, ...] = ()
    machining_order: tuple[str, ...] = ("line", "slot", "polyline", "circle", "squaring", "drilling", "drilling_pattern")
    xn: XnSpec = field(default_factory=XnSpec)


# ============================================================================
# Public spec builders
# ============================================================================

def _strip_namespace(tag: str) -> str:
    """Devuelve el nombre local de un tag XML, sin su namespace."""

    return tag.split("}", 1)[-1] if "}" in tag else tag


def _compact_number(value: float) -> str:
    """Serializa un numero con el formato compacto que usamos en PGMX."""

    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.6f}".rstrip("0").rstrip(".")


def _xsi_type(element: ET.Element) -> str:
    """Lee el `xsi:type` de un nodo XML sin depender del prefijo exacto."""

    for key, value in element.attrib.items():
        if _strip_namespace(key).lower() == "type":
            return value or ""
    return ""


def _set_text(element: Optional[ET.Element], value) -> None:
    """Asigna texto a un nodo XML, tolerando `None`."""

    if element is not None:
        element.text = "" if value is None else str(value)


def _set_xmlns(element: Optional[ET.Element], prefix: str, uri: str) -> None:
    """Inyecta una declaracion `xmlns:prefix` en un nodo si existe."""

    if element is not None:
        element.set(f"xmlns:{prefix}", uri)


def _resolve_exploded_pgmx_xml_path(source_path: Path) -> Path:
    """Resuelve el XML base cuando el baseline esta desempaquetado en disco."""

    if source_path.is_file() and source_path.suffix.lower() == ".xml":
        return source_path
    if not source_path.is_dir():
        raise ValueError(
            "El baseline Maestro desempaquetado debe pasarse como carpeta o como archivo `.xml`."
        )

    xml_candidates = sorted(
        (
            child
            for child in source_path.iterdir()
            if child.is_file() and child.suffix.lower() == ".xml"
        ),
        key=lambda path: (path.name.lower() != "pieza.xml", path.name.lower()),
    )
    if not xml_candidates:
        raise ValueError(f"La carpeta '{source_path}' no contiene ningun archivo `.xml`.")
    return xml_candidates[0]


def _load_exploded_pgmx_container(source_path: Path) -> tuple[ET.Element, dict[str, bytes], str]:
    """Carga un baseline Maestro desempaquetado (`Pieza.xml` + extras asociados)."""

    xml_path = _resolve_exploded_pgmx_xml_path(source_path)
    container_dir = xml_path.parent
    archive_entries: dict[str, bytes] = {xml_path.name: xml_path.read_bytes()}
    for child in sorted(container_dir.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_file() or child == xml_path:
            continue
        if child.suffix.lower() not in {".epl", ".tlgx"}:
            continue
        archive_entries[child.name] = child.read_bytes()

    xml_root = ET.fromstring(archive_entries[xml_path.name].decode("utf-8", errors="ignore"))
    return xml_root, archive_entries, xml_path.name


def _load_pgmx_container(source_path: Path) -> tuple[ET.Element, dict[str, bytes], str]:
    """Carga un baseline Maestro desde `.pgmx`, `Pieza.xml` o carpeta contenedora."""

    if not source_path.exists():
        raise FileNotFoundError(f"No existe el baseline Maestro '{source_path}'.")
    if source_path.is_file() and source_path.suffix.lower() == ".pgmx":
        with zipfile.ZipFile(source_path) as zip_file:
            archive_entries = {name: zip_file.read(name) for name in zip_file.namelist()}
        xml_entry_name = next((name for name in archive_entries if name.lower().endswith(".xml")), "")
        if not xml_entry_name:
            raise ValueError(f"El archivo '{source_path}' no contiene una entrada XML.")
        xml_root = ET.fromstring(archive_entries[xml_entry_name].decode("utf-8", errors="ignore"))
        return xml_root, archive_entries, xml_entry_name
    if source_path.is_dir() or (source_path.is_file() and source_path.suffix.lower() == ".xml"):
        return _load_exploded_pgmx_container(source_path)
    raise ValueError(
        f"El baseline Maestro '{source_path}' debe ser un `.pgmx`, un `.xml` o una carpeta."
    )


def _id_counter(root: ET.Element):
    """Genera IDs nuevos por encima del mayor ID/unsignedInt ya presente en el XML."""

    max_value = 0
    for element in root.iter():
        tag = _strip_namespace(element.tag)
        text = str(element.text or "").strip()
        if tag not in {"ID", "unsignedInt"} or not text.isdigit():
            continue
        max_value = max(max_value, int(text))

    current = max_value + 1
    while True:
        yield str(current)
        current += 1


def _toolpath_line_string(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    """Serializa un segmento recto de `ToolpathList` en el formato raw de Maestro."""

    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    dz = end_point[2] - start_point[2]
    length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if length <= 1e-6:
        raise ValueError("No se puede crear un segmento de toolpath con longitud cero.")

    return "\n".join(
        [
            f"8 0 {_compact_number(length)}",
            " ".join(
                [
                    "1",
                    _compact_number(start_point[0]),
                    _compact_number(start_point[1]),
                    _compact_number(start_point[2]),
                    _compact_number(dx / length),
                    _compact_number(dy / length),
                    _compact_number(dz / length),
                ]
            ),
        ]
    )


def _write_pgmx_zip(output_path: Path, xml_bytes: bytes, template_entries: dict[str, bytes], xml_entry_name: str) -> None:
    """Escribe un `.pgmx` preservando el resto de entradas del template ZIP."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epl_written = False
    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(xml_entry_name, xml_bytes)
        for entry_name, data in template_entries.items():
            if entry_name.lower().endswith(".xml"):
                continue
            if entry_name.lower().endswith(".epl"):
                zip_file.writestr(f"{output_path.stem}.epl", data)
                epl_written = True
                continue
            zip_file.writestr(entry_name, data)
        if not epl_written:
            zip_file.writestr(f"{output_path.stem}.epl", b"")


def _finalize_pgmx_xml_bytes(xml_bytes: bytes) -> bytes:
    """Normaliza namespaces y tipos XML para que Maestro acepte el `.pgmx`."""

    xml_text = xml_bytes.decode("utf-8")
    geometry_decl = f'<Geometries xmlns:a="{GEOMETRY_NS}">'
    global_setup_decl = f'<GlobalSetup xmlns:a="{BASE_MODEL_NS}">'
    machining_params_decl = (
        f'<MachiningParameters i:type="a:XilogHeaderParameters" xmlns:a="{BASE_MODEL_NS}">'
    )
    workpiece_geometry_decl = f'<Geometry i:type="a:WorkpieceBoxGeometry" xmlns:a="{BASE_MODEL_NS}">'
    variable_value_decl = f'<Value i:type="b:double" xmlns:b="{XSD_NS}">'
    toolpath_list_decl = f'<ToolpathList xmlns:b="{BASE_MODEL_NS}">'
    head_decl = f'<Head xmlns:b="{BASE_MODEL_NS}">'
    machine_functions_decl = f'<MachineFunctions xmlns:b="{BASE_MODEL_NS}">'
    start_point_decl = f'<StartPoint xmlns:b="{GEOMETRY_NS}">'
    tool_key_decl = f'<ToolKey xmlns:b="{UTILITY_NS}">'
    approach_decl = f'<Approach i:type="b:BaseApproachStrategy" xmlns:b="{STRATEGY_NS}">'
    retract_decl = f'<Retract i:type="b:BaseRetractStrategy" xmlns:b="{STRATEGY_NS}">'

    def ensure_prefixed_namespace_attr(text: str, element_name: str, prefix: str, namespace: str) -> str:
        pattern = re.compile(
            rf'<(?P<tagprefix>[A-Za-z_][\w.-]*:)?{element_name}(?P<attrs>[^<>]*?)(?P<selfclose>\s*/?)>',
        )

        def replacer(match: re.Match[str]) -> str:
            attrs = (match.group("attrs") or "").rstrip()
            selfclose = match.group("selfclose") or ""
            if f'xmlns:{prefix}="' in attrs:
                return match.group(0)
            if attrs:
                return (
                    f'<{match.group("tagprefix") or ""}{element_name}'
                    f'{attrs} xmlns:{prefix}="{namespace}"{selfclose}>'
                )
            return (
                f'<{match.group("tagprefix") or ""}{element_name}'
                f' xmlns:{prefix}="{namespace}"{selfclose}>'
            )

        return pattern.sub(replacer, text)

    if "<Geometries>" in xml_text and geometry_decl not in xml_text:
        xml_text = xml_text.replace("<Geometries>", geometry_decl, 1)
    if "<GlobalSetup>" in xml_text and global_setup_decl not in xml_text:
        xml_text = xml_text.replace("<GlobalSetup>", global_setup_decl, 1)
    xml_text = xml_text.replace(
        '<MachiningParameters i:type="a:XilogHeaderParameters">',
        machining_params_decl,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Geometry i:type="a:WorkpieceBoxGeometry">',
        lambda match: (
            f'<{match.group("prefix") or ""}Geometry i:type="a:WorkpieceBoxGeometry" '
            f'xmlns:a="{BASE_MODEL_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Value i:type="b:double">',
        lambda match: (
            f'<{match.group("prefix") or ""}Value i:type="b:double" '
            f'xmlns:b="{XSD_NS}">'
        ),
        xml_text,
    )
    xml_text = ensure_prefixed_namespace_attr(xml_text, "ToolpathList", "b", BASE_MODEL_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "Head", "b", BASE_MODEL_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "MachineFunctions", "b", BASE_MODEL_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "StartPoint", "b", GEOMETRY_NS)
    xml_text = ensure_prefixed_namespace_attr(xml_text, "ToolKey", "b", UTILITY_NS)
    xml_text = xml_text.replace(
        '<Approach i:type="b:BaseApproachStrategy">',
        approach_decl,
    )
    xml_text = xml_text.replace(
        '<Retract i:type="b:BaseRetractStrategy">',
        retract_decl,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="a:MachiningWorkingStep">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="a:MachiningWorkingStep" '
            f'xmlns:a="{PGMX_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Executable i:type="Xn">',
        lambda match: (
            f'<{match.group("prefix") or ""}Executable i:type="Xn" '
            f'xmlns="{BASE_MODEL_NS}">'
        ),
        xml_text,
        count=1,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?ManufacturingFeatureID>',
        lambda match: (
            f'<{match.group("prefix") or ""}ManufacturingFeatureID '
            f'xmlns:b="{UTILITY_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?OperationID>',
        lambda match: (
            f'<{match.group("prefix") or ""}OperationID '
            f'xmlns:b="{UTILITY_NS}">'
        ),
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?PlaneID>',
        lambda match: f'<{match.group("prefix") or ""}PlaneID xmlns:c="{UTILITY_NS}">',
        xml_text,
    )
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?BasicCurve i:type="c:GeomCompositeCurve">',
        lambda match: (
            f'<{match.group("prefix") or ""}BasicCurve i:type="c:GeomCompositeCurve" '
            f'xmlns:c="{GEOMETRY_NS}">'
        ),
        xml_text,
    )
    xml_text = xml_text.replace(
        '<Geometry i:type="a:WorkpieceBoxGeometry">',
        workpiece_geometry_decl,
    )
    xml_text = xml_text.replace(
        '<Value i:type="b:double">',
        variable_value_decl,
    )
    return xml_text.encode("utf-8")


def _safe_float(value, default: float) -> float:
    raw = "" if value is None else str(value).strip().replace(",", ".")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _safe_bool(value, default: bool) -> bool:
    raw = "" if value is None else str(value).strip().lower()
    if not raw:
        return default
    if raw in {"true", "1", "yes", "si", "sí"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    return default


def _finalize_synthesized_pgmx_xml_bytes(xml_bytes: bytes) -> bytes:
    finalized = _finalize_pgmx_xml_bytes(xml_bytes)
    xml_text = finalized.decode("utf-8")
    expressions_decl = f'<Expressions xmlns:a="{PARAMETRIC_NS}">'
    if "<Expressions>" in xml_text and expressions_decl not in xml_text:
        xml_text = xml_text.replace("<Expressions>", expressions_decl, 1)
    xml_text = re.sub(
        r'<(?P<prefix>[A-Za-z_][\w.-]*:)?Property i:type="a:CompositeField">',
        lambda match: (
            f'<{match.group("prefix") or ""}Property i:type="a:CompositeField" '
            f'xmlns:a="{PARAMETRIC_NS}">'
        ),
        xml_text,
    )
    def runtime_type_namespace(element_name: str, dtype: str) -> str:
        if element_name == "ManufacturingFeature":
            return {
                "GeneralProfileFeature": MILLING_NS,
                "RoundHole": DRILLING_NS,
            }.get(dtype, MILLING_NS)
        if element_name == "Operation":
            return {
                "BottomAndSideFinishMilling": MILLING_NS,
                "DrillingOperation": DRILLING_NS,
            }.get(dtype, MILLING_NS)
        if element_name == "GeomGeometry":
            return GEOMETRY_NS
        return MILLING_NS

    for element_name in ("ManufacturingFeature", "Operation", "GeomGeometry"):
        xml_text = re.sub(
            rf'<(?P<prefix>[A-Za-z_][\w.-]*:)?{element_name}(?P<attrs>[^>]*) i:type="a:(?P<dtype>[^"]+)"(?P<tail>[^>]*)>',
            lambda match: (
                match.group(0)
                if 'xmlns:a="' in match.group(0)
                else (
                    f'<{match.group("prefix") or ""}{element_name}'
                    f'{match.group("attrs")} i:type="a:{match.group("dtype")}"'
                    f' xmlns:a="{runtime_type_namespace(element_name, match.group("dtype"))}"{match.group("tail")}>'
                )
            ),
            xml_text,
        )
    xml_text = xml_text.replace(
        '<MachiningStrategy i:type="b:SingleStepDrilling">',
        f'<MachiningStrategy i:type="b:SingleStepDrilling" xmlns:b="{BASE_MODEL_NS}">',
    )
    return xml_text.encode("utf-8")


def _text(node: Optional[ET.Element], path: str, default: str = "") -> str:
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return str(found.text).strip()


def _raw_text(node: Optional[ET.Element], path: str, default: str = "") -> str:
    if node is None:
        return default
    found = node.find(path)
    if found is None or found.text is None:
        return default
    return str(found.text)


def _normalize_execution_fields(value: Optional[str]) -> str:
    raw = (value or "HG").strip().upper().replace(" ", "")
    if not raw:
        return "HG"
    if any(letter not in "ABCDEFGH" for letter in raw):
        raise ValueError(
            "ExecutionFields invalido. Use letras entre A y H, por ejemplo: A, EF o HG."
        )
    if len(set(raw)) != len(raw):
        raise ValueError("ExecutionFields invalido. No debe repetir letras.")
    return raw


def _normalize_side_of_feature(value: Optional[str]) -> str:
    raw = (value or "Center").strip().lower()
    mapping = {
        "center": "Center",
        "centre": "Center",
        "central": "Center",
        "right": "Right",
        "derecha": "Right",
        "left": "Left",
        "izquierda": "Left",
    }
    if raw not in mapping:
        raise ValueError("SideOfFeature invalido. Valores admitidos: Center, Right, Left.")
    return mapping[raw]


def _normalize_plane_name(value: Optional[str]) -> str:
    raw = (value or "Top").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "top": "Top",
        "superior": "Top",
        "carasuperior": "Top",
        "front": "Front",
        "frontal": "Front",
        "caradelantera": "Front",
        "delantera": "Front",
        "back": "Back",
        "trasera": "Back",
        "caratrasera": "Back",
        "right": "Right",
        "derecha": "Right",
        "caraderecha": "Right",
        "left": "Left",
        "izquierda": "Left",
        "caraizquierda": "Left",
    }
    if raw not in mapping:
        raise ValueError(
            "PlaneName invalido. Valores admitidos: Top/Superior, Front/Delantera, "
            "Back/Trasera, Right/Derecha o Left/Izquierda."
        )
    return mapping[raw]


def _normalize_drill_family(value: Optional[str]) -> str:
    raw = (value or "Flat").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "flat": "Flat",
        "plana": "Flat",
        "plano": "Flat",
        "conical": "Conical",
        "conica": "Conical",
        "conico": "Conical",
        "lanza": "Conical",
        "puntadelanza": "Conical",
        "countersunk": "Countersunk",
        "abocinado": "Countersunk",
        "abocinada": "Countersunk",
    }
    if raw not in mapping:
        raise ValueError(
            "DrillFamily invalido. Valores admitidos: Flat/Plana, Conical/Lanza o Countersunk/Abocinado."
        )
    return mapping[raw]


def _normalize_tool_resolution(value: Optional[str]) -> str:
    raw = (value or "Auto").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "auto": "Auto",
        "automatic": "Auto",
        "automatico": "Auto",
        "none": "None",
        "sin": "None",
        "ninguna": "None",
        "empty": "None",
        "explicit": "Explicit",
        "explicita": "Explicit",
        "manual": "Explicit",
    }
    if raw not in mapping:
        raise ValueError("ToolResolution invalido. Valores admitidos: Auto, None o Explicit.")
    return mapping[raw]


def _normalize_approach_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("ApproachType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_approach_mode(value: Optional[str]) -> str:
    raw = (value or "Down").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "down": "Down",
        "vertical": "Down",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("ApproachMode invalido. Valores admitidos: Down o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_approach_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("ApproachArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def _normalize_retract_type(value: Optional[str]) -> str:
    raw = (value or "Line").strip().lower()
    mapping = {
        "line": "Line",
        "lineal": "Line",
        "arc": "Arc",
        "arco": "Arc",
    }
    if raw not in mapping:
        raise ValueError("RetractType invalido. Valores admitidos: Line, Arc.")
    return mapping[raw]


def _normalize_retract_mode(value: Optional[str]) -> str:
    raw = (value or "Up").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "up": "Up",
        "subida": "Up",
        "vertical": "Up",
        "quote": "Quote",
        "encota": "Quote",
    }
    if raw not in mapping:
        raise ValueError("RetractMode invalido. Valores admitidos: Up o Quote (UI Maestro: En Cota).")
    return mapping[raw]


def _normalize_retract_arc_side(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower()
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "left": "Left",
        "izquierda": "Left",
        "right": "Right",
        "derecha": "Right",
    }
    if raw not in mapping:
        raise ValueError("RetractArcSide invalido. Valores admitidos: Automatic, Left, Right.")
    return mapping[raw]


def _normalize_geometry_winding(value: Optional[str]) -> str:
    raw = (value or "CounterClockwise").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "counterclockwise": "CounterClockwise",
        "ccw": "CounterClockwise",
        "antihorario": "CounterClockwise",
        "clockwise": "Clockwise",
        "cw": "Clockwise",
        "horario": "Clockwise",
    }
    if raw not in mapping:
        raise ValueError("Winding invalido. Valores admitidos: CounterClockwise/Antihorario o Clockwise/Horario.")
    return mapping[raw]


def _normalize_squaring_start_edge(value: Optional[str]) -> str:
    raw = (value or "Bottom").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "bottom": "Bottom",
        "inferior": "Bottom",
        "bordeinferior": "Bottom",
        "right": "Right",
        "derecho": "Right",
        "bordederecho": "Right",
        "top": "Top",
        "superior": "Top",
        "bordesuperior": "Top",
        "left": "Left",
        "izquierdo": "Left",
        "bordeizquierdo": "Left",
    }
    if raw not in mapping:
        raise ValueError("StartEdge invalido. Valores admitidos: Bottom/Inferior, Right/Derecho, Top/Superior o Left/Izquierdo.")
    return mapping[raw]


def _normalize_strategy_connection_mode(value: Optional[str]) -> str:
    raw = (value or "Automatic").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "automatic": "Automatic",
        "auto": "Automatic",
        "salidaacotadeseguridad": "SafetyHeight",
        "salidacota": "SafetyHeight",
        "securityheight": "SafetyHeight",
        "safetyheight": "SafetyHeight",
        "liftshiftplunge": "SafetyHeight",
        "enlapieza": "InPiece",
        "inpiece": "InPiece",
        "straightline": "InPiece",
        "straghtline": "InPiece",
    }
    if raw not in mapping:
        raise ValueError(
            "ConnectionMode invalido. Valores admitidos: Automatic, SafetyHeight/SalidaCota o InPiece/EnLaPieza."
        )
    return mapping[raw]


def _normalize_nonnegative_strategy_depth(value: Optional[float], field_name: str) -> float:
    normalized = 0.0 if value is None else float(value)
    if normalized < -1e-9:
        raise ValueError(f"{field_name} no puede ser negativo.")
    return normalized


def _normalize_contour_rotation_direction(value: Optional[str]) -> str:
    raw = (value or "CounterClockwise").strip()
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "counterclockwise": "CounterClockwise",
        "anticlockwise": "CounterClockwise",
        "antihorario": "CounterClockwise",
        "clockwise": "Clockwise",
        "horario": "Clockwise",
    }
    return mapping.get(normalized, raw)


def _normalize_contour_stroke_connection_strategy(value: Optional[str]) -> str:
    raw = (value or "LiftShiftPlunge").strip()
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "liftshiftplunge": "LiftShiftPlunge",
        "salidaacotadeseguridad": "LiftShiftPlunge",
        "salidacotadeseguridad": "LiftShiftPlunge",
        "safetyheight": "LiftShiftPlunge",
        "straghtline": "Straghtline",
        "straightline": "Straghtline",
        "enlapieza": "Straghtline",
        "inpiece": "Straghtline",
    }
    return mapping.get(normalized, raw)


def _normalize_contour_cutmode(value: Optional[str]) -> str:
    raw = (value or "Climb").strip()
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "")
    mapping = {
        "climb": "Climb",
        "concordante": "Climb",
        "conventional": "Conventional",
        "convencional": "Conventional",
    }
    return mapping.get(normalized, raw)


def build_unidirectional_milling_strategy_spec(
    *,
    connection_mode: Optional[str] = None,
    allow_multiple_passes: Optional[bool] = None,
    axial_cutting_depth: Optional[float] = None,
    axial_finish_cutting_depth: Optional[float] = None,
) -> UnidirectionalMillingStrategySpec:
    """Construye una estrategia publica `Unidireccional`.

    `connection_mode` usa nombres canonicos orientados a API:
    - `Automatic`
    - `SafetyHeight` (UI Maestro: Salida a cota de seguridad)
    - `InPiece` (UI Maestro: En la pieza)
    """

    normalized_axial_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_cutting_depth,
        "AxialCuttingDepth",
    )
    normalized_axial_finish_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_finish_cutting_depth,
        "AxialFinishCuttingDepth",
    )
    inferred_allow_multiple_passes = (
        normalized_axial_cutting_depth > 0.0 or normalized_axial_finish_cutting_depth > 0.0
    )
    normalized_allow_multiple_passes = (
        inferred_allow_multiple_passes if allow_multiple_passes is None else bool(allow_multiple_passes)
    )
    if not normalized_allow_multiple_passes and inferred_allow_multiple_passes:
        raise ValueError(
            "No se puede deshabilitar AllowMultiplePasses si AxialCuttingDepth o "
            "AxialFinishCuttingDepth son mayores que cero."
        )
    return UnidirectionalMillingStrategySpec(
        connection_mode=_normalize_strategy_connection_mode(connection_mode),
        allow_multiple_passes=normalized_allow_multiple_passes,
        axial_cutting_depth=normalized_axial_cutting_depth,
        axial_finish_cutting_depth=normalized_axial_finish_cutting_depth,
    )


def build_bidirectional_milling_strategy_spec(
    *,
    allow_multiple_passes: Optional[bool] = None,
    axial_cutting_depth: Optional[float] = None,
    axial_finish_cutting_depth: Optional[float] = None,
) -> BidirectionalMillingStrategySpec:
    """Construye una estrategia publica `Bidireccional`."""

    normalized_axial_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_cutting_depth,
        "AxialCuttingDepth",
    )
    normalized_axial_finish_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_finish_cutting_depth,
        "AxialFinishCuttingDepth",
    )
    inferred_allow_multiple_passes = (
        normalized_axial_cutting_depth > 0.0 or normalized_axial_finish_cutting_depth > 0.0
    )
    normalized_allow_multiple_passes = (
        inferred_allow_multiple_passes if allow_multiple_passes is None else bool(allow_multiple_passes)
    )
    if not normalized_allow_multiple_passes and inferred_allow_multiple_passes:
        raise ValueError(
            "No se puede deshabilitar AllowMultiplePasses si AxialCuttingDepth o "
            "AxialFinishCuttingDepth son mayores que cero."
        )
    return BidirectionalMillingStrategySpec(
        allow_multiple_passes=normalized_allow_multiple_passes,
        axial_cutting_depth=normalized_axial_cutting_depth,
        axial_finish_cutting_depth=normalized_axial_finish_cutting_depth,
    )


def build_helical_milling_strategy_spec(
    *,
    axial_cutting_depth: Optional[float] = None,
    allows_finish_cutting: Optional[bool] = None,
    axial_finish_cutting_depth: Optional[float] = None,
) -> HelicalMillingStrategySpec:
    """Construye una estrategia publica `Helicoidal`.

    Por ahora esta familia queda validada solo para `CircleMillingSpec`.
    """

    normalized_axial_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_cutting_depth,
        "AxialCuttingDepth",
    )
    normalized_axial_finish_cutting_depth = _normalize_nonnegative_strategy_depth(
        axial_finish_cutting_depth,
        "AxialFinishCuttingDepth",
    )
    normalized_allows_finish_cutting = True if allows_finish_cutting is None else bool(allows_finish_cutting)
    if not normalized_allows_finish_cutting and normalized_axial_finish_cutting_depth > 0.0:
        raise ValueError(
            "No se puede definir AxialFinishCuttingDepth mayor que cero si AllowsFinishCutting esta deshabilitado."
        )
    return HelicalMillingStrategySpec(
        axial_cutting_depth=normalized_axial_cutting_depth,
        allows_finish_cutting=normalized_allows_finish_cutting,
        axial_finish_cutting_depth=normalized_axial_finish_cutting_depth,
    )


def build_contour_parallel_milling_strategy_spec(
    *,
    rotation_direction: Optional[str] = None,
    stroke_connection_strategy: Optional[str] = None,
    inside_to_outside: Optional[bool] = None,
    overlap: Optional[float] = None,
    is_helic_strategy: Optional[bool] = None,
    allow_multiple_passes: Optional[bool] = None,
    axial_cutting_depth: Optional[float] = None,
    axial_finish_cutting_depth: Optional[float] = None,
    cutmode: Optional[str] = None,
    is_internal: Optional[bool] = None,
    radial_cutting_depth: Optional[float] = None,
    radial_finish_cutting_depth: Optional[float] = None,
    allows_bidirectional: Optional[bool] = None,
    allows_finish_cutting: Optional[bool] = None,
) -> ContourParallelMillingStrategySpec:
    """Construye una estrategia `Paralela al perfil/contorno` para lectura.

    La serializacion productiva de esta estrategia todavia no esta habilitada.
    """

    normalized_overlap = 0.5 if overlap is None else float(overlap)
    if normalized_overlap < -1e-9:
        raise ValueError("Overlap no puede ser negativo.")
    return ContourParallelMillingStrategySpec(
        rotation_direction=_normalize_contour_rotation_direction(rotation_direction),
        stroke_connection_strategy=_normalize_contour_stroke_connection_strategy(stroke_connection_strategy),
        inside_to_outside=True if inside_to_outside is None else bool(inside_to_outside),
        overlap=normalized_overlap,
        is_helic_strategy=False if is_helic_strategy is None else bool(is_helic_strategy),
        allow_multiple_passes=False if allow_multiple_passes is None else bool(allow_multiple_passes),
        axial_cutting_depth=_normalize_nonnegative_strategy_depth(axial_cutting_depth, "AxialCuttingDepth"),
        axial_finish_cutting_depth=_normalize_nonnegative_strategy_depth(
            axial_finish_cutting_depth,
            "AxialFinishCuttingDepth",
        ),
        cutmode=_normalize_contour_cutmode(cutmode),
        is_internal=True if is_internal is None else bool(is_internal),
        radial_cutting_depth=_normalize_nonnegative_strategy_depth(radial_cutting_depth, "RadialCuttingDepth"),
        radial_finish_cutting_depth=_normalize_nonnegative_strategy_depth(
            radial_finish_cutting_depth,
            "RadialFinishCuttingDepth",
        ),
        allows_bidirectional=False if allows_bidirectional is None else bool(allows_bidirectional),
        allows_finish_cutting=False if allows_finish_cutting is None else bool(allows_finish_cutting),
    )


def _normalize_xn_reference(value: Optional[str]) -> str:
    raw = (value or "Absolute").strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "absolute": "Absolute",
        "absoluto": "Absolute",
        "relative": "Relative",
        "relativo": "Relative",
    }
    normalized = mapping.get(raw)
    if normalized is None:
        raise ValueError("Reference invalido para Xn. Valores admitidos: Absolute/Absoluto o Relative/Relativo.")
    return normalized


def build_xn_spec(
    *,
    reference: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
) -> XnSpec:
    """Construye la spec publica `Xn` con defaults observados en Maestro."""

    return XnSpec(
        reference=_normalize_xn_reference(reference),
        x=-3700.0 if x is None else float(x),
        y=None if y is None else float(y),
    )


def _normalize_xn_spec(xn: Optional[XnSpec]) -> XnSpec:
    if xn is None:
        return build_xn_spec()
    return build_xn_spec(
        reference=xn.reference,
        x=xn.x,
        y=xn.y,
    )


def _normalize_milling_strategy_spec(
    strategy: Optional[MillingStrategySpec],
) -> Optional[MillingStrategySpec]:
    if strategy is None:
        return None
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return build_unidirectional_milling_strategy_spec(
            connection_mode=strategy.connection_mode,
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
    if isinstance(strategy, BidirectionalMillingStrategySpec):
        return build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
    if isinstance(strategy, HelicalMillingStrategySpec):
        return build_helical_milling_strategy_spec(
            axial_cutting_depth=strategy.axial_cutting_depth,
            allows_finish_cutting=strategy.allows_finish_cutting,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
        )
    if isinstance(strategy, ContourParallelMillingStrategySpec):
        return build_contour_parallel_milling_strategy_spec(
            rotation_direction=strategy.rotation_direction,
            stroke_connection_strategy=strategy.stroke_connection_strategy,
            inside_to_outside=strategy.inside_to_outside,
            overlap=strategy.overlap,
            is_helic_strategy=strategy.is_helic_strategy,
            allow_multiple_passes=strategy.allow_multiple_passes,
            axial_cutting_depth=strategy.axial_cutting_depth,
            axial_finish_cutting_depth=strategy.axial_finish_cutting_depth,
            cutmode=strategy.cutmode,
            is_internal=strategy.is_internal,
            radial_cutting_depth=strategy.radial_cutting_depth,
            radial_finish_cutting_depth=strategy.radial_finish_cutting_depth,
            allows_bidirectional=strategy.allows_bidirectional,
            allows_finish_cutting=strategy.allows_finish_cutting,
        )
    raise ValueError(f"Tipo de estrategia de fresado no soportado: {type(strategy)!r}")


def _ensure_milling_strategy_allowed(
    strategy: Optional[MillingStrategySpec],
    *,
    allowed_types: tuple[type, ...],
    context: str,
) -> Optional[MillingStrategySpec]:
    if strategy is None:
        return None
    if isinstance(strategy, allowed_types):
        return strategy
    admitted = ", ".join(sorted(strategy_type.__name__ for strategy_type in allowed_types))
    raise ValueError(
        f"La estrategia {type(strategy).__name__} no esta validada para {context}. "
        f"Estrategias admitidas: {admitted}."
    )


def build_milling_depth_spec(
    is_through: Optional[bool] = None,
    *,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
) -> MillingDepthSpec:
    """Construye un `MillingDepthSpec` reusable para Pasante/Extra/Profundidad.

    Reglas:
    - si no se pasa nada, devuelve el default observado en Maestro
    - si `is_through=True`, `extra_depth` representa `Extra`
    - si `is_through=False`, `target_depth` es obligatorio y `extra_depth` no aplica
    - Maestro permite `target_depth = 0` como estado manual neutro/default para
      un fresado no pasante recien creado; por eso se admite `0` al leer o
      construir plantillas
    """

    has_explicit_configuration = any(value is not None for value in (is_through, target_depth, extra_depth))
    if not has_explicit_configuration:
        return MillingDepthSpec()

    normalized_is_through = (target_depth is None) if is_through is None else bool(is_through)
    if normalized_is_through:
        extra_value = 0.0 if extra_depth is None else float(extra_depth)
        if extra_value < -1e-9:
            raise ValueError("ExtraDepth no puede ser negativo.")
        return MillingDepthSpec(is_through=True, target_depth=None, extra_depth=extra_value)

    if target_depth is None:
        raise ValueError("Para un fresado no pasante hay que indicar target_depth.")
    target_depth_value = float(target_depth)
    if target_depth_value < 0.0:
        raise ValueError("La profundidad no pasante debe ser mayor o igual a cero.")
    extra_value = 0.0 if extra_depth is None else float(extra_depth)
    if not math.isclose(extra_value, 0.0, abs_tol=1e-9):
        raise ValueError("ExtraDepth solo aplica a fresados pasantes.")
    return MillingDepthSpec(is_through=False, target_depth=target_depth_value, extra_depth=0.0)


def build_line_geometry_primitive(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    *,
    start_z: float = 0.0,
    end_z: float = 0.0,
) -> GeometryPrimitiveSpec:
    """Construye una primitiva lineal reusable para perfiles Maestro."""

    start_point = (float(start_x), float(start_y), float(start_z))
    end_point = (float(end_x), float(end_y), float(end_z))
    length = math.dist(start_point, end_point)
    if length <= 1e-9:
        raise ValueError("Una primitiva lineal necesita longitud mayor que cero.")
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=start_point,
        end_point=end_point,
        parameter_start=0.0,
        parameter_end=length,
    )


def _build_parameterized_line_geometry_primitive(
    origin_point: tuple[float, float, float],
    direction: tuple[float, float, float],
    parameter_start: float,
    parameter_end: float,
) -> GeometryPrimitiveSpec:
    direction_length = math.sqrt(
        (direction[0] * direction[0]) + (direction[1] * direction[1]) + (direction[2] * direction[2])
    )
    if direction_length <= 1e-9:
        raise ValueError("La direccion de una linea parametrizada no puede ser nula.")
    unit_direction = (
        direction[0] / direction_length,
        direction[1] / direction_length,
        direction[2] / direction_length,
    )
    start_value = float(parameter_start)
    end_value = float(parameter_end)
    if math.isclose(start_value, end_value, abs_tol=1e-9):
        raise ValueError("Una linea parametrizada necesita un rango no nulo.")
    start_point = (
        origin_point[0] + (unit_direction[0] * start_value),
        origin_point[1] + (unit_direction[1] * start_value),
        origin_point[2] + (unit_direction[2] * start_value),
    )
    end_point = (
        origin_point[0] + (unit_direction[0] * end_value),
        origin_point[1] + (unit_direction[1] * end_value),
        origin_point[2] + (unit_direction[2] * end_value),
    )
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=start_point,
        end_point=end_point,
        parameter_start=start_value,
        parameter_end=end_value,
    )


def build_arc_geometry_primitive(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    center_x: float,
    center_y: float,
    *,
    z_value: float = 0.0,
    winding: Optional[str] = None,
) -> GeometryPrimitiveSpec:
    """Construye una primitiva de arco en XY reusable para perfiles Maestro."""

    normalized_winding = _normalize_geometry_winding(winding)
    normal_z = 1.0 if normalized_winding == "CounterClockwise" else -1.0
    normal_y = -0.0 if normalized_winding == "CounterClockwise" else 0.0
    v_x = -0.0 if normalized_winding == "CounterClockwise" else 0.0
    start_point = (float(start_x), float(start_y), float(z_value))
    end_point = (float(end_x), float(end_y), float(z_value))
    center_point = (float(center_x), float(center_y), float(z_value))
    start_radius = math.dist(start_point, center_point)
    end_radius = math.dist(end_point, center_point)
    if start_radius <= 1e-9 or end_radius <= 1e-9:
        raise ValueError("Una primitiva de arco necesita radio mayor que cero.")
    if not math.isclose(start_radius, end_radius, abs_tol=1e-6):
        raise ValueError("Los puntos inicial y final del arco deben estar al mismo radio del centro.")
    start_angle = _point_to_maestro_basis_angle((center_point[0], center_point[1]), (start_point[0], start_point[1]), normal_z)
    end_angle = _point_to_maestro_basis_angle((center_point[0], center_point[1]), (end_point[0], end_point[1]), normal_z)
    end_angle = _unwrap_maestro_arc_end_angle(start_angle, end_angle)
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=start_angle,
        parameter_end=end_angle,
        center_point=center_point,
        radius=start_radius,
        normal_vector=(0.0, normal_y, normal_z),
        u_vector=(1.0, 0.0, 0.0),
        v_vector=(v_x, normal_z, 0.0),
    )


def build_line_geometry_profile(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    *,
    start_z: float = 0.0,
    end_z: float = 0.0,
) -> GeometryProfileSpec:
    """Construye un perfil geometrico lineal ya serializado para Maestro."""

    primitive = build_line_geometry_primitive(
        start_x,
        start_y,
        end_x,
        end_y,
        start_z=start_z,
        end_z=end_z,
    )
    return _build_profile_geometry_spec(
        geometry_type="GeomTrimmedCurve",
        primitives=(primitive,),
    )


def build_point_geometry_profile(
    point_x: float,
    point_y: float,
    *,
    z_value: float = 0.0,
) -> GeometryProfileSpec:
    """Construye un punto geometrico Maestro listo para inspeccion o futura sintesis."""

    point = (float(point_x), float(point_y), float(z_value))
    primitive = GeometryPrimitiveSpec(
        primitive_type="Point",
        start_point=point,
        end_point=point,
    )
    return _build_profile_geometry_spec(
        geometry_type="GeomCartesianPoint",
        primitives=(primitive,),
    )


def build_circle_geometry_profile(
    center_x: float,
    center_y: float,
    radius: float,
    *,
    z_value: float = 0.0,
    winding: Optional[str] = None,
) -> GeometryProfileSpec:
    """Construye un perfil circular Maestro listo para futura sintesis."""

    normalized_winding = _normalize_geometry_winding(winding)
    radius_value = float(radius)
    if radius_value <= 1e-9:
        raise ValueError("Un perfil circular necesita radio mayor que cero.")
    normal_z = 1.0 if normalized_winding == "CounterClockwise" else -1.0
    serialization = _build_circle_geometry_serialization(
        center_point=(float(center_x), float(center_y), float(z_value)),
        radius=radius_value,
        normal_z=normal_z,
    )
    return GeometryProfileSpec(
        geometry_type="GeomCircle",
        family="Circle",
        is_closed=True,
        winding=normalized_winding,
        has_arcs=True,
        corner_radii=(radius_value,),
        bounding_box=(
            float(center_x) - radius_value,
            float(center_y) - radius_value,
            float(center_x) + radius_value,
            float(center_y) + radius_value,
        ),
        center_point=(float(center_x), float(center_y), float(z_value)),
        radius=radius_value,
        serialization=serialization,
    )


def build_composite_geometry_profile(
    primitives: Sequence[GeometryPrimitiveSpec],
) -> GeometryProfileSpec:
    """Construye un perfil compuesto reusable a partir de lineas y arcos."""

    normalized_primitives = tuple(primitives)
    if not normalized_primitives:
        raise ValueError("Un perfil compuesto necesita al menos una primitiva.")
    return _build_profile_geometry_spec(
        geometry_type="GeomCompositeCurve",
        primitives=normalized_primitives,
    )


def build_compensated_toolpath_profile(
    profile: GeometryProfileSpec,
    *,
    side_of_feature: Optional[str] = None,
    tool_width: float,
    z_value: Optional[float] = None,
) -> GeometryProfileSpec:
    """Compensa una geometria nominal segun `SideOfFeature` y el ancho de herramienta.

    Esta helper vuelca en codigo las reglas observadas en Maestro para:
    - lineas
    - arcos
    - circulos
    - polilineas abiertas
    - polilineas cerradas con esquinas vivas
    - polilineas cerradas redondeadas y otras curvas compuestas tangentes

    El resultado es el perfil efectivo que debe seguir el centro de la herramienta.
    La geometria nominal original no se altera.
    """

    return _build_compensated_profile_geometry(
        profile,
        side_of_feature=_normalize_side_of_feature(side_of_feature),
        tool_width=float(tool_width),
        z_value=z_value,
    )


def build_approach_spec(
    enabled: Optional[bool] = None,
    *,
    approach_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
) -> ApproachSpec:
    """Construye un `ApproachSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Approach` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, approach_type, mode, radius_multiplier, speed, arc_side)
    )
    if not has_explicit_configuration:
        return ApproachSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Down"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return ApproachSpec(
        is_enabled=is_enabled,
        approach_type=_normalize_approach_type(approach_type or "Line"),
        mode=_normalize_approach_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_approach_arc_side(arc_side or "Automatic"),
    )


def build_retract_spec(
    enabled: Optional[bool] = None,
    *,
    retract_type: Optional[str] = None,
    mode: Optional[str] = None,
    radius_multiplier: Optional[float] = None,
    speed: Optional[float] = None,
    arc_side: Optional[str] = None,
    overlap: Optional[float] = None,
) -> RetractSpec:
    """Construye un `RetractSpec` con defaults observados en Maestro.

    Si no se pasa ningun parametro, deja el `Retract` deshabilitado.
    Si se configura cualquier campo, completa el resto con defaults coherentes.
    """

    has_explicit_configuration = any(
        value is not None for value in (enabled, retract_type, mode, radius_multiplier, speed, arc_side, overlap)
    )
    if not has_explicit_configuration:
        return RetractSpec()

    is_enabled = True if enabled is None else bool(enabled)
    default_mode = "Quote" if is_enabled else "Up"
    default_radius_multiplier = 2.0 if is_enabled else 1.2
    default_speed = -1.0 if is_enabled else 0.0
    return RetractSpec(
        is_enabled=is_enabled,
        retract_type=_normalize_retract_type(retract_type or "Line"),
        mode=_normalize_retract_mode(mode or default_mode),
        radius_multiplier=default_radius_multiplier if radius_multiplier is None else float(radius_multiplier),
        speed=default_speed if speed is None else float(speed),
        arc_side=_normalize_retract_arc_side(arc_side or "Automatic"),
        overlap=0.0 if overlap is None else float(overlap),
    )


def _normalize_approach_spec(approach: Optional[ApproachSpec]) -> ApproachSpec:
    if approach is None:
        return ApproachSpec()
    return build_approach_spec(
        enabled=approach.is_enabled,
        approach_type=approach.approach_type,
        mode=approach.mode,
        radius_multiplier=approach.radius_multiplier,
        speed=approach.speed,
        arc_side=approach.arc_side,
    )


def _normalize_retract_spec(retract: Optional[RetractSpec]) -> RetractSpec:
    if retract is None:
        return RetractSpec()
    return build_retract_spec(
        enabled=retract.is_enabled,
        retract_type=retract.retract_type,
        mode=retract.mode,
        radius_multiplier=retract.radius_multiplier,
        speed=retract.speed,
        arc_side=retract.arc_side,
        overlap=retract.overlap,
    )


def _normalize_milling_depth_spec(depth_spec: Optional[MillingDepthSpec]) -> MillingDepthSpec:
    if depth_spec is None:
        return MillingDepthSpec()
    return build_milling_depth_spec(
        is_through=depth_spec.is_through,
        target_depth=depth_spec.target_depth,
        extra_depth=depth_spec.extra_depth,
    )


def _normalize_line_milling_spec(line_milling: LineMillingSpec) -> LineMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(line_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="LineMillingSpec",
    )
    return replace(
        line_milling,
        side_of_feature=_normalize_side_of_feature(line_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(line_milling.depth_spec),
        approach=_normalize_approach_spec(line_milling.approach),
        retract=_normalize_retract_spec(line_milling.retract),
        milling_strategy=normalized_strategy,
    )


def _normalize_slot_milling_spec(slot_milling: SlotMillingSpec) -> SlotMillingSpec:
    if math.isclose(float(slot_milling.start_x), float(slot_milling.end_x), abs_tol=1e-9) and math.isclose(
        float(slot_milling.start_y),
        float(slot_milling.end_y),
        abs_tol=1e-9,
    ):
        raise ValueError("La ranura no puede tener longitud cero.")
    end_radius = float(slot_milling.end_radius)
    if end_radius < 0.0:
        raise ValueError("El radio de extremo de la ranura no puede ser negativo.")
    return replace(
        slot_milling,
        start_x=float(slot_milling.start_x),
        start_y=float(slot_milling.start_y),
        end_x=float(slot_milling.end_x),
        end_y=float(slot_milling.end_y),
        plane_name=_normalize_plane_name(slot_milling.plane_name),
        side_of_feature=_normalize_side_of_feature(slot_milling.side_of_feature),
        tool_id=(slot_milling.tool_id or "1899").strip() or "1899",
        tool_name=(slot_milling.tool_name or "082").strip() or "082",
        tool_width=float(slot_milling.tool_width),
        security_plane=float(slot_milling.security_plane),
        depth_spec=_normalize_milling_depth_spec(slot_milling.depth_spec),
        approach=_normalize_approach_spec(slot_milling.approach),
        retract=_normalize_retract_spec(slot_milling.retract),
        material_position=(slot_milling.material_position or "Left").strip() or "Left",
        side_offset=float(slot_milling.side_offset),
        end_radius=end_radius,
        slot_angle=float(slot_milling.slot_angle),
    )


def _workpiece_depth_name(workpiece: Optional[ET.Element]) -> str:
    """Devuelve el nombre parametrico de espesor usado por la pieza.

    Maestro suele usar `dz1`, pero conviene leerlo del `WorkPiece` para no
    fijar la sintesis a un unico baseline.
    """

    return _text(workpiece, "./{*}DepthName", "dz1") or "dz1"


def _workpiece_length_name(workpiece: Optional[ET.Element]) -> str:
    return _text(workpiece, "./{*}LengthName", "dx1") or "dx1"


def _workpiece_width_name(workpiece: Optional[ET.Element]) -> str:
    return _text(workpiece, "./{*}WidthName", "dy1") or "dy1"


def _normalize_polyline_points(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    normalized = tuple((float(point[0]), float(point[1])) for point in points)
    if len(normalized) < 2:
        raise ValueError("Una polilinea necesita al menos 2 puntos.")
    for start_point, end_point in zip(normalized, normalized[1:]):
        if math.isclose(start_point[0], end_point[0], abs_tol=1e-9) and math.isclose(
            start_point[1], end_point[1], abs_tol=1e-9
        ):
            raise ValueError("La polilinea no puede contener segmentos de longitud cero.")
    return normalized


def _is_closed_polyline_points(points: Sequence[tuple[float, float]]) -> bool:
    normalized_points = tuple((float(point[0]), float(point[1])) for point in points)
    return len(normalized_points) >= 4 and _points_close_2d(normalized_points[0], normalized_points[-1])


def _validate_polyline_postprocessable_by_maestro(spec: PolylineMillingSpec) -> None:
    """Bloquea una combinacion que Maestro no logra postprocesar a ISO."""

    points = _normalize_polyline_points(spec.points)
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    retract = _normalize_retract_spec(spec.retract)
    is_open_multisegment = len(points) > 2 and not _is_closed_polyline_points(points)
    has_ph_multipass = bool(strategy and strategy.allow_multiple_passes)
    uses_arc_up_retract = (
        retract.is_enabled
        and retract.retract_type == "Arc"
        and retract.mode == "Up"
    )
    if is_open_multisegment and has_ph_multipass and uses_arc_up_retract:
        raise ValueError(
            "Maestro no postprocesa polilineas abiertas de varios segmentos con "
            "estrategia multipasada PH y Retract Arc + Up. Usar Retract Line + Up "
            "o Arc + Quote para obtener ISO postprocesable."
        )


def _normalize_polyline_milling_spec(polyline_milling: PolylineMillingSpec) -> PolylineMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(polyline_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="PolylineMillingSpec",
    )
    normalized_spec = replace(
        polyline_milling,
        points=_normalize_polyline_points(polyline_milling.points),
        side_of_feature=_normalize_side_of_feature(polyline_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(polyline_milling.depth_spec),
        approach=_normalize_approach_spec(polyline_milling.approach),
        retract=_normalize_retract_spec(polyline_milling.retract),
        milling_strategy=normalized_strategy,
    )
    _validate_polyline_postprocessable_by_maestro(normalized_spec)
    return normalized_spec


def _normalize_circle_milling_spec(circle_milling: CircleMillingSpec) -> CircleMillingSpec:
    radius_value = float(circle_milling.radius)
    if radius_value <= 1e-9:
        raise ValueError("El radio del fresado circular debe ser mayor que cero.")
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(circle_milling.milling_strategy),
        allowed_types=(
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
        ),
        context="CircleMillingSpec",
    )
    return replace(
        circle_milling,
        center_x=float(circle_milling.center_x),
        center_y=float(circle_milling.center_y),
        radius=radius_value,
        winding=_normalize_geometry_winding(circle_milling.winding),
        side_of_feature=_normalize_side_of_feature(circle_milling.side_of_feature),
        depth_spec=_normalize_milling_depth_spec(circle_milling.depth_spec),
        approach=_normalize_approach_spec(circle_milling.approach),
        retract=_normalize_retract_spec(circle_milling.retract),
        milling_strategy=normalized_strategy,
    )


def _normalize_squaring_milling_spec(squaring_milling: SquaringMillingSpec) -> SquaringMillingSpec:
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(squaring_milling.milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="SquaringMillingSpec",
    )
    return replace(
        squaring_milling,
        start_edge=_normalize_squaring_start_edge(squaring_milling.start_edge),
        winding=_normalize_geometry_winding(squaring_milling.winding),
        depth_spec=_normalize_milling_depth_spec(squaring_milling.depth_spec),
        approach=_normalize_approach_spec(squaring_milling.approach),
        retract=_normalize_retract_spec(squaring_milling.retract),
        milling_strategy=normalized_strategy,
    )


def _load_tool_catalog() -> dict[str, dict[str, str]]:
    """Carga el catalogo plano de herramientas indexado por `tool_id`."""

    if not TOOL_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"No existe el catalogo de herramientas '{TOOL_CATALOG_PATH}'."
        )
    with TOOL_CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    return {
        str((row.get("tool_id") or "").strip()): row
        for row in rows
        if (row.get("tool_id") or "").strip()
    }


_AUTO_VERTICAL_DRILL_TOOLS: dict[tuple[str, str], tuple[str, str]] = {
    ("Flat", "8"): ("1888", "001"),
    ("Flat", "15"): ("1889", "002"),
    ("Flat", "20"): ("1890", "003"),
    ("Flat", "35"): ("1891", "004"),
    ("Flat", "5"): ("1892", "005"),
    ("Flat", "4"): ("1893", "006"),
    ("Conical", "5"): ("1894", "007"),
}

def _lookup_tool_catalog_entry(
    tool_catalog: dict[str, dict[str, str]],
    *,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> dict[str, str]:
    normalized_tool_id = (tool_id or "").strip()
    normalized_tool_name = (tool_name or "").strip()
    if normalized_tool_id == "0" and normalized_tool_name:
        normalized_tool_id = ""

    if normalized_tool_id:
        row = tool_catalog.get(normalized_tool_id)
        if row is None:
            raise ValueError(
                f"No existe la herramienta '{normalized_tool_id}' en '{TOOL_CATALOG_PATH.name}'."
            )
        if normalized_tool_name and (row.get("name") or "").strip() != normalized_tool_name:
            raise ValueError(
                "La herramienta explicita no coincide con el catalogo: "
                f"id={normalized_tool_id} corresponde a '{(row.get('name') or '').strip()}'."
            )
        return row

    if normalized_tool_name:
        for row in tool_catalog.values():
            if (row.get("name") or "").strip() == normalized_tool_name:
                return row
        raise ValueError(
            f"No existe la herramienta '{normalized_tool_name}' en '{TOOL_CATALOG_PATH.name}'."
        )

    raise ValueError("La resolucion explicita de herramienta requiere tool_id, tool_name o ambos.")


def _feature_depth_value(state: PgmxState, spec) -> float:
    # En Maestro, un pasante deja `Depth.StartDepth/EndDepth` igual al espesor
    # actual de la pieza y luego agrega expresiones parametricas hacia `DepthName`.
    # Por eso, para el feature serializado, el valor numerico base del pasante es
    # `state.depth`, mientras que la cota real del toolpath se corrige aparte con
    # `_toolpath_cut_z(...)`.
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    if depth_spec.target_depth > state.depth + 1e-9:
        raise ValueError("La profundidad del fresado no pasante no puede superar el espesor de la pieza.")
    return depth_spec.target_depth


def _tool_total_milling_depth(state: PgmxState, spec) -> float:
    """Calcula la profundidad total efectiva que debe alcanzar la herramienta."""

    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return state.depth + depth_spec.extra_depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del fresado no pasante no puede quedar vacia.")
    return depth_spec.target_depth


def _tool_catalog_label(spec) -> str:
    return f"{spec.tool_name} ({spec.tool_id})"


def _diameter_key(value: float) -> str:
    return _compact_number(float(value))


def _plane_local_dimensions(state: PgmxState, plane_name: str) -> tuple[float, float]:
    normalized_plane_name = _normalize_plane_name(plane_name)
    mapping = {
        "Top": (state.length, state.width),
        "Front": (state.length, state.depth),
        "Back": (state.length, state.depth),
        "Right": (state.width, state.depth),
        "Left": (state.width, state.depth),
    }
    return mapping[normalized_plane_name]


def _drilling_axis_span(state: PgmxState, plane_name: str) -> float:
    normalized_plane_name = _normalize_plane_name(plane_name)
    mapping = {
        "Top": state.depth,
        "Front": state.width,
        "Back": state.width,
        "Right": state.length,
        "Left": state.length,
    }
    return mapping[normalized_plane_name]


def _drilling_axis_variable_name(workpiece: Optional[ET.Element], plane_name: str) -> str:
    normalized_plane_name = _normalize_plane_name(plane_name)
    if normalized_plane_name == "Top":
        return _workpiece_depth_name(workpiece)
    if normalized_plane_name in {"Front", "Back"}:
        return _workpiece_width_name(workpiece)
    return _workpiece_length_name(workpiece)


def _drilling_entry_point_and_direction(
    state: PgmxState,
    spec: _HydratedDrillingSpec,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    plane_name = spec.plane_name
    local_x = spec.center_x
    local_y = spec.center_y
    if plane_name == "Top":
        return (local_x, local_y, state.depth), (0.0, 0.0, -1.0)
    if plane_name == "Front":
        return (local_x, 0.0, local_y), (0.0, 1.0, 0.0)
    if plane_name == "Back":
        return (state.length - local_x, state.width, local_y), (0.0, -1.0, 0.0)
    if plane_name == "Right":
        return (state.length, local_x, local_y), (-1.0, 0.0, 0.0)
    if plane_name == "Left":
        return (0.0, state.width - local_x, local_y), (1.0, 0.0, 0.0)
    raise ValueError(f"No hay una transformacion de taladro validada para el plano '{plane_name}'.")


def _drilling_feature_depth_value(state: PgmxState, spec: _HydratedDrillingSpec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    plane_span = _drilling_axis_span(state, spec.plane_name)
    if depth_spec.is_through:
        return plane_span
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del taladro no pasante no puede quedar vacia.")
    if depth_spec.target_depth > plane_span + 1e-9:
        raise ValueError(
            "La profundidad del taladro no pasante no puede superar el espesor util de la cara."
        )
    return depth_spec.target_depth


def _drilling_total_depth(state: PgmxState, spec: _HydratedDrillingSpec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return _drilling_axis_span(state, spec.plane_name) + depth_spec.extra_depth
    if depth_spec.target_depth is None:
        raise ValueError("La profundidad del taladro no pasante no puede quedar vacia.")
    return depth_spec.target_depth


def _drilling_bottom_condition_type(spec: _HydratedDrillingSpec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return "a:ThroughHoleBottom"
    if spec.drill_family == "Conical" and spec.tool_object_type == "System.Object":
        return "a:ConicalHoleBottom"
    return "a:FlatHoleBottom"


def _uses_drilling_depth_expressions(spec: _HydratedDrillingSpec) -> bool:
    return _normalize_milling_depth_spec(spec.depth_spec).is_through


def _validate_drilling_center(state: PgmxState, spec: _HydratedDrillingSpec) -> None:
    max_x, max_y = _plane_local_dimensions(state, spec.plane_name)
    if spec.center_x < -1e-9 or spec.center_x > max_x + 1e-9:
        raise ValueError(
            f"El centro X del taladro cae fuera del plano '{spec.plane_name}': "
            f"{_compact_number(spec.center_x)} no pertenece a [0, {_compact_number(max_x)}]."
        )
    if spec.center_y < -1e-9 or spec.center_y > max_y + 1e-9:
        raise ValueError(
            f"El centro Y del taladro cae fuera del plano '{spec.plane_name}': "
            f"{_compact_number(spec.center_y)} no pertenece a [0, {_compact_number(max_y)}]."
        )


def _default_drill_family(
    plane_name: str,
    diameter: float,
    depth_spec: MillingDepthSpec,
    requested_family: Optional[str],
) -> str:
    if requested_family is not None:
        return _normalize_drill_family(requested_family)
    if depth_spec.is_through and plane_name == "Top" and math.isclose(float(diameter), 5.0, abs_tol=1e-9):
        return "Conical"
    return "Flat"


def _resolve_drilling_tool(
    drilling: DrillingSpec,
    tool_catalog: dict[str, dict[str, str]],
) -> tuple[str, str, str]:
    if drilling.tool_resolution == "None":
        return "0", "", "System.Object"

    if drilling.tool_resolution == "Explicit":
        row = _lookup_tool_catalog_entry(
            tool_catalog,
            tool_id=drilling.tool_id,
            tool_name=drilling.tool_name,
        )
        return (
            str((row.get("tool_id") or "").strip()),
            str((row.get("name") or "").strip()),
            "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
        )

    if drilling.plane_name in {"Front", "Back", "Right", "Left"}:
        # En los taladros laterales Maestro deja la operacion sin ToolKey hasta
        # el postprocesado. Forzar 058/059/060/061 desde el PGMX puede asignar
        # una broca incorrecta segun el sentido real de la cara.
        return "0", "", "System.Object"

    diameter_key = _diameter_key(drilling.diameter)
    tool_key = _AUTO_VERTICAL_DRILL_TOOLS.get((drilling.drill_family, diameter_key))
    if tool_key is None:
        raise ValueError(
            "No hay una herramienta vertical auto-resoluble para ese diametro/familia en el toolset relevado."
        )

    row = _lookup_tool_catalog_entry(
        tool_catalog,
        tool_id=tool_key[0],
        tool_name=tool_key[1],
    )
    return (
        str((row.get("tool_id") or "").strip()),
        str((row.get("name") or "").strip()),
        "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
    )


def _normalize_drilling_spec(drilling: DrillingSpec) -> DrillingSpec:
    normalized_plane_name = _normalize_plane_name(drilling.plane_name)
    normalized_depth_spec = _normalize_milling_depth_spec(drilling.depth_spec)
    normalized_drill_family = _normalize_drill_family(drilling.drill_family)
    if normalized_drill_family == "Countersunk":
        raise ValueError(
            "La familia `Countersunk/Abocinado` todavia no tiene un caso manual validado en Maestro."
        )
    if normalized_drill_family == "Conical":
        if normalized_plane_name != "Top":
            raise ValueError("La broca conica solo esta validada por ahora sobre la cara `Top`.")
        if not math.isclose(float(drilling.diameter), 5.0, abs_tol=1e-9):
            raise ValueError("La broca conica relevada hasta ahora solo existe en `D5`.")
    diameter_value = float(drilling.diameter)
    if diameter_value <= 0.0:
        raise ValueError("El diametro del taladro debe ser mayor que cero.")
    security_plane_value = float(drilling.security_plane)
    if security_plane_value < 0.0:
        raise ValueError("SecurityPlane no puede ser negativo.")
    return replace(
        drilling,
        center_x=float(drilling.center_x),
        center_y=float(drilling.center_y),
        diameter=diameter_value,
        feature_name=(drilling.feature_name or "Taladrado").strip() or "Taladrado",
        plane_name=normalized_plane_name,
        security_plane=security_plane_value,
        depth_spec=normalized_depth_spec,
        drill_family=normalized_drill_family,
        tool_resolution=_normalize_tool_resolution(drilling.tool_resolution),
        tool_id=(drilling.tool_id or "").strip() or "0",
        tool_name=(drilling.tool_name or "").strip(),
    )


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


def _validate_tool_sinking_length_for_spec(
    state: PgmxState,
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    """Valida que la profundidad total no supere el `sinking_length` de la herramienta."""

    catalog_entry = tool_catalog.get(spec.tool_id)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar la seguridad de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    sinking_length_text = (catalog_entry.get("sinking_length") or "").strip()
    sinking_length = float(sinking_length_text or "0")
    if sinking_length <= 0.0:
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} no tiene un `sinking_length` valido en '{TOOL_CATALOG_PATH.name}'."
        )

    total_depth = _tool_total_milling_depth(state, spec)
    if total_depth > sinking_length + 1e-9:
        raise ValueError(
            "La profundidad total del fresado excede el `sinking_length` de la herramienta: "
            f"{_tool_catalog_label(spec)} permite { _compact_number(sinking_length) } mm, "
            f"pero la solicitud requiere { _compact_number(total_depth) } mm."
        )


def _normalize_tool_usage_group(tool_type: str) -> str:
    normalized = (tool_type or "").strip().lower()
    if normalized.startswith("broca"):
        return "drilling"
    if normalized.startswith("fresa") or normalized.startswith("freza"):
        return "milling"
    if normalized.startswith("sierra"):
        return "saw"
    return "other"


def _is_vertical_x_saw(tool_type: str) -> bool:
    return (tool_type or "").strip().lower() == "sierra vertical x"


def _validate_vertical_x_saw_for_milling_spec(spec, tool_type: str) -> None:
    if not isinstance(spec, (_HydratedLineMillingSpec, _HydratedSlotMillingSpec)):
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite ranurados lineales rectos."
        )

    if _normalize_plane_name(spec.plane_name) != "Top":
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite ranurados sobre el plano Top."
        )

    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite ranurados no pasantes."
        )

    if not math.isclose(float(spec.start_y), float(spec.end_y), abs_tol=1e-9):
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} ({tool_type}) solo permite líneas horizontales."
        )


def _validate_tool_type_for_milling_spec(spec, tool_catalog: dict[str, dict[str, str]]) -> None:
    catalog_entry = tool_catalog.get(spec.tool_id)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar el tipo de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    tool_type = (catalog_entry.get("type") or "").strip()
    usage_group = _normalize_tool_usage_group(tool_type)
    if isinstance(spec, _HydratedSlotMillingSpec):
        if not _is_vertical_x_saw(tool_type):
            raise ValueError(
                "La ranura `SlotSide` requiere una Sierra Vertical X compatible: "
                f"{_tool_catalog_label(spec)} figura como '{tool_type or 'sin tipo'}'."
            )
        _validate_vertical_x_saw_for_milling_spec(spec, tool_type)
        return
    if usage_group == "milling":
        return
    if _is_vertical_x_saw(tool_type):
        _validate_vertical_x_saw_for_milling_spec(spec, tool_type)
        return
    if usage_group != "milling":
        raise ValueError(
            "El fresado requiere una herramienta de tipo Fresa/Freza, "
            "o bien una Sierra Vertical X en modo ranurado horizontal no pasante: "
            f"{_tool_catalog_label(spec)} figura como '{tool_type or 'sin tipo'}'."
        )


def _validate_tool_type_for_drilling_spec(
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    if spec.tool_object_type == "System.Object":
        return

    catalog_entry = tool_catalog.get(spec.tool_id)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar el tipo de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    tool_type = (catalog_entry.get("type") or "").strip()
    if _normalize_tool_usage_group(tool_type) != "drilling":
        raise ValueError(
            "El taladrado requiere una herramienta de tipo Broca: "
            f"{_tool_catalog_label(spec)} figura como '{tool_type or 'sin tipo'}'."
        )


def _validate_tool_sinking_length_for_drilling_spec(
    state: PgmxState,
    spec,
    tool_catalog: dict[str, dict[str, str]],
) -> None:
    if spec.tool_object_type == "System.Object":
        return

    catalog_entry = tool_catalog.get(spec.tool_id)
    if catalog_entry is None:
        raise ValueError(
            "No se pudo validar la seguridad de la herramienta "
            f"{_tool_catalog_label(spec)} porque no existe en '{TOOL_CATALOG_PATH.name}'."
        )

    sinking_length_text = (catalog_entry.get("sinking_length") or "").strip()
    sinking_length = float(sinking_length_text or "0")
    if sinking_length <= 0.0:
        raise ValueError(
            "La herramienta "
            f"{_tool_catalog_label(spec)} no tiene un `sinking_length` valido en '{TOOL_CATALOG_PATH.name}'."
        )

    total_depth = _drilling_total_depth(state, spec)
    if total_depth > sinking_length + 1e-9:
        raise ValueError(
            "La profundidad total del taladro excede el `sinking_length` de la herramienta: "
            f"{_tool_catalog_label(spec)} permite { _compact_number(sinking_length) } mm, "
            f"pero la solicitud requiere { _compact_number(total_depth) } mm."
        )


def _validate_tool_sinking_lengths(
    state: PgmxState,
    line_millings: Sequence[_HydratedLineMillingSpec],
    slot_millings: Sequence[_HydratedSlotMillingSpec],
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
    circle_millings: Sequence[_HydratedCircleMillingSpec],
    squaring_millings: Sequence[_HydratedSquaringMillingSpec],
    drillings: Sequence[_HydratedDrillingSpec],
    drilling_patterns: Sequence[_HydratedDrillingPatternSpec] = (),
) -> None:
    """Aplica la validacion de `sinking_length` a todos los mecanizados del request."""

    tool_catalog = _load_tool_catalog()
    for spec in line_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in slot_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in polyline_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in circle_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in squaring_millings:
        _validate_tool_type_for_milling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_spec(state, spec, tool_catalog)
    for spec in drillings:
        _validate_tool_type_for_drilling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_drilling_spec(state, spec, tool_catalog)
    for spec in drilling_patterns:
        _validate_tool_type_for_drilling_spec(spec, tool_catalog)
        _validate_tool_sinking_length_for_drilling_spec(state, spec, tool_catalog)


def _toolpath_cut_z(state: PgmxState, spec) -> float:
    # Regla validada en Maestro:
    # - no pasante: `cut_z = espesor - target_depth`
    # - pasante: `cut_z = -extra_depth`
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if depth_spec.is_through:
        return -depth_spec.extra_depth
    return state.depth - _feature_depth_value(state, spec)


def _feature_bottom_condition_type(spec) -> str:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return "a:ThroughMillingBottom" if depth_spec.is_through else "a:GeneralMillingBottom"


def _operation_overcut_length(spec) -> float:
    depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    return depth_spec.extra_depth if depth_spec.is_through else 0.0


def _uses_feature_depth_expressions(spec) -> bool:
    return _normalize_milling_depth_spec(spec.depth_spec).is_through


def _qname(namespace: str, local_name: str) -> str:
    return f"{{{namespace}}}{local_name}"


def _append_node(
    parent: ET.Element,
    namespace: str,
    local_name: str,
    text: Optional[str] = None,
    attrib: Optional[dict[str, str]] = None,
) -> ET.Element:
    node = ET.SubElement(parent, _qname(namespace, local_name), attrib or {})
    if text is not None:
        node.text = text
    return node


def _append_key(parent: ET.Element, key_id: str, object_type: str) -> ET.Element:
    key = _append_node(parent, UTILITY_NS, "Key")
    _append_node(key, UTILITY_NS, "ID", key_id)
    _append_node(key, UTILITY_NS, "ObjectType", object_type)
    return key


def _append_reference_key(parent: ET.Element, key_id: str, object_type: str) -> ET.Element:
    key = _append_node(parent, UTILITY_NS, "ReferenceKey")
    _append_node(key, UTILITY_NS, "ID", key_id)
    _append_node(key, UTILITY_NS, "ObjectType", object_type)
    return key


def _append_object_ref(
    parent: ET.Element,
    namespace: str,
    local_name: str,
    ref_id: str,
    object_type: str,
    *,
    include_name: bool = False,
    name_text: str = "",
) -> ET.Element:
    ref = _append_node(parent, namespace, local_name)
    _append_node(ref, UTILITY_NS, "ID", ref_id)
    _append_node(ref, UTILITY_NS, "ObjectType", object_type)
    if include_name:
        _append_node(ref, UTILITY_NS, "Name", name_text)
    return ref


def _append_blank_name(parent: ET.Element) -> ET.Element:
    return _append_node(parent, UTILITY_NS, "Name", "")


def _build_line_description(start_x: float, start_y: float, end_x: float, end_y: float) -> str:
    return _build_maestro_line_serialization((start_x, start_y, 0.0), (end_x, end_y, 0.0))


def _build_open_polyline_descriptions(points: Sequence[tuple[float, float]]) -> tuple[str, ...]:
    normalized_points = _normalize_polyline_points(points)
    return tuple(
        _build_line_description(start_point[0], start_point[1], end_point[0], end_point[1])
        for start_point, end_point in zip(normalized_points, normalized_points[1:])
    )


def _build_open_polyline_geometry_profile(
    points: Sequence[tuple[float, float]],
    *,
    z_value: float = 0.0,
) -> GeometryProfileSpec:
    """Construye una polilinea abierta plana como `GeometryProfileSpec`."""

    normalized_points = _normalize_polyline_points(points)
    return build_composite_geometry_profile(
        tuple(
            _line_primitive_at_plane(start_point, end_point, z_value=z_value)
            for start_point, end_point in zip(normalized_points, normalized_points[1:])
        )
    )


def _build_closed_polyline_geometry_profile(
    points: Sequence[tuple[float, float]],
    *,
    z_value: float = 0.0,
) -> GeometryProfileSpec:
    """Construye una polilinea cerrada plana como `GeometryProfileSpec`."""

    normalized_points = tuple((float(point[0]), float(point[1])) for point in points)
    if len(normalized_points) < 4:
        raise ValueError("Un contorno cerrado necesita al menos 4 puntos incluyendo el cierre.")
    if not _points_close_2d(normalized_points[0], normalized_points[-1]):
        raise ValueError("La polilinea cerrada debe terminar en el mismo punto en el que empieza.")
    return build_composite_geometry_profile(
        tuple(
            _line_primitive_at_plane(start_point, end_point, z_value=z_value)
            for start_point, end_point in zip(normalized_points, normalized_points[1:])
        )
    )


def _build_squaring_outline_points(
    length: float,
    width: float,
    *,
    start_edge: str,
    winding: str,
) -> tuple[tuple[float, float], ...]:
    length_value = float(length)
    width_value = float(width)
    if length_value <= 1e-9 or width_value <= 1e-9:
        raise ValueError("El escuadrado necesita una pieza con largo y ancho mayores que cero.")

    bottom_left = (0.0, 0.0)
    bottom_right = (length_value, 0.0)
    top_right = (length_value, width_value)
    top_left = (0.0, width_value)
    mid_bottom = (length_value / 2.0, 0.0)
    mid_right = (length_value, width_value / 2.0)
    mid_top = (length_value / 2.0, width_value)
    mid_left = (0.0, width_value / 2.0)

    normalized_start_edge = _normalize_squaring_start_edge(start_edge)
    normalized_winding = _normalize_geometry_winding(winding)
    if normalized_winding == "CounterClockwise":
        mapping = {
            "Bottom": (mid_bottom, bottom_right, top_right, top_left, bottom_left, mid_bottom),
            "Right": (mid_right, top_right, top_left, bottom_left, bottom_right, mid_right),
            "Top": (mid_top, top_left, bottom_left, bottom_right, top_right, mid_top),
            "Left": (mid_left, bottom_left, bottom_right, top_right, top_left, mid_left),
        }
    else:
        mapping = {
            "Bottom": (mid_bottom, bottom_left, top_left, top_right, bottom_right, mid_bottom),
            "Right": (mid_right, bottom_right, bottom_left, top_left, top_right, mid_right),
            "Top": (mid_top, top_right, bottom_right, bottom_left, top_left, mid_top),
            "Left": (mid_left, top_left, top_right, bottom_right, bottom_left, mid_left),
        }
    return mapping[normalized_start_edge]


def _build_squaring_geometry_profile(
    state: PgmxState,
    spec: _HydratedSquaringMillingSpec,
    *,
    z_value: float = 0.0,
) -> GeometryProfileSpec:
    points = _build_squaring_outline_points(
        state.length,
        state.width,
        start_edge=spec.start_edge,
        winding=spec.winding,
    )
    length_value = float(state.length)
    width_value = float(state.width)
    target_z = float(z_value)
    edge_length = length_value if spec.start_edge in {"Bottom", "Top"} else width_value

    parameterized_edge_map: dict[tuple[str, str], tuple[tuple[float, float, float], tuple[float, float, float]]] = {
        ("CounterClockwise", "Bottom"): ((0.0, 0.0, target_z), (1.0, 0.0, 0.0)),
        ("CounterClockwise", "Right"): ((length_value, 0.0, target_z), (0.0, 1.0, 0.0)),
        ("CounterClockwise", "Top"): ((length_value, width_value, target_z), (-1.0, 0.0, 0.0)),
        ("CounterClockwise", "Left"): ((0.0, width_value, target_z), (0.0, -1.0, 0.0)),
        ("Clockwise", "Bottom"): ((length_value, 0.0, target_z), (-1.0, 0.0, 0.0)),
        ("Clockwise", "Right"): ((length_value, width_value, target_z), (0.0, -1.0, 0.0)),
        ("Clockwise", "Top"): ((0.0, width_value, target_z), (1.0, 0.0, 0.0)),
        ("Clockwise", "Left"): ((0.0, 0.0, target_z), (0.0, 1.0, 0.0)),
    }
    edge_origin, edge_direction = parameterized_edge_map[(spec.winding, spec.start_edge)]
    midpoint_parameter = edge_length / 2.0

    primitives = [
        _build_parameterized_line_geometry_primitive(
            edge_origin,
            edge_direction,
            midpoint_parameter,
            edge_length,
        ),
        build_line_geometry_primitive(points[1][0], points[1][1], points[2][0], points[2][1], start_z=target_z, end_z=target_z),
        build_line_geometry_primitive(points[2][0], points[2][1], points[3][0], points[3][1], start_z=target_z, end_z=target_z),
        build_line_geometry_primitive(points[3][0], points[3][1], points[4][0], points[4][1], start_z=target_z, end_z=target_z),
        _build_parameterized_line_geometry_primitive(
            edge_origin,
            edge_direction,
            0.0,
            midpoint_parameter,
        ),
    ]
    return build_composite_geometry_profile(tuple(primitives))


def _build_toolpath_description(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    return _build_maestro_line_serialization(start_point, end_point)


def _format_maestro_number(value: float) -> str:
    number = float(value)
    if number == 0.0:
        return "-0" if math.copysign(1.0, number) < 0.0 else "0"
    if math.isclose(number, 0.0, abs_tol=1e-15):
        return "0"
    if number.is_integer():
        return str(int(number))
    return format(number, ".17g")


def _format_maestro_orientation_number(value: float) -> str:
    number = float(value)
    if number == 0.0:
        return "-0" if math.copysign(1.0, number) < 0.0 else "0"
    if number.is_integer():
        return str(int(number))
    text = format(number, ".17g")
    if "e" not in text and "E" not in text:
        return text
    mantissa, exponent = text.lower().split("e", 1)
    sign = exponent[:1]
    digits = exponent[1:].rjust(3, "0")
    return f"{mantissa}e{sign}{digits}"


def _normalize_curve_serialization_text(text: str) -> str:
    raw_text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = raw_text.split("\n")

    while lines and lines[0] == "":
        lines.pop(0)

    trailing_newline = raw_text.endswith("\n")
    while lines and lines[-1] == "":
        lines.pop()
        trailing_newline = True

    normalized = "\n".join(lines)
    if trailing_newline and normalized:
        return f"{normalized}\n"
    return normalized


def _build_parameterized_maestro_line_serialization(
    *,
    parameter_start: float,
    parameter_end: float,
    origin_point: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> str:
    return (
        f"8 {_format_maestro_number(parameter_start)} {_format_maestro_number(parameter_end)}\n"
        f"1 {_format_maestro_number(origin_point[0])} {_format_maestro_number(origin_point[1])} {_format_maestro_number(origin_point[2])} "
        f"{_format_maestro_orientation_number(direction[0])} {_format_maestro_orientation_number(direction[1])} {_format_maestro_orientation_number(direction[2])} \n"
    )


def _build_maestro_line_serialization(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> str:
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    dz = end_point[2] - start_point[2]
    length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
    if length <= 1e-9:
        raise ValueError("No se puede serializar un segmento de longitud cero.")

    return _build_parameterized_maestro_line_serialization(
        parameter_start=0.0,
        parameter_end=length,
        origin_point=start_point,
        direction=(dx / length, dy / length, dz / length),
    )


def _line_right_normal(start_x: float, start_y: float, end_x: float, end_y: float) -> tuple[float, float]:
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    length = math.hypot(delta_x, delta_y)
    if length <= 1e-9:
        raise ValueError("No se puede sintetizar un fresado lineal con longitud cero.")
    return (delta_y / length, -delta_x / length)


def _line_unit_direction(start_x: float, start_y: float, end_x: float, end_y: float) -> tuple[float, float]:
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    length = math.hypot(delta_x, delta_y)
    if length <= 1e-9:
        raise ValueError("No se puede sintetizar un fresado lineal con longitud cero.")
    return (delta_x / length, delta_y / length)


def _resolve_toolpath_direction(
    toolpath_start: tuple[float, float],
    toolpath_end: tuple[float, float],
    direction: Optional[tuple[float, float]] = None,
) -> tuple[float, float]:
    if direction is not None:
        return direction
    return _line_unit_direction(
        toolpath_start[0],
        toolpath_start[1],
        toolpath_end[0],
        toolpath_end[1],
    )


def _preferred_side_for_arc(side_of_feature: str, arc_side: str) -> str:
    normalized_side = _normalize_side_of_feature(side_of_feature)
    if normalized_side != "Center":
        return normalized_side
    normalized_arc_side = _normalize_approach_arc_side(arc_side)
    if normalized_arc_side in {"Left", "Right"}:
        return normalized_arc_side
    return "Right"


def _side_normal_for_direction(
    direction_x: float,
    direction_y: float,
    side_of_feature: str,
    arc_side: str,
) -> tuple[tuple[float, float], float]:
    right_normal = (direction_y, -direction_x)
    left_normal = (-right_normal[0], -right_normal[1])
    preferred_side = _preferred_side_for_arc(side_of_feature, arc_side)
    if preferred_side == "Left":
        return left_normal, 1.0
    return right_normal, -1.0


def _build_vertical_toolpath_curve(
    x_value: float,
    y_value: float,
    start_z: float,
    end_z: float,
) -> _CurveSpec:
    # Maestro mantiene un toolpath vertical en Approach/Lift aunque la estrategia este deshabilitada.
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (x_value, y_value, start_z),
            (x_value, y_value, end_z),
        )
    )


def _quote_arc_radius(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * max(radius_multiplier - 1.0, 0.0)


def _linear_lead_distance(tool_width: float, radius_multiplier: float) -> float:
    return (tool_width / 2.0) * radius_multiplier


def _dominant_component_sign_2d(vector: tuple[float, float]) -> float:
    x_value, y_value = vector
    if abs(x_value) >= abs(y_value):
        if not math.isclose(x_value, 0.0, abs_tol=1e-15):
            return 1.0 if x_value > 0.0 else -1.0
    if not math.isclose(y_value, 0.0, abs_tol=1e-15):
        return 1.0 if y_value > 0.0 else -1.0
    return 1.0


def _build_oriented_maestro_arc_basis(
    direction: tuple[float, float],
    side_normal: tuple[float, float],
    normal_z: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    # Maestro serializa estos arcos con una base 3D orientada y pequeños epsilon
    # en algunos componentes. Mantener esta estructura ayuda a que el XML sintetizado
    # se parezca mas al guardado manualmente desde Maestro.
    epsilon = math.ulp(0.5)
    direction_x, direction_y = direction
    side_x, side_y = side_normal
    u_vector = (
        0.0 if math.isclose(side_x, 0.0, abs_tol=1e-15) else (normal_z * side_x),
        normal_z * side_y,
        epsilon * normal_z,
    )
    v_vector = (
        -normal_z * direction_x,
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-normal_z * direction_y),
        0.0,
    )
    normal_vector = (
        (-0.0 if normal_z > 0.0 else 0.0)
        if math.isclose(direction_y, 0.0, abs_tol=1e-15)
        else (epsilon * direction_y),
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-epsilon * direction_x),
        normal_z,
    )
    return normal_vector, u_vector, v_vector


def _build_quote_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. bajada vertical en el punto inicial del acercamiento
    # 2. cuarto de arco en la cota de corte hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = entry_point[0] + (side_normal[0] * arc_radius)
    center_y = entry_point[1] + (side_normal[1] * arc_radius)
    plunge_x = center_x - (direction_x * arc_radius)
    plunge_y = center_y - (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = (1.5 * math.pi) if normal_z < 0.0 else (0.5 * math.pi)
    end_angle = (2.0 * math.pi) if normal_z < 0.0 else math.pi

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, cut_z),
            ),
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
        ]
    )


def _build_down_arc_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Down:
    # 1. bajada vertical hasta `cut_z + radio`
    # 2. cuarto de arco en un plano vertical hasta el punto de entrada del toolpath
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(entry_point[0], entry_point[1], clearance_z, cut_z)

    direction_x, direction_y = direction
    right_normal_x = direction_y
    right_normal_y = -direction_x
    pre_entry_z = cut_z + arc_radius
    plunge_x = entry_point[0] - (direction_x * arc_radius)
    plunge_y = entry_point[1] - (direction_y * arc_radius)

    return _composite_curve_spec(
        [
            _build_toolpath_description(
                (plunge_x, plunge_y, clearance_z),
                (plunge_x, plunge_y, pre_entry_z),
            ),
            _build_oriented_maestro_arc_serialization(
                1.5 * math.pi,
                2.0 * math.pi,
                (entry_point[0], entry_point[1], pre_entry_z),
                (right_normal_x, right_normal_y, 0.0),
                (0.0, 0.0, -1.0),
                (direction_x, direction_y, 0.0),
                arc_radius,
                z_value=pre_entry_z,
            ),
        ]
    )


def _build_down_line_entry_curve(
    *,
    clearance_z: float,
    cut_z: float,
    entry_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Down:
    # una sola bajada oblicua desde un punto previo desplazado
    # en la direccion opuesta al avance del toolpath.
    pre_entry_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    pre_entry_x = entry_point[0] - (direction_x * pre_entry_distance)
    pre_entry_y = entry_point[1] - (direction_y * pre_entry_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (pre_entry_x, pre_entry_y, clearance_z),
            (entry_point[0], entry_point[1], cut_z),
        )
    )


def _build_up_line_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Line + Up:
    # una sola subida oblicua hacia un punto final desplazado
    # sobre la direccion de salida del toolpath.
    post_exit_distance = _linear_lead_distance(tool_width, radius_multiplier)
    direction_x, direction_y = direction
    post_exit_x = exit_point[0] + (direction_x * post_exit_distance)
    post_exit_y = exit_point[1] + (direction_y * post_exit_distance)
    return _trimmed_curve_spec(
        _build_toolpath_description(
            (exit_point[0], exit_point[1], cut_z),
            (post_exit_x, post_exit_y, clearance_z),
        )
    )


def _build_quote_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    side_of_feature: str,
    arc_side: str,
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Quote:
    # 1. cuarto de arco en la cota de corte desde el punto de salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    side_normal, normal_z = _side_normal_for_direction(
        direction_x,
        direction_y,
        side_of_feature,
        arc_side,
    )
    center_x = exit_point[0] + (side_normal[0] * arc_radius)
    center_y = exit_point[1] + (side_normal[1] * arc_radius)
    lift_x = center_x + (direction_x * arc_radius)
    lift_y = center_y + (direction_y * arc_radius)
    normal_vector, u_vector, v_vector = _build_oriented_maestro_arc_basis(
        (direction_x, direction_y),
        side_normal,
        normal_z,
    )
    start_angle = 0.0 if normal_z < 0.0 else math.pi
    end_angle = (0.5 * math.pi) if normal_z < 0.0 else (1.5 * math.pi)

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                start_angle,
                end_angle,
                (center_x, center_y),
                normal_vector,
                u_vector,
                v_vector,
                arc_radius,
                z_value=cut_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, cut_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _build_up_arc_exit_curve(
    *,
    clearance_z: float,
    cut_z: float,
    exit_point: tuple[float, float],
    direction: tuple[float, float],
    tool_width: float,
    radius_multiplier: float,
) -> _CurveSpec:
    # Regla validada en Maestro para Arc + Up:
    # 1. cuarto de arco en un plano vertical desde la salida del toolpath
    # 2. subida vertical en el punto final del alejamiento
    arc_radius = _quote_arc_radius(tool_width, radius_multiplier)
    if arc_radius <= 1e-9:
        return _build_vertical_toolpath_curve(exit_point[0], exit_point[1], cut_z, clearance_z)

    direction_x, direction_y = direction
    plane_normal = (
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else direction_y,
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-direction_x),
    )
    basis_sign = _dominant_component_sign_2d(plane_normal)
    center_z = cut_z + arc_radius
    lift_x = exit_point[0] + (direction_x * arc_radius)
    lift_y = exit_point[1] + (direction_y * arc_radius)
    lift_z = center_z
    tangent_vector = (
        0.0 if math.isclose(direction_x, 0.0, abs_tol=1e-15) else (-basis_sign * direction_x),
        0.0 if math.isclose(direction_y, 0.0, abs_tol=1e-15) else (-basis_sign * direction_y),
        0.0,
    )

    return _composite_curve_spec(
        [
            _build_oriented_maestro_arc_serialization(
                math.pi if basis_sign > 0.0 else 0.0,
                (1.5 * math.pi) if basis_sign > 0.0 else (0.5 * math.pi),
                exit_point,
                (plane_normal[0], plane_normal[1], 0.0),
                (0.0, 0.0, basis_sign),
                tangent_vector,
                arc_radius,
                z_value=center_z,
            ),
            _build_toolpath_description(
                (lift_x, lift_y, lift_z),
                (lift_x, lift_y, clearance_z),
            ),
        ]
    )


def _offset_factor(side_of_feature: str) -> float:
    normalized = _normalize_side_of_feature(side_of_feature)
    return {
        "Left": -1.0,
        "Center": 0.0,
        "Right": 1.0,
    }[normalized]


def _profile_endpoint_points(profile: GeometryProfileSpec) -> tuple[tuple[float, float], tuple[float, float]]:
    """Devuelve inicio y fin XY del recorrido efectivo."""

    if profile.geometry_type == "GeomCircle":
        if profile.center_point is None or profile.radius is None:
            raise ValueError("El perfil circular necesita centro y radio para exponer sus extremos.")
        start_point = (profile.center_point[0] + profile.radius, profile.center_point[1])
        return start_point, start_point

    if not profile.primitives:
        raise ValueError("El perfil compensado no contiene primitivas.")
    first_primitive = profile.primitives[0]
    last_primitive = profile.primitives[-1]
    return (
        (first_primitive.start_point[0], first_primitive.start_point[1]),
        (last_primitive.end_point[0], last_primitive.end_point[1]),
    )


def _profile_endpoint_directions(
    profile: GeometryProfileSpec,
) -> tuple[Optional[tuple[float, float]], Optional[tuple[float, float]]]:
    """Devuelve tangentes XY de entrada y salida del perfil compensado."""

    if profile.geometry_type == "GeomCircle":
        winding = _normalize_geometry_winding(profile.winding)
        tangent = (0.0, 1.0 if winding == "CounterClockwise" else -1.0)
        return tangent, tangent

    if not profile.primitives:
        return None, None
    return _primitive_start_tangent_2d(profile.primitives[0]), _primitive_end_tangent_2d(profile.primitives[-1])


def _profile_entry_exit_context(
    profile: GeometryProfileSpec,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Resuelve punto y tangente de entrada/salida para cualquier trayectoria compensada."""

    start_point, end_point = _profile_endpoint_points(profile)
    start_direction, end_direction = _profile_endpoint_directions(profile)

    if start_direction is None:
        start_direction = _resolve_toolpath_direction(start_point, end_point)
    if end_direction is None:
        end_direction = _resolve_toolpath_direction(start_point, end_point)

    return start_point, end_point, start_direction, end_direction


def _profile_endpoint_points_3d(
    profile: GeometryProfileSpec,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if profile.geometry_type == "GeomCircle":
        if profile.center_point is None or profile.radius is None:
            raise ValueError("El perfil circular necesita centro y radio para exponer sus extremos 3D.")
        start_point = (
            profile.center_point[0] + profile.radius,
            profile.center_point[1],
            profile.center_point[2],
        )
        return start_point, start_point
    if not profile.primitives:
        raise ValueError("El perfil compensado no contiene primitivas.")
    return profile.primitives[0].start_point, profile.primitives[-1].end_point


def _strategy_is_multilevel(strategy: Optional[MillingStrategySpec]) -> bool:
    normalized_strategy = _normalize_milling_strategy_spec(strategy)
    if normalized_strategy is None:
        return False
    if isinstance(normalized_strategy, HelicalMillingStrategySpec):
        return True
    if not normalized_strategy.allow_multiple_passes:
        return False
    return (
        normalized_strategy.axial_cutting_depth > 0.0
        or normalized_strategy.axial_finish_cutting_depth > 0.0
    )


def _resolve_unidirectional_connection_mode(
    strategy: UnidirectionalMillingStrategySpec,
    *,
    is_closed_profile: bool,
) -> str:
    if strategy.connection_mode != "Automatic":
        return strategy.connection_mode
    return "InPiece" if is_closed_profile else "SafetyHeight"


def _serialize_unidirectional_connection_mode(connection_mode: str) -> str:
    normalized_connection_mode = _normalize_strategy_connection_mode(connection_mode)
    return {
        "Automatic": "LiftShiftPlunge",
        "SafetyHeight": "LiftShiftPlunge",
        "InPiece": "Straghtline",
    }[normalized_connection_mode]


def _strategy_pass_levels(
    state: PgmxState,
    spec,
    strategy: UnidirectionalMillingStrategySpec | BidirectionalMillingStrategySpec,
) -> tuple[float, ...]:
    final_level = _toolpath_cut_z(state, spec)
    if not strategy.allow_multiple_passes:
        return (final_level,)

    top_level = float(state.depth)
    rough_step = float(strategy.axial_cutting_depth)
    finish_step = float(strategy.axial_finish_cutting_depth)
    finish_start = final_level + finish_step if finish_step > 0.0 else None
    levels: list[float] = []

    if rough_step > 0.0:
        current_level = top_level - rough_step
        rough_stop_level = finish_start if finish_start is not None else final_level
        while current_level > rough_stop_level + 1e-9:
            levels.append(current_level)
            current_level -= rough_step

    if finish_start is not None and finish_start > final_level + 1e-9:
        if not levels or not math.isclose(levels[-1], finish_start, abs_tol=1e-9):
            levels.append(finish_start)

    if not levels or not math.isclose(levels[-1], final_level, abs_tol=1e-9):
        levels.append(final_level)
    return tuple(levels)


def _helical_rough_end_levels(
    state: PgmxState,
    spec,
    strategy: HelicalMillingStrategySpec,
) -> tuple[float, ...]:
    final_level = _toolpath_cut_z(state, spec)
    top_level = float(state.depth)
    rough_step = float(strategy.axial_cutting_depth)
    finish_step = float(strategy.axial_finish_cutting_depth)
    helical_end_level = final_level
    if strategy.allows_finish_cutting and finish_step > 0.0:
        helical_end_level = final_level + finish_step

    levels: list[float] = []
    if rough_step > 0.0:
        current_level = top_level - rough_step
        while current_level > helical_end_level + 1e-9:
            levels.append(current_level)
            current_level -= rough_step

    if not levels or not math.isclose(levels[-1], helical_end_level, abs_tol=1e-9):
        levels.append(helical_end_level)
    return tuple(levels)


def _line_primitive_3d(
    start_point: tuple[float, float, float],
    end_point: tuple[float, float, float],
) -> GeometryPrimitiveSpec:
    return build_line_geometry_primitive(
        start_point[0],
        start_point[1],
        end_point[0],
        end_point[1],
        start_z=start_point[2],
        end_z=end_point[2],
    )


def _vertical_transition_primitive(
    xy_point: tuple[float, float],
    start_z: float,
    end_z: float,
) -> GeometryPrimitiveSpec:
    return _line_primitive_3d(
        (xy_point[0], xy_point[1], start_z),
        (xy_point[0], xy_point[1], end_z),
    )


def _primitive_at_z(primitive: GeometryPrimitiveSpec, z_value: float) -> GeometryPrimitiveSpec:
    if primitive.primitive_type == "Line":
        return GeometryPrimitiveSpec(
            primitive_type="Line",
            start_point=(primitive.start_point[0], primitive.start_point[1], z_value),
            end_point=(primitive.end_point[0], primitive.end_point[1], z_value),
            parameter_start=primitive.parameter_start,
            parameter_end=primitive.parameter_end,
            direction_hint=primitive.direction_hint,
        )
    if primitive.primitive_type == "Arc":
        if (
            primitive.center_point is None
            or primitive.radius is None
            or primitive.normal_vector is None
            or primitive.u_vector is None
            or primitive.v_vector is None
        ):
            raise ValueError("La primitiva de arco necesita centro, radio y base orientada.")
        return GeometryPrimitiveSpec(
            primitive_type="Arc",
            start_point=(primitive.start_point[0], primitive.start_point[1], z_value),
            end_point=(primitive.end_point[0], primitive.end_point[1], z_value),
            parameter_start=primitive.parameter_start,
            parameter_end=primitive.parameter_end,
            center_point=(primitive.center_point[0], primitive.center_point[1], z_value),
            radius=primitive.radius,
            normal_vector=primitive.normal_vector,
            u_vector=primitive.u_vector,
            v_vector=primitive.v_vector,
        )
    raise ValueError(f"Tipo de primitiva no soportado para reasignar z: {primitive.primitive_type}")


def _profile_at_z(profile: GeometryProfileSpec, z_value: float) -> GeometryProfileSpec:
    if profile.geometry_type == "GeomCircle":
        if profile.center_point is None or profile.radius is None:
            raise ValueError("El perfil circular necesita centro y radio para reasignar z.")
        return build_circle_geometry_profile(
            profile.center_point[0],
            profile.center_point[1],
            profile.radius,
            z_value=z_value,
            winding=profile.winding,
        )
    if not profile.primitives:
        raise ValueError("El perfil necesita primitivas para reasignar z.")
    return _build_profile_geometry_spec(
        geometry_type=profile.geometry_type,
        primitives=tuple(_primitive_at_z(primitive, z_value) for primitive in profile.primitives),
    )


def _reverse_geometry_primitive(primitive: GeometryPrimitiveSpec) -> GeometryPrimitiveSpec:
    if primitive.primitive_type == "Line":
        return GeometryPrimitiveSpec(
            primitive_type="Line",
            start_point=primitive.end_point,
            end_point=primitive.start_point,
            parameter_start=primitive.parameter_start,
            parameter_end=primitive.parameter_end,
            direction_hint=(
                None
                if primitive.direction_hint is None
                else (
                    -primitive.direction_hint[0],
                    -primitive.direction_hint[1],
                    -primitive.direction_hint[2],
                )
            ),
        )
    if primitive.primitive_type == "Arc":
        if primitive.center_point is None:
            raise ValueError("La primitiva de arco necesita centro para invertirse.")
        return build_arc_geometry_primitive(
            primitive.end_point[0],
            primitive.end_point[1],
            primitive.start_point[0],
            primitive.start_point[1],
            primitive.center_point[0],
            primitive.center_point[1],
            z_value=primitive.center_point[2],
            winding="Clockwise" if _primitive_winding(primitive) == "CounterClockwise" else "CounterClockwise",
        )
    raise ValueError(f"Tipo de primitiva no soportado para invertir: {primitive.primitive_type}")


def _reverse_profile_geometry(profile: GeometryProfileSpec) -> GeometryProfileSpec:
    if profile.geometry_type == "GeomCircle":
        if profile.center_point is None or profile.radius is None:
            raise ValueError("El perfil circular necesita centro y radio para invertirse.")
        reversed_winding = "Clockwise" if _normalize_geometry_winding(profile.winding) == "CounterClockwise" else "CounterClockwise"
        return build_circle_geometry_profile(
            profile.center_point[0],
            profile.center_point[1],
            profile.radius,
            z_value=profile.center_point[2],
            winding=reversed_winding,
        )
    return _build_profile_geometry_spec(
        geometry_type=profile.geometry_type,
        primitives=tuple(
            _reverse_geometry_primitive(primitive)
            for primitive in reversed(profile.primitives)
        ),
    )


def _build_unidirectional_line_strategy_profile(
    state: PgmxState,
    spec,
    base_profile: GeometryProfileSpec,
    strategy: UnidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(state, spec, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    start_xy, end_xy = _profile_endpoint_points(base_profile)
    is_closed_profile = False
    connection_mode = _resolve_unidirectional_connection_mode(strategy, is_closed_profile=is_closed_profile)
    clearance_level = state.depth + spec.security_plane
    in_piece_lift = spec.security_plane / 2.0
    primitives: list[GeometryPrimitiveSpec] = []

    for index, current_level in enumerate(pass_levels):
        primitives.append(
            _line_primitive_3d(
                (start_xy[0], start_xy[1], current_level),
                (end_xy[0], end_xy[1], current_level),
            )
        )
        if index == len(pass_levels) - 1:
            continue
        reconnect_level = (
            clearance_level
            if connection_mode == "SafetyHeight"
            else current_level + in_piece_lift
        )
        primitives.append(_vertical_transition_primitive(end_xy, current_level, reconnect_level))
        primitives.append(
            _line_primitive_3d(
                (end_xy[0], end_xy[1], reconnect_level),
                (start_xy[0], start_xy[1], reconnect_level),
            )
        )
        primitives.append(_vertical_transition_primitive(start_xy, reconnect_level, pass_levels[index + 1]))

    return build_composite_geometry_profile(tuple(primitives))


def _build_bidirectional_line_strategy_profile(
    state: PgmxState,
    spec,
    base_profile: GeometryProfileSpec,
    strategy: BidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(state, spec, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    start_xy, end_xy = _profile_endpoint_points(base_profile)
    primitives: list[GeometryPrimitiveSpec] = []
    current_forward = True

    for index, current_level in enumerate(pass_levels):
        current_start = start_xy if current_forward else end_xy
        current_end = end_xy if current_forward else start_xy
        primitives.append(
            _line_primitive_3d(
                (current_start[0], current_start[1], current_level),
                (current_end[0], current_end[1], current_level),
            )
        )
        if index == len(pass_levels) - 1:
            continue
        primitives.append(
            _vertical_transition_primitive(
                current_end,
                current_level,
                pass_levels[index + 1],
            )
        )
        current_forward = not current_forward

    return build_composite_geometry_profile(tuple(primitives))


def _build_unidirectional_open_profile_strategy_toolpath(
    state: PgmxState,
    spec,
    base_profile: GeometryProfileSpec,
    strategy: UnidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(state, spec, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    connection_mode = _resolve_unidirectional_connection_mode(strategy, is_closed_profile=False)
    clearance_level = state.depth + spec.security_plane
    in_piece_lift = spec.security_plane / 2.0
    primitives: list[GeometryPrimitiveSpec] = []

    for index, current_level in enumerate(pass_levels):
        forward_profile = _profile_at_z(base_profile, current_level)
        primitives.extend(forward_profile.primitives)
        if index == len(pass_levels) - 1:
            continue

        forward_end = forward_profile.primitives[-1].end_point
        reverse_reconnect_level = (
            clearance_level
            if connection_mode == "SafetyHeight"
            else current_level + in_piece_lift
        )
        primitives.append(
            _vertical_transition_primitive(
                (forward_end[0], forward_end[1]),
                current_level,
                reverse_reconnect_level,
            )
        )

        reverse_profile = _reverse_profile_geometry(_profile_at_z(base_profile, reverse_reconnect_level))
        primitives.extend(reverse_profile.primitives)
        reverse_end = reverse_profile.primitives[-1].end_point
        primitives.append(
            _vertical_transition_primitive(
                (reverse_end[0], reverse_end[1]),
                reverse_reconnect_level,
                pass_levels[index + 1],
            )
        )

    return build_composite_geometry_profile(tuple(primitives))


def _build_bidirectional_open_profile_strategy_toolpath(
    state: PgmxState,
    spec,
    base_profile: GeometryProfileSpec,
    strategy: BidirectionalMillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(state, spec, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    primitives: list[GeometryPrimitiveSpec] = []
    current_forward = True

    for index, current_level in enumerate(pass_levels):
        current_profile = _profile_at_z(base_profile, current_level)
        if not current_forward:
            current_profile = _reverse_profile_geometry(current_profile)
        primitives.extend(current_profile.primitives)
        if index == len(pass_levels) - 1:
            continue

        current_end = current_profile.primitives[-1].end_point
        primitives.append(
            _vertical_transition_primitive(
                (current_end[0], current_end[1]),
                current_level,
                pass_levels[index + 1],
            )
        )
        current_forward = not current_forward

    return build_composite_geometry_profile(tuple(primitives))


def _build_closed_profile_strategy_toolpath(
    state: PgmxState,
    spec,
    base_profile: GeometryProfileSpec,
    strategy: MillingStrategySpec,
) -> GeometryProfileSpec:
    pass_levels = _strategy_pass_levels(state, spec, strategy)
    if len(pass_levels) <= 1:
        return _profile_at_z(base_profile, pass_levels[0])

    primitives: list[GeometryPrimitiveSpec] = []
    for index, current_level in enumerate(pass_levels):
        loop_profile = _profile_at_z(base_profile, current_level)
        if isinstance(strategy, BidirectionalMillingStrategySpec) and index % 2 == 1:
            loop_profile = _reverse_profile_geometry(loop_profile)
        primitives.extend(loop_profile.primitives)
        if index == len(pass_levels) - 1:
            continue
        loop_end = loop_profile.primitives[-1].end_point
        primitives.append(
            _vertical_transition_primitive(
                (loop_end[0], loop_end[1]),
                current_level,
                pass_levels[index + 1],
            )
        )
    return build_composite_geometry_profile(tuple(primitives))


def _build_helical_arc_primitive(
    flat_arc: GeometryPrimitiveSpec,
    *,
    start_z: float,
    end_z: float,
) -> GeometryPrimitiveSpec:
    if (
        flat_arc.primitive_type != "Arc"
        or flat_arc.center_point is None
        or flat_arc.radius is None
    ):
        raise ValueError("La estrategia helicoidal sobre circulo requiere primitivas de arco planas.")

    tangent_xy = _primitive_start_tangent_2d(flat_arc)
    if tangent_xy is None:
        raise ValueError("No se pudo resolver la tangente de arranque del arco helicoidal.")

    center_x = flat_arc.center_point[0]
    center_y = flat_arc.center_point[1]
    center_z = (float(start_z) + float(end_z)) / 2.0
    radius_3d = math.hypot(float(flat_arc.radius), (float(start_z) - float(end_z)) / 2.0)
    if radius_3d <= 1e-9:
        raise ValueError("El arco helicoidal requiere radio 3D positivo.")

    start_angle = float(flat_arc.parameter_start)
    start_point = (flat_arc.start_point[0], flat_arc.start_point[1], float(start_z))
    end_point = (flat_arc.end_point[0], flat_arc.end_point[1], float(end_z))
    radial_start = (
        (start_point[0] - center_x) / radius_3d,
        (start_point[1] - center_y) / radius_3d,
        (start_point[2] - center_z) / radius_3d,
    )
    tangent_start = (tangent_xy[0], tangent_xy[1], 0.0)
    cos_start = math.cos(start_angle)
    sin_start = math.sin(start_angle)
    u_vector = (
        (radial_start[0] * cos_start) - (tangent_start[0] * sin_start),
        (radial_start[1] * cos_start) - (tangent_start[1] * sin_start),
        (radial_start[2] * cos_start) - (tangent_start[2] * sin_start),
    )
    v_vector = (
        (radial_start[0] * sin_start) + (tangent_start[0] * cos_start),
        (radial_start[1] * sin_start) + (tangent_start[1] * cos_start),
        (radial_start[2] * sin_start) + (tangent_start[2] * cos_start),
    )
    normal_vector = (
        (u_vector[1] * v_vector[2]) - (u_vector[2] * v_vector[1]),
        (u_vector[2] * v_vector[0]) - (u_vector[0] * v_vector[2]),
        (u_vector[0] * v_vector[1]) - (u_vector[1] * v_vector[0]),
    )
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=flat_arc.parameter_start,
        parameter_end=flat_arc.parameter_end,
        center_point=(center_x, center_y, center_z),
        radius=radius_3d,
        normal_vector=normal_vector,
        u_vector=u_vector,
        v_vector=v_vector,
    )


def _build_helical_circle_strategy_toolpath(
    state: PgmxState,
    spec,
    base_profile: GeometryProfileSpec,
    strategy: HelicalMillingStrategySpec,
) -> GeometryProfileSpec:
    if (
        base_profile.geometry_type != "GeomCompositeCurve"
        or len(base_profile.primitives) != 2
        or any(primitive.primitive_type != "Arc" for primitive in base_profile.primitives)
    ):
        raise ValueError(
            "La estrategia Helicoidal hoy espera un circulo compensado compuesto por dos semicircunferencias."
        )

    rough_end_levels = _helical_rough_end_levels(state, spec, strategy)
    final_level = _toolpath_cut_z(state, spec)
    current_level = float(state.depth)
    primitives: list[GeometryPrimitiveSpec] = []

    for rough_end_level in rough_end_levels:
        midpoint_level = (current_level + rough_end_level) / 2.0
        primitives.append(
            _build_helical_arc_primitive(
                base_profile.primitives[0],
                start_z=current_level,
                end_z=midpoint_level,
            )
        )
        primitives.append(
            _build_helical_arc_primitive(
                base_profile.primitives[1],
                start_z=midpoint_level,
                end_z=rough_end_level,
            )
        )
        current_level = rough_end_level

    if strategy.allows_finish_cutting:
        loop_end_point = primitives[-1].end_point
        if not math.isclose(current_level, final_level, abs_tol=1e-9):
            primitives.append(
                _vertical_transition_primitive(
                    (loop_end_point[0], loop_end_point[1]),
                    current_level,
                    final_level,
                )
            )
        primitives.extend(_profile_at_z(base_profile, final_level).primitives)

    return build_composite_geometry_profile(tuple(primitives))


def _build_line_toolpath_profile(state: PgmxState, spec: _HydratedLineMillingSpec) -> GeometryProfileSpec:
    """Construye el perfil de trayectoria efectivo para un fresado lineal."""

    cut_z = _toolpath_cut_z(state, spec)
    nominal_profile = build_line_geometry_profile(
        spec.start_x,
        spec.start_y,
        spec.end_x,
        spec.end_y,
        start_z=cut_z,
        end_z=cut_z,
    )
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_line_strategy_profile(state, spec, base_profile, strategy)
    if isinstance(strategy, BidirectionalMillingStrategySpec):
        return _build_bidirectional_line_strategy_profile(state, spec, base_profile, strategy)
    return base_profile


def _offset_line_for_toolpath(spec: _HydratedLineMillingSpec) -> tuple[tuple[float, float], tuple[float, float]]:
    toolpath_profile = build_compensated_toolpath_profile(
        build_line_geometry_profile(spec.start_x, spec.start_y, spec.end_x, spec.end_y),
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
    )
    return _profile_endpoint_points(toolpath_profile)


def _offset_point(point: tuple[float, float], offset_x: float, offset_y: float) -> tuple[float, float]:
    return (point[0] + offset_x, point[1] + offset_y)


def _intersect_lines(
    point_a: tuple[float, float],
    direction_a: tuple[float, float],
    point_b: tuple[float, float],
    direction_b: tuple[float, float],
    tolerance: float = 1e-9,
) -> Optional[tuple[float, float]]:
    denominator = (direction_a[0] * direction_b[1]) - (direction_a[1] * direction_b[0])
    if math.isclose(denominator, 0.0, abs_tol=tolerance):
        return None
    delta_x = point_b[0] - point_a[0]
    delta_y = point_b[1] - point_a[1]
    factor = ((delta_x * direction_b[1]) - (delta_y * direction_b[0])) / denominator
    return (
        point_a[0] + (direction_a[0] * factor),
        point_a[1] + (direction_a[1] * factor),
    )


def _points_close_2d(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    tolerance: float = 1e-9,
) -> bool:
    return math.isclose(point_a[0], point_b[0], abs_tol=tolerance) and math.isclose(
        point_a[1], point_b[1], abs_tol=tolerance
    )


def _cross_2d(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> float:
    return (vector_a[0] * vector_b[1]) - (vector_a[1] * vector_b[0])


def _tool_offset_distance(side_of_feature: str, tool_width: float) -> float:
    """Devuelve el offset lateral firmado del centro de herramienta."""

    tool_width_value = float(tool_width)
    if tool_width_value <= 1e-9:
        raise ValueError("El ancho de herramienta debe ser mayor que cero para compensar la trayectoria.")
    return _offset_factor(side_of_feature) * (tool_width_value / 2.0)


def _primitive_winding(primitive: GeometryPrimitiveSpec) -> str:
    """Obtiene el sentido horario/antihorario de una primitiva de arco."""

    if primitive.normal_vector is None or primitive.normal_vector[2] >= 0.0:
        return "CounterClockwise"
    return "Clockwise"


def _line_primitive_at_plane(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    *,
    z_value: float,
) -> GeometryPrimitiveSpec:
    """Construye una linea plana lista para serializacion Maestro."""

    return build_line_geometry_primitive(
        start_point[0],
        start_point[1],
        end_point[0],
        end_point[1],
        start_z=z_value,
        end_z=z_value,
    )


def _reuse_line_primitive_or_rebuild(
    primitive: GeometryPrimitiveSpec,
    *,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    z_value: float,
) -> GeometryPrimitiveSpec:
    primitive_start = (primitive.start_point[0], primitive.start_point[1])
    primitive_end = (primitive.end_point[0], primitive.end_point[1])
    if _points_close_2d(start_point, primitive_start) and _points_close_2d(end_point, primitive_end):
        return primitive
    return _line_primitive_at_plane(start_point, end_point, z_value=z_value)


def _offset_line_primitive(
    primitive: GeometryPrimitiveSpec,
    *,
    offset_distance: float,
    z_value: Optional[float] = None,
) -> GeometryPrimitiveSpec:
    """Desplaza una linea plana segun `SideOfFeature` sin alterar su direccion."""

    right_x, right_y = _line_right_normal(
        primitive.start_point[0],
        primitive.start_point[1],
        primitive.end_point[0],
        primitive.end_point[1],
    )
    offset_x = right_x * offset_distance
    offset_y = right_y * offset_distance
    target_z = primitive.start_point[2] if z_value is None else float(z_value)
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=(primitive.start_point[0] + offset_x, primitive.start_point[1] + offset_y, target_z),
        end_point=(primitive.end_point[0] + offset_x, primitive.end_point[1] + offset_y, target_z),
        parameter_start=primitive.parameter_start,
        parameter_end=primitive.parameter_end,
    )


def _offset_arc_primitive(
    primitive: GeometryPrimitiveSpec,
    *,
    offset_distance: float,
    z_value: Optional[float] = None,
) -> GeometryPrimitiveSpec:
    """Compensa un arco en XY ajustando su radio segun winding y lado."""

    if (
        primitive.center_point is None
        or primitive.radius is None
        or primitive.u_vector is None
        or primitive.v_vector is None
    ):
        raise ValueError("La primitiva de arco necesita centro, radio y base orientada.")

    winding = _primitive_winding(primitive)
    normal_sign = 1.0 if winding == "CounterClockwise" else -1.0
    compensated_radius = primitive.radius + (offset_distance * normal_sign)
    if compensated_radius <= 1e-9:
        raise ValueError("La compensacion hace no positivo el radio efectivo del arco.")

    center_z = primitive.center_point[2] if z_value is None else float(z_value)
    center_point = (primitive.center_point[0], primitive.center_point[1], center_z)
    start_point = _sample_arc_point(
        center_point,
        primitive.u_vector,
        primitive.v_vector,
        compensated_radius,
        primitive.parameter_start,
    )
    end_point = _sample_arc_point(
        center_point,
        primitive.u_vector,
        primitive.v_vector,
        compensated_radius,
        primitive.parameter_end,
    )
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=primitive.parameter_start,
        parameter_end=primitive.parameter_end,
        center_point=center_point,
        radius=compensated_radius,
        normal_vector=primitive.normal_vector,
        u_vector=primitive.u_vector,
        v_vector=primitive.v_vector,
    )


def _offset_geometry_primitive(
    primitive: GeometryPrimitiveSpec,
    *,
    offset_distance: float,
    z_value: Optional[float] = None,
) -> GeometryPrimitiveSpec:
    """Compensa una primitiva lineal o circular conservando su serializacion base."""

    if primitive.primitive_type == "Line":
        return _offset_line_primitive(primitive, offset_distance=offset_distance, z_value=z_value)
    if primitive.primitive_type == "Arc":
        return _offset_arc_primitive(primitive, offset_distance=offset_distance, z_value=z_value)
    raise ValueError(f"Tipo de primitiva no soportado para compensacion: {primitive.primitive_type}")


def _intersection_or_fallback(
    point_a: tuple[float, float],
    direction_a: tuple[float, float],
    point_b: tuple[float, float],
    direction_b: tuple[float, float],
    *,
    fallback_a: tuple[float, float],
    fallback_b: tuple[float, float],
) -> tuple[float, float]:
    """Resuelve una union interior por interseccion o con un fallback robusto."""

    intersection = _intersect_lines(point_a, direction_a, point_b, direction_b)
    if intersection is not None:
        return intersection
    if _points_close_2d(fallback_a, fallback_b):
        return fallback_a
    return ((fallback_a[0] + fallback_b[0]) / 2.0, (fallback_a[1] + fallback_b[1]) / 2.0)


def _build_corner_join_arc(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    center_point: tuple[float, float, float],
    *,
    side_sign: float,
    z_value: float,
) -> GeometryPrimitiveSpec:
    """Construye el arco tangente observado en Maestro para una esquina exterior."""

    winding = "CounterClockwise" if side_sign > 0.0 else "Clockwise"
    return build_arc_geometry_primitive(
        start_point[0],
        start_point[1],
        end_point[0],
        end_point[1],
        center_point[0],
        center_point[1],
        z_value=z_value,
        winding=winding,
    )


def _build_compensated_line_only_open_profile(
    profile: GeometryProfileSpec,
    *,
    offset_distance: float,
    z_value: Optional[float] = None,
) -> GeometryProfileSpec:
    """Compensa una polilinea abierta de lineas usando la regla validada en Maestro."""

    offset_primitives = tuple(
        _offset_line_primitive(primitive, offset_distance=offset_distance, z_value=z_value)
        for primitive in profile.primitives
    )
    if len(offset_primitives) == 1 or math.isclose(offset_distance, 0.0, abs_tol=1e-9):
        return _build_profile_geometry_spec(
            geometry_type="GeomCompositeCurve",
            primitives=offset_primitives,
        )

    side_sign = 1.0 if offset_distance > 0.0 else -1.0
    cut_z = offset_primitives[0].start_point[2]
    member_primitives: list[GeometryPrimitiveSpec] = []
    current_point = (offset_primitives[0].start_point[0], offset_primitives[0].start_point[1])

    for index, (previous_primitive, next_primitive) in enumerate(zip(offset_primitives, offset_primitives[1:])):
        previous_start = (previous_primitive.start_point[0], previous_primitive.start_point[1])
        previous_end = (previous_primitive.end_point[0], previous_primitive.end_point[1])
        next_start = (next_primitive.start_point[0], next_primitive.start_point[1])
        previous_direction = _primitive_end_tangent_2d(previous_primitive)
        next_direction = _primitive_start_tangent_2d(next_primitive)
        if previous_direction is None or next_direction is None:
            raise ValueError("No se pudo resolver la tangente de una polilinea abierta compensada.")

        turn_cross = _cross_2d(previous_direction, next_direction)
        if math.isclose(turn_cross, 0.0, abs_tol=1e-9):
            if not _points_close_2d(current_point, previous_end):
                member_primitives.append(
                    _reuse_line_primitive_or_rebuild(
                        previous_primitive,
                        start_point=current_point,
                        end_point=previous_end,
                        z_value=cut_z,
                    )
                )
            current_point = next_start
            continue

        is_outer_corner = (side_sign * turn_cross) > 0.0
        if is_outer_corner:
            if not _points_close_2d(current_point, previous_end):
                member_primitives.append(
                    _reuse_line_primitive_or_rebuild(
                        previous_primitive,
                        start_point=current_point,
                        end_point=previous_end,
                        z_value=cut_z,
                    )
                )
            member_primitives.append(
                _build_corner_join_arc(
                    previous_end,
                    next_start,
                    profile.primitives[index].end_point,
                    side_sign=side_sign,
                    z_value=cut_z,
                )
            )
            current_point = next_start
            continue

        intersection = _intersection_or_fallback(
            previous_start,
            previous_direction,
            next_start,
            next_direction,
            fallback_a=previous_end,
            fallback_b=next_start,
        )
        if not _points_close_2d(current_point, intersection):
            member_primitives.append(
                _reuse_line_primitive_or_rebuild(
                    previous_primitive,
                    start_point=current_point,
                    end_point=intersection,
                    z_value=cut_z,
                )
            )
        current_point = intersection

    final_point = (offset_primitives[-1].end_point[0], offset_primitives[-1].end_point[1])
    if not _points_close_2d(current_point, final_point):
        member_primitives.append(
            _reuse_line_primitive_or_rebuild(
                offset_primitives[-1],
                start_point=current_point,
                end_point=final_point,
                z_value=cut_z,
            )
        )
    return _build_profile_geometry_spec(
        geometry_type="GeomCompositeCurve",
        primitives=tuple(member_primitives),
    )


def _build_compensated_line_only_closed_profile(
    profile: GeometryProfileSpec,
    *,
    offset_distance: float,
    z_value: Optional[float] = None,
) -> GeometryProfileSpec:
    """Compensa un contorno cerrado de lineas preservando esquinas vivas o exteriores."""

    offset_primitives = tuple(
        _offset_line_primitive(primitive, offset_distance=offset_distance, z_value=z_value)
        for primitive in profile.primitives
    )
    if math.isclose(offset_distance, 0.0, abs_tol=1e-9):
        return _build_profile_geometry_spec(
            geometry_type="GeomCompositeCurve",
            primitives=offset_primitives,
        )

    side_sign = 1.0 if offset_distance > 0.0 else -1.0
    cut_z = offset_primitives[0].start_point[2]
    transitions: list[dict[str, object]] = []
    primitive_count = len(offset_primitives)

    for index in range(primitive_count):
        previous_primitive = offset_primitives[index]
        next_primitive = offset_primitives[(index + 1) % primitive_count]
        previous_start = (previous_primitive.start_point[0], previous_primitive.start_point[1])
        previous_end = (previous_primitive.end_point[0], previous_primitive.end_point[1])
        next_start = (next_primitive.start_point[0], next_primitive.start_point[1])
        previous_direction = _primitive_end_tangent_2d(previous_primitive)
        next_direction = _primitive_start_tangent_2d(next_primitive)
        if previous_direction is None or next_direction is None:
            raise ValueError("No se pudo resolver la tangente de un contorno cerrado compensado.")

        turn_cross = _cross_2d(previous_direction, next_direction)
        if math.isclose(turn_cross, 0.0, abs_tol=1e-9):
            transitions.append(
                {
                    "kind": "collinear",
                    "point": previous_end if _points_close_2d(previous_end, next_start) else next_start,
                }
            )
            continue

        is_outer_corner = (side_sign * turn_cross) > 0.0
        if is_outer_corner:
            transitions.append(
                {
                    "kind": "outer",
                    "arc": _build_corner_join_arc(
                        previous_end,
                        next_start,
                        profile.primitives[index].end_point,
                        side_sign=side_sign,
                        z_value=cut_z,
                    ),
                }
            )
            continue

        transitions.append(
            {
                "kind": "inner",
                "point": _intersection_or_fallback(
                    previous_start,
                    previous_direction,
                    next_start,
                    next_direction,
                    fallback_a=previous_end,
                    fallback_b=next_start,
                ),
            }
        )

    member_primitives: list[GeometryPrimitiveSpec] = []
    wrap_transition = transitions[-1]
    winding = _normalize_geometry_winding(profile.winding)
    emit_wrap_arc_first = wrap_transition["kind"] == "outer" and winding == "CounterClockwise"
    if emit_wrap_arc_first:
        member_primitives.append(wrap_transition["arc"])  # type: ignore[arg-type]
        current_point = (offset_primitives[0].start_point[0], offset_primitives[0].start_point[1])
        segment_order = list(range(primitive_count))
    elif wrap_transition["kind"] == "outer":
        current_point = (offset_primitives[0].start_point[0], offset_primitives[0].start_point[1])
        segment_order = list(range(primitive_count))
    else:
        current_point = wrap_transition["point"]  # type: ignore[assignment]
        segment_order = list(range(primitive_count))

    for index in segment_order:
        primitive = offset_primitives[index]
        transition = transitions[index]
        if transition["kind"] == "outer":
            segment_end = (primitive.end_point[0], primitive.end_point[1])
        else:
            segment_end = transition["point"]  # type: ignore[assignment]

        if not _points_close_2d(current_point, segment_end):
            member_primitives.append(
                _reuse_line_primitive_or_rebuild(
                    primitive,
                    start_point=current_point,
                    end_point=segment_end,
                    z_value=cut_z,
                )
            )

        if transition["kind"] == "outer":
            is_wrap_transition = index == (primitive_count - 1)
            if not (emit_wrap_arc_first and is_wrap_transition):
                member_primitives.append(transition["arc"])  # type: ignore[arg-type]
                next_primitive = offset_primitives[(index + 1) % primitive_count]
                current_point = (next_primitive.start_point[0], next_primitive.start_point[1])
        else:
            current_point = transition["point"]  # type: ignore[assignment]

    return _build_profile_geometry_spec(
        geometry_type="GeomCompositeCurve",
        primitives=tuple(member_primitives),
    )


def _build_compensated_tangent_composite_profile(
    profile: GeometryProfileSpec,
    *,
    offset_distance: float,
    z_value: Optional[float] = None,
) -> GeometryProfileSpec:
    """Compensa curvas compuestas tangentes, incluyendo esquinas redondeadas."""

    offset_primitives = tuple(
        _offset_geometry_primitive(primitive, offset_distance=offset_distance, z_value=z_value)
        for primitive in profile.primitives
    )
    for previous_primitive, next_primitive in zip(offset_primitives, offset_primitives[1:]):
        if not _points_close_3d(previous_primitive.end_point, next_primitive.start_point, tolerance=1e-5):
            raise ValueError(
                "La compensacion de una curva compuesta con arcos requiere miembros tangentes y conectados."
            )
    if profile.is_closed and not _points_close_3d(
        offset_primitives[-1].end_point,
        offset_primitives[0].start_point,
        tolerance=1e-5,
    ):
        raise ValueError(
            "La compensacion de un contorno cerrado con arcos requiere que el cierre siga siendo tangente."
        )
    return _build_profile_geometry_spec(
        geometry_type="GeomCompositeCurve",
        primitives=offset_primitives,
    )


def _build_compensated_profile_geometry(
    profile: GeometryProfileSpec,
    *,
    side_of_feature: str,
    tool_width: float,
    z_value: Optional[float] = None,
) -> GeometryProfileSpec:
    """Motor comun de compensacion geometrica segun las reglas ya validadas."""

    offset_distance = _tool_offset_distance(side_of_feature, tool_width)

    if profile.geometry_type == "GeomCircle":
        if profile.center_point is None or profile.radius is None:
            raise ValueError("El perfil circular necesita centro y radio.")
        winding = _normalize_geometry_winding(profile.winding)
        normal_sign = 1.0 if winding == "CounterClockwise" else -1.0
        compensated_radius = profile.radius + (offset_distance * normal_sign)
        if compensated_radius <= 1e-9:
            raise ValueError("La compensacion hace no positivo el radio efectivo del circulo.")
        target_z = profile.center_point[2] if z_value is None else float(z_value)
        center_x = profile.center_point[0]
        center_y = profile.center_point[1]
        start_point = (center_x + compensated_radius, center_y)
        opposite_point = (center_x - compensated_radius, center_y)
        return build_composite_geometry_profile(
            (
                build_arc_geometry_primitive(
                    start_point[0],
                    start_point[1],
                    opposite_point[0],
                    opposite_point[1],
                    center_x,
                    center_y,
                    z_value=target_z,
                    winding=winding,
                ),
                build_arc_geometry_primitive(
                    opposite_point[0],
                    opposite_point[1],
                    start_point[0],
                    start_point[1],
                    center_x,
                    center_y,
                    z_value=target_z,
                    winding=winding,
                ),
            )
        )

    if profile.geometry_type == "GeomTrimmedCurve":
        if len(profile.primitives) != 1:
            raise ValueError("Un GeomTrimmedCurve compensado requiere exactamente una primitiva.")
        primitive = _offset_geometry_primitive(profile.primitives[0], offset_distance=offset_distance, z_value=z_value)
        return _build_profile_geometry_spec(
            geometry_type="GeomTrimmedCurve",
            primitives=(primitive,),
        )

    if profile.geometry_type != "GeomCompositeCurve":
        raise ValueError(f"Tipo de geometria no soportado para compensacion: {profile.geometry_type}")

    if not profile.primitives:
        raise ValueError("La curva compuesta necesita primitivas para compensarse.")

    if all(primitive.primitive_type == "Line" for primitive in profile.primitives):
        if profile.is_closed:
            return _build_compensated_line_only_closed_profile(
                profile,
                offset_distance=offset_distance,
                z_value=z_value,
            )
        return _build_compensated_line_only_open_profile(
            profile,
            offset_distance=offset_distance,
            z_value=z_value,
        )

    return _build_compensated_tangent_composite_profile(
        profile,
        offset_distance=offset_distance,
        z_value=z_value,
    )


def _reparameterize_line_primitive_from_end(primitive: GeometryPrimitiveSpec) -> GeometryPrimitiveSpec:
    """Reexpresa una linea con origen en su punto final y rango `[-length, 0]`.

    Maestro tiende a reserializar asi los dos tramos partidos del borde inicial
    en `TrajectoryPath` de escuadrados. La geometria efectiva no cambia; solo
    cambia la parametrizacion textual de la recta.
    """

    if primitive.primitive_type != "Line":
        return primitive
    length = math.dist(primitive.start_point, primitive.end_point)
    if length <= 1e-9:
        return primitive
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=primitive.start_point,
        end_point=primitive.end_point,
        parameter_start=-length,
        parameter_end=-0.0,
        direction_hint=primitive.direction_hint,
    )


def _with_line_direction_hint(
    primitive: GeometryPrimitiveSpec,
    *,
    z_negative_zero: bool = False,
) -> GeometryPrimitiveSpec:
    """Anota signos preferidos para componentes nulas de direccion en lineas."""

    if primitive.primitive_type != "Line":
        return primitive
    dx = primitive.end_point[0] - primitive.start_point[0]
    dy = primitive.end_point[1] - primitive.start_point[1]
    dz = primitive.end_point[2] - primitive.start_point[2]
    length = math.dist(primitive.start_point, primitive.end_point)
    if length <= 1e-9:
        return primitive
    direction_z = -0.0 if z_negative_zero and math.isclose(dz, 0.0, abs_tol=1e-12) else (dz / length)
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=primitive.start_point,
        end_point=primitive.end_point,
        parameter_start=primitive.parameter_start,
        parameter_end=primitive.parameter_end,
        direction_hint=(dx / length, dy / length, direction_z),
    )


def _reparameterize_squaring_toolpath_profile(profile: GeometryProfileSpec) -> GeometryProfileSpec:
    """Alinea parametrizacion y signos de direccion del escuadrado con Maestro."""

    if profile.geometry_type != "GeomCompositeCurve" or len(profile.primitives) < 2:
        return profile
    primitives = list(profile.primitives)
    bbox = profile.bounding_box
    min_y = bbox[1] if bbox is not None else None
    max_vertical_length = max(
        (
            math.dist(primitive.start_point, primitive.end_point)
            for primitive in primitives
            if primitive.primitive_type == "Line"
            and math.isclose(primitive.start_point[0], primitive.end_point[0], abs_tol=1e-6)
        ),
        default=0.0,
    )
    if primitives[0].primitive_type == "Line":
        primitives[0] = _reparameterize_line_primitive_from_end(primitives[0])
        if min_y is not None and math.isclose(primitives[0].start_point[1], min_y, abs_tol=1e-6):
            primitives[0] = _with_line_direction_hint(primitives[0], z_negative_zero=True)
    if primitives[-1].primitive_type == "Line":
        primitives[-1] = _reparameterize_line_primitive_from_end(primitives[-1])
        if min_y is not None and math.isclose(primitives[-1].start_point[1], min_y, abs_tol=1e-6):
            primitives[-1] = _with_line_direction_hint(primitives[-1], z_negative_zero=True)
    if max_vertical_length > 0.0:
        for index, primitive in enumerate(primitives):
            if primitive.primitive_type != "Line":
                continue
            dx = primitive.end_point[0] - primitive.start_point[0]
            dy = primitive.end_point[1] - primitive.start_point[1]
            length = math.dist(primitive.start_point, primitive.end_point)
            if (
                math.isclose(dx, 0.0, abs_tol=1e-6)
                and dy < 0.0
                and math.isclose(length, max_vertical_length, abs_tol=1e-6)
            ):
                primitives[index] = _with_line_direction_hint(primitive, z_negative_zero=True)
    return build_composite_geometry_profile(tuple(primitives))


def _normalize_positive_angle(angle: float) -> float:
    normalized = math.fmod(angle, 2.0 * math.pi)
    if normalized < 0.0:
        normalized += 2.0 * math.pi
    if math.isclose(normalized, 2.0 * math.pi, abs_tol=1e-12):
        return 0.0
    return normalized


def _point_to_maestro_basis_angle(
    center_point: tuple[float, float],
    point: tuple[float, float],
    normal_z: float,
) -> float:
    relative_x = point[0] - center_point[0]
    relative_y = point[1] - center_point[1]
    return _normalize_positive_angle(math.atan2(relative_y * normal_z, relative_x))


def _unwrap_maestro_arc_end_angle(start_angle: float, end_angle: float) -> float:
    """Desenvuelve el parametro final para preservar el avance real del arco."""

    if math.isclose(start_angle, end_angle, abs_tol=1e-12):
        return end_angle
    unwrapped_end = end_angle
    while unwrapped_end <= start_angle:
        unwrapped_end += 2.0 * math.pi
    return unwrapped_end


def _build_maestro_arc_serialization(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    center_point: tuple[float, float],
    normal_z: float,
    z_value: float = 0.0,
) -> str:
    radius = math.hypot(start_point[0] - center_point[0], start_point[1] - center_point[1])
    if radius <= 1e-9:
        raise ValueError("No se puede serializar un arco de radio cero.")

    start_angle = _point_to_maestro_basis_angle(center_point, start_point, normal_z)
    end_angle = _point_to_maestro_basis_angle(center_point, end_point, normal_z)
    end_angle = _unwrap_maestro_arc_end_angle(start_angle, end_angle)

    return (
        f"8 {_format_maestro_number(start_angle)} {_format_maestro_number(end_angle)}\n"
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(z_value)} "
        f"0 0 {_format_maestro_number(normal_z)} 1 0 0 0 {_format_maestro_number(normal_z)} 0 {_format_maestro_number(radius)} \n"
    )


def _build_oriented_maestro_arc_serialization(
    start_angle: float,
    end_angle: float,
    center_point: tuple[float, float],
    normal_vector: tuple[float, float, float],
    u_vector: tuple[float, float, float],
    v_vector: tuple[float, float, float],
    radius: float,
    z_value: float = 0.0,
) -> str:
    if radius <= 1e-9:
        raise ValueError("No se puede serializar un arco de radio cero.")
    return (
        f"8 {_format_maestro_number(start_angle)} {_format_maestro_number(end_angle)}\n"
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(z_value)} "
        f"{_format_maestro_orientation_number(normal_vector[0])} {_format_maestro_orientation_number(normal_vector[1])} {_format_maestro_orientation_number(normal_vector[2])} "
        f"{_format_maestro_orientation_number(u_vector[0])} {_format_maestro_orientation_number(u_vector[1])} {_format_maestro_orientation_number(u_vector[2])} "
        f"{_format_maestro_orientation_number(v_vector[0])} {_format_maestro_orientation_number(v_vector[1])} {_format_maestro_orientation_number(v_vector[2])} "
        f"{_format_maestro_number(radius)} \n"
    )


def _build_circle_geometry_serialization(
    *,
    center_point: tuple[float, float, float],
    radius: float,
    normal_z: float,
) -> str:
    return (
        f"2 {_format_maestro_number(center_point[0])} {_format_maestro_number(center_point[1])} {_format_maestro_number(center_point[2])} "
        f"0 0 {_format_maestro_orientation_number(normal_z)} 1 0 0 0 {_format_maestro_orientation_number(normal_z)} 0 "
        f"{_format_maestro_number(radius)}\n"
    )


def _points_close_3d(
    point_a: tuple[float, float, float],
    point_b: tuple[float, float, float],
    tolerance: float = 1e-6,
) -> bool:
    return (
        math.isclose(point_a[0], point_b[0], abs_tol=tolerance)
        and math.isclose(point_a[1], point_b[1], abs_tol=tolerance)
        and math.isclose(point_a[2], point_b[2], abs_tol=tolerance)
    )


def _normalize_vector_2d(
    vector: tuple[float, float],
    tolerance: float = 1e-9,
) -> Optional[tuple[float, float]]:
    length = math.hypot(vector[0], vector[1])
    if length <= tolerance:
        return None
    return (vector[0] / length, vector[1] / length)


def _vectors_parallel_same_direction_2d(
    vector_a: tuple[float, float],
    vector_b: tuple[float, float],
    tolerance: float = 1e-6,
) -> bool:
    normalized_a = _normalize_vector_2d(vector_a, tolerance=tolerance)
    normalized_b = _normalize_vector_2d(vector_b, tolerance=tolerance)
    if normalized_a is None or normalized_b is None:
        return False
    return math.isclose(normalized_a[0], normalized_b[0], abs_tol=tolerance) and math.isclose(
        normalized_a[1], normalized_b[1], abs_tol=tolerance
    )


def _sample_arc_point(
    center_point: tuple[float, float, float],
    u_vector: tuple[float, float, float],
    v_vector: tuple[float, float, float],
    radius: float,
    angle: float,
) -> tuple[float, float, float]:
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    return (
        center_point[0] + (radius * ((u_vector[0] * cos_angle) + (v_vector[0] * sin_angle))),
        center_point[1] + (radius * ((u_vector[1] * cos_angle) + (v_vector[1] * sin_angle))),
        center_point[2] + (radius * ((u_vector[2] * cos_angle) + (v_vector[2] * sin_angle))),
    )


def _arc_tangent_vector(
    primitive: GeometryPrimitiveSpec,
    angle: float,
) -> Optional[tuple[float, float]]:
    if primitive.radius is None or primitive.u_vector is None or primitive.v_vector is None:
        return None
    parameter_delta = primitive.parameter_end - primitive.parameter_start
    travel_sign = 1.0 if parameter_delta >= 0.0 else -1.0
    tangent_x = (
        (-primitive.u_vector[0] * math.sin(angle)) + (primitive.v_vector[0] * math.cos(angle))
    ) * primitive.radius * travel_sign
    tangent_y = (
        (-primitive.u_vector[1] * math.sin(angle)) + (primitive.v_vector[1] * math.cos(angle))
    ) * primitive.radius * travel_sign
    return _normalize_vector_2d((tangent_x, tangent_y))


def _primitive_start_tangent_2d(primitive: GeometryPrimitiveSpec) -> Optional[tuple[float, float]]:
    if primitive.primitive_type == "Line":
        return _normalize_vector_2d(
            (
                primitive.end_point[0] - primitive.start_point[0],
                primitive.end_point[1] - primitive.start_point[1],
            )
        )
    if primitive.primitive_type == "Arc":
        return _arc_tangent_vector(primitive, primitive.parameter_start)
    return None


def _primitive_end_tangent_2d(primitive: GeometryPrimitiveSpec) -> Optional[tuple[float, float]]:
    if primitive.primitive_type == "Line":
        return _normalize_vector_2d(
            (
                primitive.end_point[0] - primitive.start_point[0],
                primitive.end_point[1] - primitive.start_point[1],
            )
        )
    if primitive.primitive_type == "Arc":
        return _arc_tangent_vector(primitive, primitive.parameter_end)
    return None


def _primitive_sample_points_2d(primitive: GeometryPrimitiveSpec) -> tuple[tuple[float, float], ...]:
    if primitive.primitive_type == "Arc":
        if primitive.center_point is None or primitive.radius is None or primitive.u_vector is None or primitive.v_vector is None:
            return (
                (primitive.start_point[0], primitive.start_point[1]),
                (primitive.end_point[0], primitive.end_point[1]),
            )
        midpoint_angle = primitive.parameter_start + ((primitive.parameter_end - primitive.parameter_start) / 2.0)
        midpoint = _sample_arc_point(
            primitive.center_point,
            primitive.u_vector,
            primitive.v_vector,
            primitive.radius,
            midpoint_angle,
        )
        return (
            (primitive.start_point[0], primitive.start_point[1]),
            (midpoint[0], midpoint[1]),
            (primitive.end_point[0], primitive.end_point[1]),
        )
    return (
        (primitive.start_point[0], primitive.start_point[1]),
        (primitive.end_point[0], primitive.end_point[1]),
    )


def _profile_bounding_box(
    primitives: Sequence[GeometryPrimitiveSpec],
    *,
    circle_center: Optional[tuple[float, float, float]] = None,
    circle_radius: Optional[float] = None,
) -> Optional[tuple[float, float, float, float]]:
    if circle_center is not None and circle_radius is not None:
        return (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius,
        )

    sample_points: list[tuple[float, float]] = []
    for primitive in primitives:
        for point in _primitive_sample_points_2d(primitive):
            sample_points.append(point)
    if not sample_points:
        return None
    xs = [point[0] for point in sample_points]
    ys = [point[1] for point in sample_points]
    return (min(xs), min(ys), max(xs), max(ys))


def _profile_signed_area(primitives: Sequence[GeometryPrimitiveSpec]) -> float:
    sampled_points: list[tuple[float, float]] = []
    for primitive in primitives:
        primitive_points = list(_primitive_sample_points_2d(primitive))
        if not primitive_points:
            continue
        if sampled_points and _points_close_2d(sampled_points[-1], primitive_points[0]):
            primitive_points = primitive_points[1:]
        sampled_points.extend(primitive_points)
    if len(sampled_points) < 3:
        return 0.0
    if not _points_close_2d(sampled_points[0], sampled_points[-1]):
        sampled_points.append(sampled_points[0])
    double_area = 0.0
    for start_point, end_point in zip(sampled_points, sampled_points[1:]):
        double_area += (start_point[0] * end_point[1]) - (end_point[0] * start_point[1])
    return double_area / 2.0


def _primitive_to_serialization(primitive: GeometryPrimitiveSpec) -> str:
    if primitive.primitive_type == "Line":
        dx = primitive.end_point[0] - primitive.start_point[0]
        dy = primitive.end_point[1] - primitive.start_point[1]
        dz = primitive.end_point[2] - primitive.start_point[2]
        length = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
        if length <= 1e-9:
            raise ValueError("No se puede serializar un segmento de longitud cero.")
        direction = (dx / length, dy / length, dz / length)
        if primitive.direction_hint is not None:
            direction = primitive.direction_hint
        origin_point = (
            primitive.start_point[0] - (direction[0] * primitive.parameter_start),
            primitive.start_point[1] - (direction[1] * primitive.parameter_start),
            primitive.start_point[2] - (direction[2] * primitive.parameter_start),
        )
        return _build_parameterized_maestro_line_serialization(
            parameter_start=primitive.parameter_start,
            parameter_end=primitive.parameter_end,
            origin_point=origin_point,
            direction=direction,
        )
    if primitive.primitive_type != "Arc":
        raise ValueError(f"Tipo de primitiva no soportado: {primitive.primitive_type}")
    if (
        primitive.center_point is None
        or primitive.radius is None
        or primitive.normal_vector is None
        or primitive.u_vector is None
        or primitive.v_vector is None
    ):
        raise ValueError("Una primitiva de arco necesita centro, radio y base orientada.")
    return _build_oriented_maestro_arc_serialization(
        primitive.parameter_start,
        primitive.parameter_end,
        (primitive.center_point[0], primitive.center_point[1]),
        primitive.normal_vector,
        primitive.u_vector,
        primitive.v_vector,
        primitive.radius,
        z_value=primitive.center_point[2],
    )


def _build_profile_geometry_spec(
    *,
    geometry_type: str,
    primitives: Sequence[GeometryPrimitiveSpec],
    serialization: Optional[str] = None,
    member_serializations: Sequence[str] = (),
) -> GeometryProfileSpec:
    normalized_primitives = tuple(primitives)
    if geometry_type != "GeomCircle" and not normalized_primitives:
        raise ValueError("El perfil geometrico necesita al menos una primitiva.")

    normalized_member_serializations = tuple(
        _normalize_curve_serialization_text(member_serialization)
        for member_serialization in member_serializations
    )
    normalized_serialization = (
        _normalize_curve_serialization_text(serialization)
        if serialization is not None
        else None
    )

    if geometry_type == "GeomCartesianPoint":
        if len(normalized_primitives) != 1 or normalized_primitives[0].primitive_type != "Point":
            raise ValueError("Un GeomCartesianPoint requiere exactamente una primitiva Point.")
        point = normalized_primitives[0].start_point
        if not _points_close_3d(normalized_primitives[0].start_point, normalized_primitives[0].end_point):
            raise ValueError("La primitiva Point debe usar el mismo punto como inicio y fin.")
        return GeometryProfileSpec(
            geometry_type="GeomCartesianPoint",
            family="Point",
            primitives=normalized_primitives,
            is_closed=False,
            winding=None,
            start_mode=None,
            has_arcs=False,
            corner_radii=(),
            bounding_box=(point[0], point[1], point[0], point[1]),
            center_point=point,
        )

    if geometry_type == "GeomTrimmedCurve":
        primitive = normalized_primitives[0]
        if primitive.primitive_type == "Line":
            delta_x = primitive.end_point[0] - primitive.start_point[0]
            delta_y = primitive.end_point[1] - primitive.start_point[1]
            if math.isclose(delta_x, 0.0, abs_tol=1e-6) and not math.isclose(delta_y, 0.0, abs_tol=1e-6):
                family = "LineVertical"
            elif math.isclose(delta_y, 0.0, abs_tol=1e-6) and not math.isclose(delta_x, 0.0, abs_tol=1e-6):
                family = "LineHorizontal"
            else:
                family = "Line"
            winding = None
            has_arcs = False
            corner_radii: tuple[float, ...] = ()
        else:
            family = "Arc"
            winding = (
                "CounterClockwise"
                if (primitive.normal_vector is None or primitive.normal_vector[2] >= 0.0)
                else "Clockwise"
            )
            has_arcs = True
            corner_radii = (float(primitive.radius),) if primitive.radius is not None else ()
        return GeometryProfileSpec(
            geometry_type="GeomTrimmedCurve",
            family=family,
            primitives=normalized_primitives,
            is_closed=False,
            winding=winding,
            start_mode=None,
            has_arcs=has_arcs,
            corner_radii=corner_radii,
            bounding_box=_profile_bounding_box(normalized_primitives),
            serialization=normalized_serialization or _primitive_to_serialization(primitive),
        )

    if geometry_type != "GeomCompositeCurve":
        raise ValueError(f"Tipo de perfil geometrico no soportado: {geometry_type}")

    is_closed = _points_close_3d(
        normalized_primitives[0].start_point,
        normalized_primitives[-1].end_point,
    )
    has_arcs = any(primitive.primitive_type == "Arc" for primitive in normalized_primitives)
    start_mode = None
    if is_closed:
        first_tangent = _primitive_start_tangent_2d(normalized_primitives[0])
        last_tangent = _primitive_end_tangent_2d(normalized_primitives[-1])
        if first_tangent is not None and last_tangent is not None and _vectors_parallel_same_direction_2d(first_tangent, last_tangent):
            start_mode = "MidEdge"
        else:
            start_mode = "Corner"

    if not is_closed:
        family = "OpenCompositeCurve" if has_arcs else "OpenPolyline"
        winding = None
    else:
        signed_area = _profile_signed_area(normalized_primitives)
        winding = "CounterClockwise" if signed_area >= 0.0 else "Clockwise"
        if has_arcs:
            family = "ClosedPolylineMidEdgeStartRounded" if start_mode == "MidEdge" else "ClosedPolylineRounded"
        else:
            family = "ClosedPolylineMidEdgeStart" if start_mode == "MidEdge" else "ClosedPolylineCornerStart"

    return GeometryProfileSpec(
        geometry_type="GeomCompositeCurve",
        family=family,
        primitives=normalized_primitives,
        is_closed=is_closed,
        winding=winding,
        start_mode=start_mode,
        has_arcs=has_arcs,
        corner_radii=tuple(
            sorted(
                {
                    round(float(primitive.radius), 6)
                    for primitive in normalized_primitives
                    if primitive.radius is not None and primitive.primitive_type == "Arc"
                }
            )
        ),
        bounding_box=_profile_bounding_box(normalized_primitives),
        member_serializations=normalized_member_serializations
        or tuple(_primitive_to_serialization(primitive) for primitive in normalized_primitives),
    )


def _curve_spec_from_profile_geometry(profile: GeometryProfileSpec) -> _CurveSpec:
    if profile.geometry_type == "GeomCartesianPoint":
        raise ValueError("El perfil Point no puede convertirse en una curva/toolpath.")
    if profile.geometry_type == "GeomTrimmedCurve":
        if profile.serialization is None:
            raise ValueError("El perfil lineal/arco necesita serialization para convertirse en curva.")
        return _trimmed_curve_spec(profile.serialization)
    if profile.geometry_type == "GeomCircle":
        if profile.serialization is None:
            raise ValueError("El perfil circular necesita serialization para convertirse en curva.")
        return _circle_curve_spec(profile.serialization)
    if profile.geometry_type == "GeomCompositeCurve":
        return _composite_curve_spec(profile.member_serializations)
    raise ValueError(f"Tipo de perfil geometrico no soportado: {profile.geometry_type}")


def _parse_trimmed_curve_line(text: str) -> Optional[GeometryPrimitiveSpec]:
    lines = [line.strip().split() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    header = lines[0]
    body = lines[1]
    if len(header) < 3 or len(body) < 7 or header[0] != "8" or body[0] != "1":
        return None
    try:
        parameter_start = float(header[1])
        parameter_end = float(header[2])
        origin_x = float(body[1])
        origin_y = float(body[2])
        origin_z = float(body[3])
        direction_x = float(body[4])
        direction_y = float(body[5])
        direction_z = float(body[6])
    except ValueError:
        return None

    # Maestro puede trimar la misma recta con parametros crecientes o decrecientes.
    # Para leer horario/antihorario sin perder informacion hay que evaluar ambos
    # puntos sobre la recta base, en vez de asumir `8 0 longitud`.
    start_point = (
        origin_x + (direction_x * parameter_start),
        origin_y + (direction_y * parameter_start),
        origin_z + (direction_z * parameter_start),
    )
    end_point = (
        origin_x + (direction_x * parameter_end),
        origin_y + (direction_y * parameter_end),
        origin_z + (direction_z * parameter_end),
    )
    return GeometryPrimitiveSpec(
        primitive_type="Line",
        start_point=start_point,
        end_point=end_point,
        parameter_start=parameter_start,
        parameter_end=parameter_end,
    )


def _parse_trimmed_curve_arc(text: str) -> Optional[GeometryPrimitiveSpec]:
    lines = [line.strip().split() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    header = lines[0]
    body = lines[1]
    if len(header) < 3 or len(body) < 14 or header[0] != "8" or body[0] != "2":
        return None
    try:
        parameter_start = float(header[1])
        parameter_end = float(header[2])
        center_x = float(body[1])
        center_y = float(body[2])
        center_z = float(body[3])
        normal_vector = (float(body[4]), float(body[5]), float(body[6]))
        u_vector = (float(body[7]), float(body[8]), float(body[9]))
        v_vector = (float(body[10]), float(body[11]), float(body[12]))
        radius = float(body[13])
    except ValueError:
        return None
    center_point = (center_x, center_y, center_z)
    start_point = _sample_arc_point(center_point, u_vector, v_vector, radius, parameter_start)
    end_point = _sample_arc_point(center_point, u_vector, v_vector, radius, parameter_end)
    return GeometryPrimitiveSpec(
        primitive_type="Arc",
        start_point=start_point,
        end_point=end_point,
        parameter_start=parameter_start,
        parameter_end=parameter_end,
        center_point=center_point,
        radius=radius,
        normal_vector=normal_vector,
        u_vector=u_vector,
        v_vector=v_vector,
    )


def _parse_geometry_primitive(text: str) -> Optional[GeometryPrimitiveSpec]:
    return _parse_trimmed_curve_line(text) or _parse_trimmed_curve_arc(text)


def _parse_circle_geometry_profile(text: str) -> Optional[GeometryProfileSpec]:
    parts = (text or "").strip().split()
    if len(parts) < 14 or parts[0] != "2":
        return None
    try:
        center_x = float(parts[1])
        center_y = float(parts[2])
        center_z = float(parts[3])
        normal_z = float(parts[6])
        radius = float(parts[13])
    except ValueError:
        return None
    winding = "CounterClockwise" if normal_z >= 0.0 else "Clockwise"
    return replace(
        build_circle_geometry_profile(
            center_x,
            center_y,
            radius,
            z_value=center_z,
            winding=winding,
        ),
        serialization=_normalize_curve_serialization_text(text),
    )


def _parse_cartesian_point_geometry_profile(node: ET.Element) -> Optional[GeometryProfileSpec]:
    point_x_text = _text(node, "./{*}_x")
    point_y_text = _text(node, "./{*}_y")
    point_z_text = _text(node, "./{*}_z", "0")
    if not point_x_text or not point_y_text:
        return None
    try:
        point_x = float(point_x_text)
        point_y = float(point_y_text)
        point_z = float(point_z_text)
    except ValueError:
        return None
    return build_point_geometry_profile(point_x, point_y, z_value=point_z)


def _extract_geometry_profile(node: ET.Element) -> Optional[GeometryProfileSpec]:
    geometry_type = _xsi_type(node)
    if "GeomCartesianPoint" in geometry_type:
        return _parse_cartesian_point_geometry_profile(node)
    if "GeomCircle" in geometry_type:
        return _parse_circle_geometry_profile(_raw_text(node, "./{*}_serializationGeometryDescription"))
    if "GeomTrimmedCurve" in geometry_type:
        serialization = _raw_text(node, "./{*}_serializationGeometryDescription")
        primitive = _parse_geometry_primitive(serialization)
        if primitive is None:
            return None
        return _build_profile_geometry_spec(
            geometry_type="GeomTrimmedCurve",
            primitives=(primitive,),
            serialization=serialization,
        )
    if "GeomCompositeCurve" in geometry_type:
        member_serializations = [member.text or "" for member in node.findall("./{*}_serializingMembers/{*}string")]
        primitives = []
        for member_serialization in member_serializations:
            primitive = _parse_geometry_primitive(member_serialization)
            if primitive is None:
                return None
            primitives.append(primitive)
        return _build_profile_geometry_spec(
            geometry_type="GeomCompositeCurve",
            primitives=tuple(primitives),
            member_serializations=member_serializations,
        )
    return None


def _build_polyline_toolpath_profile(
    state: PgmxState,
    spec: _HydratedPolylineMillingSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para una polilinea abierta o cerrada."""

    cut_z = _toolpath_cut_z(state, spec)
    if _is_closed_polyline_points(spec.points):
        nominal_profile = _build_closed_polyline_geometry_profile(spec.points, z_value=cut_z)
    else:
        nominal_profile = _build_open_polyline_geometry_profile(spec.points, z_value=cut_z)
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if nominal_profile.is_closed:
        return _build_closed_profile_strategy_toolpath(state, spec, base_profile, strategy)
    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        return _build_unidirectional_open_profile_strategy_toolpath(state, spec, base_profile, strategy)
    return _build_bidirectional_open_profile_strategy_toolpath(state, spec, base_profile, strategy)


def _build_circle_toolpath_profile(
    state: PgmxState,
    spec: _HydratedCircleMillingSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para un fresado circular cerrado."""

    cut_z = _toolpath_cut_z(state, spec)
    nominal_profile = build_circle_geometry_profile(
        spec.center_x,
        spec.center_y,
        spec.radius,
        z_value=cut_z,
        winding=spec.winding,
    )
    base_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return base_profile
    if isinstance(strategy, HelicalMillingStrategySpec):
        return _build_helical_circle_strategy_toolpath(state, spec, base_profile, strategy)
    return _build_closed_profile_strategy_toolpath(state, spec, base_profile, strategy)


def _build_squaring_toolpath_profile(
    state: PgmxState,
    spec: _HydratedSquaringMillingSpec,
) -> GeometryProfileSpec:
    """Construye la trayectoria compensada para un escuadrado exterior."""

    cut_z = _toolpath_cut_z(state, spec)
    nominal_profile = _build_squaring_geometry_profile(state, spec, z_value=cut_z)
    toolpath_profile = build_compensated_toolpath_profile(
        nominal_profile,
        side_of_feature=spec.side_of_feature,
        tool_width=spec.tool_width,
        z_value=cut_z,
    )
    toolpath_profile = _reparameterize_squaring_toolpath_profile(toolpath_profile)
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return toolpath_profile
    return _build_closed_profile_strategy_toolpath(state, spec, toolpath_profile, strategy)


def _parse_line_serialization(text: str) -> Optional[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    primitive = _parse_trimmed_curve_line(text)
    if primitive is None:
        return None
    return (primitive.start_point, primitive.end_point)


def _matches_line_geometry(template: dict[str, object], spec: LineMillingSpec, tolerance: float = 1e-6) -> bool:
    parsed = _parse_line_serialization(str(template.get("geometry_serialization") or ""))
    if parsed is None:
        return False
    start, end = parsed
    expected = (spec.start_x, spec.start_y, 0.0, spec.end_x, spec.end_y, 0.0)
    direct = (start[0], start[1], start[2], end[0], end[1], end[2])
    reverse = (end[0], end[1], end[2], start[0], start[1], start[2])

    def close(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
        return all(math.isclose(x, y, abs_tol=tolerance) for x, y in zip(a, b))

    return close(direct, expected) or close(reverse, expected)


def _curve_spec_points(curve_spec: _CurveSpec) -> Optional[tuple[tuple[float, float, float], ...]]:
    if curve_spec.geometry_type in {"GeomTrimmedCurve", "GeomCircle"}:
        if curve_spec.serialization is None:
            return None
        primitive = _parse_geometry_primitive(curve_spec.serialization)
        if primitive is not None:
            return (primitive.start_point, primitive.end_point)
        circle_profile = _parse_circle_geometry_profile(curve_spec.serialization)
        if circle_profile is None or circle_profile.center_point is None or circle_profile.radius is None:
            return None
        center_x, center_y, center_z = circle_profile.center_point
        radius = circle_profile.radius
        return (
            (center_x + radius, center_y, center_z),
            (center_x, center_y + radius, center_z),
            (center_x - radius, center_y, center_z),
            (center_x, center_y - radius, center_z),
            (center_x + radius, center_y, center_z),
        )

    if curve_spec.geometry_type != "GeomCompositeCurve":
        return None

    points: list[tuple[float, float, float]] = []
    for member_serialization in curve_spec.member_serializations:
        primitive = _parse_geometry_primitive(member_serialization)
        if primitive is None:
            return None
        start_point = primitive.start_point
        end_point = primitive.end_point
        if not points:
            points.append(start_point)
        points.append(end_point)
    return tuple(points)


def _matches_polyline_geometry(template: dict[str, object], spec: PolylineMillingSpec, tolerance: float = 1e-6) -> bool:
    geometry_curve = template.get("geometry_curve")
    if not isinstance(geometry_curve, _CurveSpec):
        return False
    parsed_points = _curve_spec_points(geometry_curve)
    if parsed_points is None:
        return False
    expected_points = tuple((point[0], point[1], 0.0) for point in spec.points)
    if len(parsed_points) != len(expected_points):
        return False
    return all(
        math.isclose(parsed_point[0], expected_point[0], abs_tol=tolerance)
        and math.isclose(parsed_point[1], expected_point[1], abs_tol=tolerance)
        and math.isclose(parsed_point[2], expected_point[2], abs_tol=tolerance)
        for parsed_point, expected_point in zip(parsed_points, expected_points)
    )


def _matches_circle_geometry(template: dict[str, object], spec: CircleMillingSpec, tolerance: float = 1e-6) -> bool:
    geometry_curve = template.get("geometry_curve")
    if not isinstance(geometry_curve, _CurveSpec):
        return False
    if geometry_curve.geometry_type != "GeomCircle" or geometry_curve.serialization is None:
        return False
    parsed_profile = _parse_circle_geometry_profile(geometry_curve.serialization)
    if parsed_profile is None or parsed_profile.center_point is None or parsed_profile.radius is None:
        return False
    return (
        math.isclose(parsed_profile.center_point[0], spec.center_x, abs_tol=tolerance)
        and math.isclose(parsed_profile.center_point[1], spec.center_y, abs_tol=tolerance)
        and math.isclose(parsed_profile.center_point[2], 0.0, abs_tol=tolerance)
        and math.isclose(parsed_profile.radius, spec.radius, abs_tol=tolerance)
        and _normalize_geometry_winding(parsed_profile.winding) == _normalize_geometry_winding(spec.winding)
    )


def _extract_depth_spec_from_template(
    feature: ET.Element,
    operation: ET.Element,
    matching_expressions: Sequence[ET.Element],
    depth_variable_name: str,
) -> MillingDepthSpec:
    expression_values = {
        _text(node, "./{*}Property/{*}InnerField/{*}Name"): _text(node, "./{*}Value")
        for node in matching_expressions
        if _text(node, "./{*}Property/{*}Name") == "Depth"
    }
    bottom_condition_type = _xsi_type(feature.find("./{*}BottomCondition"))
    overcut_length = _safe_float(_text(operation, "./{*}OvercutLength"), 0.0)
    if "ThroughMillingBottom" in bottom_condition_type or (
        expression_values.get("StartDepth") == depth_variable_name
        and expression_values.get("EndDepth") == depth_variable_name
    ):
        return build_milling_depth_spec(is_through=True, extra_depth=overcut_length)

    start_depth = _safe_float(_text(feature, "./{*}Depth/{*}StartDepth"), 0.0)
    end_depth = _safe_float(_text(feature, "./{*}Depth/{*}EndDepth"), 0.0)
    if not math.isclose(start_depth, end_depth, abs_tol=1e-6):
        raise ValueError("La plantilla usa profundidades distintas para StartDepth/EndDepth; caso no soportado aun.")
    return build_milling_depth_spec(is_through=False, target_depth=start_depth)


def _extract_milling_strategy_spec_from_operation(
    operation: ET.Element,
) -> Optional[MillingStrategySpec]:
    strategy_node = operation.find("./{*}MachiningStrategy")
    if strategy_node is None:
        return None
    if (strategy_node.get(f"{{{XSI_NS}}}nil") or "").strip().lower() == "true":
        return None

    strategy_type = _xsi_type(strategy_node)
    allow_multiple_passes = _safe_bool(_text(strategy_node, "./{*}AllowMultiplePasses"), False)
    allows_finish_cutting = _safe_bool(_text(strategy_node, "./{*}AllowsFinishCutting"), True)
    axial_cutting_depth = _safe_float(_text(strategy_node, "./{*}AxialCuttingDepth"), 0.0)
    axial_finish_cutting_depth = _safe_float(_text(strategy_node, "./{*}AxialFinishCuttingDepth"), 0.0)
    stroke_connection_strategy = _text(strategy_node, "./{*}StrokeConnectionStrategy", "Automatic")

    if "ContourParallel" in strategy_type:
        return build_contour_parallel_milling_strategy_spec(
            rotation_direction=_text(strategy_node, "./{*}RotationDirection", "CounterClockwise"),
            stroke_connection_strategy=stroke_connection_strategy,
            inside_to_outside=_safe_bool(_text(strategy_node, "./{*}InsideToOutSide"), True),
            overlap=_safe_float(_text(strategy_node, "./{*}Overlap"), 0.5),
            is_helic_strategy=_safe_bool(_text(strategy_node, "./{*}IsHelicStrategy"), False),
            allow_multiple_passes=allow_multiple_passes,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
            cutmode=_text(strategy_node, "./{*}Cutmode", "Climb"),
            is_internal=_safe_bool(_text(strategy_node, "./{*}IsInternal"), True),
            radial_cutting_depth=_safe_float(_text(strategy_node, "./{*}RadialCuttingDepth"), 0.0),
            radial_finish_cutting_depth=_safe_float(_text(strategy_node, "./{*}RadialFinishCuttingDepth"), 0.0),
            allows_bidirectional=_safe_bool(_text(strategy_node, "./{*}AllowsBidirectional"), False),
            allows_finish_cutting=_safe_bool(_text(strategy_node, "./{*}AllowsFinishCutting"), False),
        )
    if "UnidirectionalMilling" in strategy_type:
        return build_unidirectional_milling_strategy_spec(
            connection_mode=stroke_connection_strategy,
            allow_multiple_passes=allow_multiple_passes,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    if "BidirectionalMilling" in strategy_type:
        return build_bidirectional_milling_strategy_spec(
            allow_multiple_passes=allow_multiple_passes,
            axial_cutting_depth=axial_cutting_depth,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    if "HelicMilling" in strategy_type:
        return build_helical_milling_strategy_spec(
            axial_cutting_depth=axial_cutting_depth,
            allows_finish_cutting=allows_finish_cutting,
            axial_finish_cutting_depth=axial_finish_cutting_depth,
        )
    return None


def _strategy_comparison_key(
    strategy: Optional[MillingStrategySpec],
    *,
    is_closed_profile: bool,
) -> Optional[tuple[object, ...]]:
    normalized_strategy = _normalize_milling_strategy_spec(strategy)
    if normalized_strategy is None:
        return None
    if isinstance(normalized_strategy, UnidirectionalMillingStrategySpec):
        return (
            "Unidirectional",
            _resolve_unidirectional_connection_mode(
                normalized_strategy,
                is_closed_profile=is_closed_profile,
            ),
            normalized_strategy.allow_multiple_passes,
            normalized_strategy.axial_cutting_depth,
            normalized_strategy.axial_finish_cutting_depth,
        )
    if isinstance(normalized_strategy, HelicalMillingStrategySpec):
        return (
            "Helical",
            normalized_strategy.allows_finish_cutting,
            normalized_strategy.axial_cutting_depth,
            normalized_strategy.axial_finish_cutting_depth,
        )
    if isinstance(normalized_strategy, ContourParallelMillingStrategySpec):
        return (
            "ContourParallel",
            normalized_strategy.rotation_direction,
            normalized_strategy.stroke_connection_strategy,
            normalized_strategy.inside_to_outside,
            normalized_strategy.overlap,
            normalized_strategy.is_helic_strategy,
            normalized_strategy.allow_multiple_passes,
            normalized_strategy.axial_cutting_depth,
            normalized_strategy.axial_finish_cutting_depth,
            normalized_strategy.cutmode,
            normalized_strategy.is_internal,
            normalized_strategy.radial_cutting_depth,
            normalized_strategy.radial_finish_cutting_depth,
            normalized_strategy.allows_bidirectional,
            normalized_strategy.allows_finish_cutting,
        )
    return (
        "Bidirectional",
        normalized_strategy.allow_multiple_passes,
        normalized_strategy.axial_cutting_depth,
        normalized_strategy.axial_finish_cutting_depth,
    )


def _can_hydrate_exact_serialization(template: dict[str, object], spec: LineMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    source_strategy = template.get("milling_strategy") if isinstance(
        template.get("milling_strategy"),
        (
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
            ContourParallelMillingStrategySpec,
        ),
    ) else None
    if _strategy_comparison_key(source_strategy, is_closed_profile=False) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=False,
    ):
        return False
    requested_side = _normalize_side_of_feature(spec.side_of_feature)
    source_side = str(template["side_of_feature"])
    if requested_side != source_side:
        return False
    source_approach = _normalize_approach_spec(template.get("approach") if isinstance(template.get("approach"), ApproachSpec) else None)
    requested_approach = _normalize_approach_spec(spec.approach)
    if source_approach != requested_approach:
        return False
    source_retract = _normalize_retract_spec(template.get("retract") if isinstance(template.get("retract"), RetractSpec) else None)
    requested_retract = _normalize_retract_spec(spec.retract)
    if source_retract != requested_retract:
        return False
    if not _matches_line_geometry(template, spec):
        return False
    if requested_side == "Center":
        return True

    source_tool_width = float(template["tool_width"])
    source_tool_id = str(template["tool_id"])
    source_tool_name = str(template["tool_name"])
    return (
        math.isclose(spec.tool_width, source_tool_width, abs_tol=1e-6)
        and spec.tool_id == source_tool_id
        and spec.tool_name == source_tool_name
    )


def _can_hydrate_exact_polyline_serialization(template: dict[str, object], spec: PolylineMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    source_strategy = template.get("milling_strategy") if isinstance(
        template.get("milling_strategy"),
        (
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
            ContourParallelMillingStrategySpec,
        ),
    ) else None
    is_closed_profile = _is_closed_polyline_points(spec.points)
    if _strategy_comparison_key(source_strategy, is_closed_profile=is_closed_profile) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=is_closed_profile,
    ):
        return False
    requested_side = _normalize_side_of_feature(spec.side_of_feature)
    source_side = str(template["side_of_feature"])
    if requested_side != source_side:
        return False
    source_approach = _normalize_approach_spec(template.get("approach") if isinstance(template.get("approach"), ApproachSpec) else None)
    requested_approach = _normalize_approach_spec(spec.approach)
    if source_approach != requested_approach:
        return False
    source_retract = _normalize_retract_spec(template.get("retract") if isinstance(template.get("retract"), RetractSpec) else None)
    requested_retract = _normalize_retract_spec(spec.retract)
    if source_retract != requested_retract:
        return False
    if not _matches_polyline_geometry(template, spec):
        return False
    if requested_side == "Center":
        return True

    source_tool_width = float(template["tool_width"])
    source_tool_id = str(template["tool_id"])
    source_tool_name = str(template["tool_name"])
    return (
        math.isclose(spec.tool_width, source_tool_width, abs_tol=1e-6)
        and spec.tool_id == source_tool_id
        and spec.tool_name == source_tool_name
    )


def _can_hydrate_exact_circle_serialization(template: dict[str, object], spec: CircleMillingSpec) -> bool:
    source_depth_spec = template.get("depth_spec") if isinstance(template.get("depth_spec"), MillingDepthSpec) else None
    requested_depth_spec = _normalize_milling_depth_spec(spec.depth_spec)
    if source_depth_spec is None or _normalize_milling_depth_spec(source_depth_spec) != requested_depth_spec:
        return False
    source_strategy = template.get("milling_strategy") if isinstance(
        template.get("milling_strategy"),
        (
            UnidirectionalMillingStrategySpec,
            BidirectionalMillingStrategySpec,
            HelicalMillingStrategySpec,
        ),
    ) else None
    if _strategy_comparison_key(source_strategy, is_closed_profile=True) != _strategy_comparison_key(
        spec.milling_strategy,
        is_closed_profile=True,
    ):
        return False
    requested_side = _normalize_side_of_feature(spec.side_of_feature)
    source_side = str(template["side_of_feature"])
    if requested_side != source_side:
        return False
    source_approach = _normalize_approach_spec(template.get("approach") if isinstance(template.get("approach"), ApproachSpec) else None)
    requested_approach = _normalize_approach_spec(spec.approach)
    if source_approach != requested_approach:
        return False
    source_retract = _normalize_retract_spec(template.get("retract") if isinstance(template.get("retract"), RetractSpec) else None)
    requested_retract = _normalize_retract_spec(spec.retract)
    if source_retract != requested_retract:
        return False
    if not _matches_circle_geometry(template, spec):
        return False
    if requested_side == "Center":
        return True

    source_tool_width = float(template["tool_width"])
    source_tool_id = str(template["tool_id"])
    source_tool_name = str(template["tool_name"])
    return (
        math.isclose(spec.tool_width, source_tool_width, abs_tol=1e-6)
        and spec.tool_id == source_tool_id
        and spec.tool_name == source_tool_name
    )


def _trimmed_curve_spec(serialization: str) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomTrimmedCurve",
        serialization=_normalize_curve_serialization_text(serialization),
    )


def _circle_curve_spec(serialization: str) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomCircle",
        serialization=_normalize_curve_serialization_text(serialization),
    )


def _composite_curve_spec(
    member_serializations: Sequence[str],
    member_keys: Sequence[str] = (),
) -> _CurveSpec:
    return _CurveSpec(
        geometry_type="GeomCompositeCurve",
        member_keys=tuple(member_keys),
        member_serializations=tuple(_normalize_curve_serialization_text(serialization) for serialization in member_serializations),
    )


def _build_curve_holder(
    local_name: str,
    curve_spec: _CurveSpec,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    curve = ET.Element(
        _qname(BASE_MODEL_NS, local_name),
        {f"{{{XSI_NS}}}type": f"c:{curve_spec.geometry_type}"},
    )
    _set_xmlns(curve, "c", GEOMETRY_NS)
    _append_key(curve, "0", "System.Object")
    _append_blank_name(curve)
    _append_node(curve, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(curve, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    if curve_spec.geometry_type in {"GeomTrimmedCurve", "GeomCircle"}:
        if curve_spec.serialization is None:
            raise ValueError(f"La curva {curve_spec.geometry_type} requiere una serializacion raw.")
        _append_node(curve, GEOMETRY_NS, "_serializationGeometryDescription", curve_spec.serialization)
        return curve

    if curve_spec.geometry_type != "GeomCompositeCurve":
        raise ValueError(f"Tipo de curva no soportado: {curve_spec.geometry_type}")

    member_keys = tuple(curve_spec.member_keys or generated_member_keys)
    if not curve_spec.member_serializations:
        raise ValueError("La curva GeomCompositeCurve requiere al menos un miembro serializado.")
    if len(member_keys) != len(curve_spec.member_serializations):
        raise ValueError("La curva GeomCompositeCurve requiere una clave por cada miembro serializado.")

    keys_group = _append_node(curve, GEOMETRY_NS, "_serializingKeys")
    members_group = _append_node(curve, GEOMETRY_NS, "_serializingMembers")
    for key_id, member_serialization in zip(member_keys, curve_spec.member_serializations):
        _append_node(keys_group, ARRAYS_NS, "unsignedInt", key_id)
        _append_node(members_group, ARRAYS_NS, "string", member_serialization)
    return curve


def _geometry_object_type(geometry_type: str) -> str:
    mapping = {
        "GeomTrimmedCurve": "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
        "GeomCompositeCurve": "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCompositeCurve",
        "GeomCircle": "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCircle",
    }
    if geometry_type not in mapping:
        raise ValueError(f"Tipo de geometria no soportado: {geometry_type}")
    return mapping[geometry_type]


def _build_geometry_from_curve_spec(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    curve_spec: _CurveSpec,
    *,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    geometry = ET.Element(
        _qname(GEOMETRY_NS, "GeomGeometry"),
        {f"{{{XSI_NS}}}type": f"a:{curve_spec.geometry_type}"},
    )
    _set_xmlns(geometry, "a", GEOMETRY_NS)
    _append_key(geometry, geometry_id, _geometry_object_type(curve_spec.geometry_type))
    _append_blank_name(geometry)
    _append_node(geometry, GEOMETRY_NS, "IsAbsolute", "false")
    _append_object_ref(geometry, GEOMETRY_NS, "PlaneID", plane_id, plane_object_type)
    if curve_spec.geometry_type in {"GeomTrimmedCurve", "GeomCircle"}:
        if curve_spec.serialization is None:
            raise ValueError(f"La geometria {curve_spec.geometry_type} requiere una serializacion raw.")
        _append_node(geometry, GEOMETRY_NS, "_serializationGeometryDescription", curve_spec.serialization)
        return geometry

    member_keys = tuple(curve_spec.member_keys or generated_member_keys)
    if len(member_keys) != len(curve_spec.member_serializations):
        raise ValueError("La geometria compuesta requiere una clave por cada miembro serializado.")
    keys_group = _append_node(geometry, GEOMETRY_NS, "_serializingKeys")
    members_group = _append_node(geometry, GEOMETRY_NS, "_serializingMembers")
    for key_id, member_serialization in zip(member_keys, curve_spec.member_serializations):
        _append_node(keys_group, ARRAYS_NS, "unsignedInt", key_id)
        _append_node(members_group, ARRAYS_NS, "string", member_serialization)
    return geometry


def _build_vector_holder(local_name: str, x_value: float, y_value: float, z_value: float) -> ET.Element:
    vector = ET.Element(_qname(BASE_MODEL_NS, local_name))
    _append_key(vector, "0", "System.Object")
    _append_blank_name(vector)
    _append_node(vector, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(vector, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    _append_node(vector, GEOMETRY_NS, "_x", _compact_number(x_value))
    _append_node(vector, GEOMETRY_NS, "_y", _compact_number(y_value))
    _append_node(vector, GEOMETRY_NS, "_z", _compact_number(z_value))
    _append_node(vector, GEOMETRY_NS, "XRotation", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(vector, GEOMETRY_NS, "ZRotation", attrib={f"{{{XSI_NS}}}nil": "true"})
    return vector


def _build_start_point(x_value: float, y_value: float, z_value: float) -> ET.Element:
    start_point = ET.Element(_qname(PGMX_NS, "StartPoint"))
    _append_key(start_point, "0", "System.Object")
    _append_blank_name(start_point)
    _append_node(start_point, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(start_point, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    _append_node(start_point, GEOMETRY_NS, "_x", _compact_number(x_value))
    _append_node(start_point, GEOMETRY_NS, "_y", _compact_number(y_value))
    _append_node(start_point, GEOMETRY_NS, "_z", _compact_number(z_value))
    return start_point


def _build_identity_profile_placement() -> ET.Element:
    placement = ET.Element(_qname(PGMX_NS, "Placement"))
    _append_key(placement, "0", "System.Object")
    _append_blank_name(placement)
    _append_node(placement, GEOMETRY_NS, "IsAbsolute", "true")
    _append_object_ref(placement, GEOMETRY_NS, "PlaneID", "0", "System.Object")
    _append_node(placement, GEOMETRY_NS, "_xN", "0")
    _append_node(placement, GEOMETRY_NS, "_xP", "0")
    _append_node(placement, GEOMETRY_NS, "_xVx", "1")
    _append_node(placement, GEOMETRY_NS, "_yN", "0")
    _append_node(placement, GEOMETRY_NS, "_yP", "0")
    _append_node(placement, GEOMETRY_NS, "_yVx", "0")
    _append_node(placement, GEOMETRY_NS, "_zN", "1")
    _append_node(placement, GEOMETRY_NS, "_zP", "0")
    _append_node(placement, GEOMETRY_NS, "_zVx", "-0")
    return placement


def _find_plane_ref(root: ET.Element, plane_name: str) -> tuple[str, str]:
    planes = root.find("./{*}Planes")
    if planes is None:
        raise ValueError("La plantilla no contiene Planes.")
    for plane in list(planes):
        plane_type = _text(plane, "./{*}Type") or _text(plane, "./{*}Name")
        if plane_type == plane_name:
            return (
                _text(plane, "./{*}Key/{*}ID"),
                _text(plane, "./{*}Key/{*}ObjectType"),
            )
    raise ValueError(f"La plantilla no contiene el plano '{plane_name}'.")


def _reserve_ids(root: ET.Element, count: int, preferred_start: Optional[int] = None) -> list[str]:
    first_default_id = int(next(_id_counter(root)))
    start_id = first_default_id if preferred_start is None else max(first_default_id, preferred_start)
    return [str(start_id + offset) for offset in range(count)]


def _extract_line_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomTrimmedCurve" in _xsi_type(node)
        ),
        None,
    )
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "GeneralProfileFeature" in _xsi_type(node)
        ),
        None,
    )
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado lineal compatible.")

    def extract_toolpath_curve(toolpath: ET.Element) -> _CurveSpec:
        basic_curve = toolpath.find("./{*}BasicCurve")
        curve_type = _xsi_type(basic_curve)
        if "GeomCompositeCurve" in curve_type:
            return _composite_curve_spec(
                [
                    member.text or ""
                    for member in basic_curve.findall("./{*}_serializingMembers/{*}string")
                ],
                [
                    (key.text or "").strip()
                    for key in basic_curve.findall("./{*}_serializingKeys/{*}unsignedInt")
                ],
            )
        return _trimmed_curve_spec(_raw_text(basic_curve, "./{*}_serializationGeometryDescription"))

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    depth_variable_name = _workpiece_depth_name(workpiece)
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): extract_toolpath_curve(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
    }
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id

    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(
            feature,
            operation,
            matching_expressions,
            depth_variable_name,
        ),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "milling_strategy": _extract_milling_strategy_spec_from_operation(operation),
        "approach": build_approach_spec(
            enabled=_safe_bool(_text(operation, "./{*}Approach/{*}IsEnabled"), False),
            approach_type=_text(operation, "./{*}Approach/{*}ApproachType", "Line"),
            mode=_text(operation, "./{*}Approach/{*}ApproachMode", "Down"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Approach/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Approach/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Approach/{*}ApproachArcSide", "Automatic"),
        ),
        "retract": build_retract_spec(
            enabled=_safe_bool(_text(operation, "./{*}Retract/{*}IsEnabled"), False),
            retract_type=_text(operation, "./{*}Retract/{*}RetractType", "Line"),
            mode=_text(operation, "./{*}Retract/{*}RetractMode", "Up"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Retract/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Retract/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Retract/{*}RetractArcSide", "Automatic"),
            overlap=_safe_float(_text(operation, "./{*}Retract/{*}OverLap"), 0.0),
        ),
        "geometry_serialization": _raw_text(geometry, "./{*}_serializationGeometryDescription"),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_line_milling_spec(
    line_milling: LineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedLineMillingSpec:
    normalized_line_milling = _normalize_line_milling_spec(line_milling)
    if source_pgmx_path is None:
        return _HydratedLineMillingSpec(spec=normalized_line_milling)
    template = _extract_line_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_serialization(template, normalized_line_milling):
        return _HydratedLineMillingSpec(spec=normalized_line_milling)
    return _HydratedLineMillingSpec(
        spec=normalized_line_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_serialization=str(template["geometry_serialization"]),
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def _hydrate_slot_milling_spec(
    slot_milling: SlotMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedSlotMillingSpec:
    del source_pgmx_path
    return _HydratedSlotMillingSpec(spec=_normalize_slot_milling_spec(slot_milling))


def _extract_polyline_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomCompositeCurve" in _xsi_type(node)
        ),
        None,
    )
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "GeneralProfileFeature" in _xsi_type(node)
        ),
        None,
    )
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado por polilinea compatible.")

    def extract_composite_curve(node: ET.Element) -> _CurveSpec:
        return _composite_curve_spec(
            [member.text or "" for member in node.findall("./{*}_serializingMembers/{*}string")],
            [(key.text or "").strip() for key in node.findall("./{*}_serializingKeys/{*}unsignedInt")],
        )

    def extract_toolpath_curve(toolpath: ET.Element) -> _CurveSpec:
        basic_curve = toolpath.find("./{*}BasicCurve")
        curve_type = _xsi_type(basic_curve)
        if "GeomCompositeCurve" in curve_type:
            return extract_composite_curve(basic_curve)
        return _trimmed_curve_spec(_raw_text(basic_curve, "./{*}_serializationGeometryDescription"))

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    depth_variable_name = _workpiece_depth_name(workpiece)
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): extract_toolpath_curve(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
    }
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id

    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(
            feature,
            operation,
            matching_expressions,
            depth_variable_name,
        ),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "milling_strategy": _extract_milling_strategy_spec_from_operation(operation),
        "approach": build_approach_spec(
            enabled=_safe_bool(_text(operation, "./{*}Approach/{*}IsEnabled"), False),
            approach_type=_text(operation, "./{*}Approach/{*}ApproachType", "Line"),
            mode=_text(operation, "./{*}Approach/{*}ApproachMode", "Down"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Approach/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Approach/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Approach/{*}ApproachArcSide", "Automatic"),
        ),
        "retract": build_retract_spec(
            enabled=_safe_bool(_text(operation, "./{*}Retract/{*}IsEnabled"), False),
            retract_type=_text(operation, "./{*}Retract/{*}RetractType", "Line"),
            mode=_text(operation, "./{*}Retract/{*}RetractMode", "Up"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Retract/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Retract/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Retract/{*}RetractArcSide", "Automatic"),
            overlap=_safe_float(_text(operation, "./{*}Retract/{*}OverLap"), 0.0),
        ),
        "geometry_curve": extract_composite_curve(geometry),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_polyline_milling_spec(
    polyline_milling: PolylineMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedPolylineMillingSpec:
    normalized_polyline_milling = _normalize_polyline_milling_spec(polyline_milling)
    if source_pgmx_path is None:
        return _HydratedPolylineMillingSpec(spec=normalized_polyline_milling)
    template = _extract_polyline_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_polyline_serialization(template, normalized_polyline_milling):
        return _HydratedPolylineMillingSpec(spec=normalized_polyline_milling)
    return _HydratedPolylineMillingSpec(
        spec=normalized_polyline_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_curve=template.get("geometry_curve") if isinstance(template.get("geometry_curve"), _CurveSpec) else None,
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def _extract_circle_milling_template(source_pgmx_path: Path) -> dict[str, object]:
    root, _, _ = _load_pgmx_container(source_pgmx_path)

    geometry = next(
        (
            node
            for node in root.findall("./{*}Geometries/{*}GeomGeometry")
            if "GeomCircle" in _xsi_type(node)
        ),
        None,
    )
    geometry_id_text = _text(geometry, "./{*}Key/{*}ID") if geometry is not None else ""
    feature = next(
        (
            node
            for node in root.findall("./{*}Features/{*}ManufacturingFeature")
            if "GeneralProfileFeature" in _xsi_type(node)
            and _text(node, "./{*}GeometryID/{*}ID") == geometry_id_text
        ),
        None,
    )
    operation_id_text = _text(feature, "./{*}OperationIDs/{*}UtilityObject/{*}ID") if feature is not None else ""
    operation = next(
        (
            node
            for node in root.findall("./{*}Operations/{*}Operation")
            if "BottomAndSideFinishMilling" in _xsi_type(node)
            and _text(node, "./{*}Key/{*}ID") == operation_id_text
        ),
        None,
    )
    if geometry is None or feature is None or operation is None:
        raise ValueError(f"El archivo '{source_pgmx_path}' no contiene una plantilla de fresado circular compatible.")

    def extract_toolpath_curve(toolpath: ET.Element) -> _CurveSpec:
        basic_curve = toolpath.find("./{*}BasicCurve")
        curve_type = _xsi_type(basic_curve)
        if "GeomCompositeCurve" in curve_type:
            return _composite_curve_spec(
                [member.text or "" for member in basic_curve.findall("./{*}_serializingMembers/{*}string")],
                [(key.text or "").strip() for key in basic_curve.findall("./{*}_serializingKeys/{*}unsignedInt")],
            )
        if "GeomCircle" in curve_type:
            return _circle_curve_spec(_raw_text(basic_curve, "./{*}_serializationGeometryDescription"))
        return _trimmed_curve_spec(_raw_text(basic_curve, "./{*}_serializationGeometryDescription"))

    geometry_id = int(_text(geometry, "./{*}Key/{*}ID", "0") or "0")
    feature_id = _text(feature, "./{*}Key/{*}ID")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    depth_variable_name = _workpiece_depth_name(workpiece)
    toolpath_by_type = {
        _text(toolpath, "./{*}Type"): extract_toolpath_curve(toolpath)
        for toolpath in operation.findall("./{*}ToolpathList/{*}Toolpath")
    }
    matching_expressions = [
        node
        for node in root.findall("./{*}Expressions/{*}Expression")
        if _text(node, "./{*}ReferencedObject/{*}ID") == feature_id
    ]
    expression_ids = [int(_text(node, "./{*}Key/{*}ID", "0") or "0") for node in matching_expressions]
    preferred_start = min([geometry_id] + expression_ids) if expression_ids else geometry_id

    return {
        "preferred_id_start": preferred_start,
        "depth_spec": _extract_depth_spec_from_template(
            feature,
            operation,
            matching_expressions,
            depth_variable_name,
        ),
        "side_of_feature": _normalize_side_of_feature(_text(feature, "./{*}SideOfFeature", "Center")),
        "tool_width": float(_text(feature, "./{*}SweptShape/{*}Width", "0") or "0"),
        "tool_id": _text(operation, "./{*}ToolKey/{*}ID"),
        "tool_name": _text(operation, "./{*}ToolKey/{*}Name"),
        "milling_strategy": _extract_milling_strategy_spec_from_operation(operation),
        "approach": build_approach_spec(
            enabled=_safe_bool(_text(operation, "./{*}Approach/{*}IsEnabled"), False),
            approach_type=_text(operation, "./{*}Approach/{*}ApproachType", "Line"),
            mode=_text(operation, "./{*}Approach/{*}ApproachMode", "Down"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Approach/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Approach/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Approach/{*}ApproachArcSide", "Automatic"),
        ),
        "retract": build_retract_spec(
            enabled=_safe_bool(_text(operation, "./{*}Retract/{*}IsEnabled"), False),
            retract_type=_text(operation, "./{*}Retract/{*}RetractType", "Line"),
            mode=_text(operation, "./{*}Retract/{*}RetractMode", "Up"),
            radius_multiplier=_safe_float(_text(operation, "./{*}Retract/{*}RadiusMultiplier"), 1.2),
            speed=_safe_float(_text(operation, "./{*}Retract/{*}Speed"), 0.0),
            arc_side=_text(operation, "./{*}Retract/{*}RetractArcSide", "Automatic"),
            overlap=_safe_float(_text(operation, "./{*}Retract/{*}OverLap"), 0.0),
        ),
        "geometry_curve": _circle_curve_spec(_raw_text(geometry, "./{*}_serializationGeometryDescription")),
        "approach_curve": toolpath_by_type.get("Approach"),
        "trajectory_curve": toolpath_by_type.get("TrajectoryPath"),
        "lift_curve": toolpath_by_type.get("Lift"),
    }


def _hydrate_circle_milling_spec(
    circle_milling: CircleMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedCircleMillingSpec:
    normalized_circle_milling = _normalize_circle_milling_spec(circle_milling)
    if source_pgmx_path is None:
        return _HydratedCircleMillingSpec(spec=normalized_circle_milling)
    template = _extract_circle_milling_template(source_pgmx_path)
    if not _can_hydrate_exact_circle_serialization(template, normalized_circle_milling):
        return _HydratedCircleMillingSpec(spec=normalized_circle_milling)
    return _HydratedCircleMillingSpec(
        spec=normalized_circle_milling,
        preferred_id_start=int(template["preferred_id_start"]),
        geometry_curve=template.get("geometry_curve") if isinstance(template.get("geometry_curve"), _CurveSpec) else None,
        approach_curve=template.get("approach_curve") if isinstance(template.get("approach_curve"), _CurveSpec) else None,
        trajectory_curve=template.get("trajectory_curve") if isinstance(template.get("trajectory_curve"), _CurveSpec) else None,
        lift_curve=template.get("lift_curve") if isinstance(template.get("lift_curve"), _CurveSpec) else None,
    )


def _hydrate_squaring_milling_spec(
    squaring_milling: SquaringMillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedSquaringMillingSpec:
    del source_pgmx_path
    return _HydratedSquaringMillingSpec(spec=_normalize_squaring_milling_spec(squaring_milling))


def _hydrate_drilling_spec(
    drilling: DrillingSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedDrillingSpec:
    del source_pgmx_path
    normalized_drilling = _normalize_drilling_spec(drilling)
    tool_catalog = _load_tool_catalog()
    resolved_tool_id, resolved_tool_name, resolved_tool_object_type = _resolve_drilling_tool(
        normalized_drilling,
        tool_catalog,
    )
    return _HydratedDrillingSpec(
        spec=normalized_drilling,
        resolved_tool_id=resolved_tool_id,
        resolved_tool_name=resolved_tool_name,
        resolved_tool_object_type=resolved_tool_object_type,
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


def _build_point_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    point_x: float,
    point_y: float,
    point_z: float = 0.0,
) -> ET.Element:
    geometry = ET.Element(
        _qname(GEOMETRY_NS, "GeomGeometry"),
        {f"{{{XSI_NS}}}type": "a:GeomCartesianPoint"},
    )
    _set_xmlns(geometry, "a", GEOMETRY_NS)
    _append_key(geometry, geometry_id, "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint")
    _append_blank_name(geometry)
    _append_node(geometry, GEOMETRY_NS, "IsAbsolute", "false")
    _append_object_ref(
        geometry,
        GEOMETRY_NS,
        "PlaneID",
        plane_id,
        plane_object_type,
    )
    _append_node(geometry, GEOMETRY_NS, "_x", _compact_number(point_x))
    _append_node(geometry, GEOMETRY_NS, "_y", _compact_number(point_y))
    _append_node(geometry, GEOMETRY_NS, "_z", _compact_number(point_z))
    return geometry


def _build_line_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    spec: _HydratedLineMillingSpec,
) -> ET.Element:
    return _build_geometry_from_curve_spec(
        geometry_id,
        plane_id,
        plane_object_type,
        _trimmed_curve_spec(
            spec.geometry_serialization or _build_line_description(spec.start_x, spec.start_y, spec.end_x, spec.end_y),
        ),
    )


def _build_polyline_geometry(
    geometry_id: str,
    plane_id: str,
    plane_object_type: str,
    curve_spec: _CurveSpec,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    return _build_geometry_from_curve_spec(
        geometry_id,
        plane_id,
        plane_object_type,
        curve_spec,
        generated_member_keys=generated_member_keys,
    )


def _build_profile_feature(
    state: PgmxState,
    spec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    geometry_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:GeneralProfileFeature"},
    )
    _set_xmlns(feature, "a", MILLING_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        geometry_object_type,
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _feature_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", MILLING_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    end_conditions = _append_node(feature, PGMX_NS, "EndConditions")
    slot_end_a = _append_node(
        end_conditions,
        MILLING_NS,
        "SlotEndType",
        attrib={f"{{{XSI_NS}}}type": "a:RadiusedSlotEndType"},
    )
    slot_end_b = _append_node(
        end_conditions,
        MILLING_NS,
        "SlotEndType",
        attrib={f"{{{XSI_NS}}}type": "a:RadiusedSlotEndType"},
    )
    _set_xmlns(slot_end_a, "a", MILLING_NS)
    _set_xmlns(slot_end_b, "a", MILLING_NS)
    _append_node(feature, PGMX_NS, "IsGeomSameDirection", "true")
    _append_node(feature, PGMX_NS, "IsPrecise", "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", "Left")
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", "0")
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", "0")
    _append_node(feature, PGMX_NS, "SideOfFeature", spec.side_of_feature)
    _append_node(feature, PGMX_NS, "SideOffset", "0")
    swept_shape = _append_node(
        feature,
        PGMX_NS,
        "SweptShape",
        attrib={f"{{{XSI_NS}}}type": "a:SquareUProfile"},
    )
    _set_xmlns(swept_shape, "a", MILLING_NS)
    swept_shape.append(_build_identity_profile_placement())
    _append_node(swept_shape, MILLING_NS, "FirstAngle", "0")
    _append_node(swept_shape, MILLING_NS, "FirstRadius", "0")
    _append_node(swept_shape, MILLING_NS, "SecondAngle", "0")
    _append_node(swept_shape, MILLING_NS, "SecondRadius", "0")
    _append_node(swept_shape, MILLING_NS, "Width", _compact_number(spec.tool_width))
    return feature


def _build_slot_side_feature(
    state: PgmxState,
    spec: _HydratedSlotMillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:SlotSide"},
    )
    _set_xmlns(feature, "a", MILLING_NS)
    _append_key(feature, feature_id, "ScmGroup.XCam.MachiningDataModel.Milling.SlotSide")
    _append_blank_name(feature).text = spec.feature_name
    _append_object_ref(
        feature,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
    )
    operation_ids = _append_node(feature, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
    )
    _append_object_ref(feature, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _feature_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", MILLING_NS)
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    end_conditions = _append_node(feature, PGMX_NS, "EndConditions")
    for _ in range(2):
        slot_end = _append_node(
            end_conditions,
            MILLING_NS,
            "SlotEndType",
            attrib={f"{{{XSI_NS}}}type": "a:WoodruffSlotEndType"},
        )
        _set_xmlns(slot_end, "a", MILLING_NS)
        _append_node(slot_end, MILLING_NS, "Radius", _compact_number(spec.end_radius))
    _append_node(feature, PGMX_NS, "IsGeomSameDirection", "true")
    _append_node(feature, PGMX_NS, "IsPrecise", "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", spec.material_position)
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", "0")
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", "0")
    _append_node(feature, PGMX_NS, "SideOfFeature", spec.side_of_feature)
    _append_node(feature, PGMX_NS, "SideOffset", _compact_number(spec.side_offset))
    swept_shape = _append_node(
        feature,
        PGMX_NS,
        "SweptShape",
        attrib={f"{{{XSI_NS}}}type": "a:SquareUProfile"},
    )
    _set_xmlns(swept_shape, "a", MILLING_NS)
    swept_shape.append(_build_identity_profile_placement())
    _append_node(swept_shape, MILLING_NS, "FirstAngle", "0")
    _append_node(swept_shape, MILLING_NS, "FirstRadius", "0")
    _append_node(swept_shape, MILLING_NS, "SecondAngle", "0")
    _append_node(swept_shape, MILLING_NS, "SecondRadius", "0")
    _append_node(swept_shape, MILLING_NS, "Width", _compact_number(spec.tool_width))
    _append_node(feature, PGMX_NS, "Angle", str(float(spec.slot_angle)))
    return feature


def _build_drilling_feature(
    state: PgmxState,
    spec: _HydratedDrillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
) -> ET.Element:
    feature = ET.Element(
        _qname(PGMX_NS, "ManufacturingFeature"),
        {f"{{{XSI_NS}}}type": "a:RoundHole"},
    )
    _set_xmlns(feature, "a", DRILLING_NS)
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
    bottom_condition = _append_node(
        feature,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": _drilling_bottom_condition_type(spec)},
    )
    _set_xmlns(bottom_condition, "a", DRILLING_NS)
    if _drilling_bottom_condition_type(spec) == "a:ConicalHoleBottom":
        _append_node(bottom_condition, DRILLING_NS, "TipAngle", "0")
        _append_node(bottom_condition, DRILLING_NS, "TipRadius", "0")
    depth = _append_node(feature, PGMX_NS, "Depth")
    depth_value = _compact_number(_drilling_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    _append_node(feature, DRILLING_NS, "Diameter", _compact_number(spec.diameter))
    _append_node(feature, DRILLING_NS, "TaperHeight", "0")
    return feature


def _drilling_pattern_bottom_condition_type(spec: _HydratedDrillingPatternSpec) -> str:
    return _drilling_bottom_condition_type(spec.base_drilling).replace("a:", "b:", 1)


def _append_drilling_feature_payload(
    parent: ET.Element,
    state: PgmxState,
    spec: _HydratedDrillingSpec,
    feature_id: str,
    geometry_id: str,
    operation_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    *,
    bottom_condition_type: Optional[str] = None,
) -> None:
    _append_key(parent, feature_id, "ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole")
    _append_blank_name(parent).text = spec.feature_name
    _append_object_ref(
        parent,
        PGMX_NS,
        "GeometryID",
        geometry_id,
        "ScmGroup.XCam.MachiningDataModel.Geometry.GeomCartesianPoint",
    )
    operation_ids = _append_node(parent, PGMX_NS, "OperationIDs")
    _append_reference_key(
        operation_ids,
        operation_id,
        "ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
    )
    _append_object_ref(parent, PGMX_NS, "WorkpieceID", workpiece_id, workpiece_object_type)
    effective_bottom_condition = bottom_condition_type or _drilling_bottom_condition_type(spec)
    bottom_condition = _append_node(
        parent,
        PGMX_NS,
        "BottomCondition",
        attrib={f"{{{XSI_NS}}}type": effective_bottom_condition},
    )
    if effective_bottom_condition.startswith("b:"):
        _set_xmlns(bottom_condition, "b", DRILLING_NS)
    else:
        _set_xmlns(bottom_condition, "a", DRILLING_NS)
    if "ThroughHoleBottom" in effective_bottom_condition:
        _append_node(bottom_condition, DRILLING_NS, "IsFlat", "false")
    if "ConicalHoleBottom" in effective_bottom_condition:
        _append_node(bottom_condition, DRILLING_NS, "TipAngle", "0")
        _append_node(bottom_condition, DRILLING_NS, "TipRadius", "0")
    depth = _append_node(parent, PGMX_NS, "Depth")
    depth_value = _compact_number(_drilling_feature_depth_value(state, spec))
    _append_node(depth, PGMX_NS, "EndDepth", depth_value)
    _append_node(depth, PGMX_NS, "StartDepth", depth_value)
    _append_node(parent, DRILLING_NS, "Diameter", _compact_number(spec.diameter))
    _append_node(parent, DRILLING_NS, "TaperHeight", "0")


def _build_drilling_pattern_feature(
    state: PgmxState,
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


def _build_drilling_operation(
    state: PgmxState,
    spec: _HydratedDrillingSpec,
    operation_id: str,
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:DrillingOperation"},
    )
    _set_xmlns(operation, "a", DRILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation")
    _append_blank_name(operation)
    _append_node(operation, PGMX_NS, "ActivateCNCCorrection", "true")
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)

    entry_point, direction = _drilling_entry_point_and_direction(state, spec)
    total_depth = _drilling_total_depth(state, spec)
    clearance_point = (
        entry_point[0] - (direction[0] * spec.security_plane),
        entry_point[1] - (direction[1] * spec.security_plane),
        entry_point[2] - (direction[2] * spec.security_plane),
    )
    cut_point = (
        entry_point[0] + (direction[0] * total_depth),
        entry_point[1] + (direction[1] * total_depth),
        entry_point[2] + (direction[2] * total_depth),
    )
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            _trimmed_curve_spec(_build_toolpath_description(clearance_point, entry_point)),
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "TrajectoryPath",
            _trimmed_curve_spec(_build_toolpath_description(entry_point, cut_point)),
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            _trimmed_curve_spec(_build_toolpath_description(cut_point, clearance_point)),
        )
    )
    _append_node(operation, PGMX_NS, "ToolpathPriority", "true")
    _append_node(operation, PGMX_NS, "AdditionalToolKeys", "")
    _append_node(operation, PGMX_NS, "ApproachSecurityPlane", _compact_number(spec.security_plane))
    _append_node(operation, PGMX_NS, "Head", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(operation, PGMX_NS, "HeadRotation", "0")
    _append_node(operation, PGMX_NS, "MachineFunctions", "")
    _append_node(operation, PGMX_NS, "RetractSecurityPlane", _compact_number(spec.security_plane))
    operation.append(_build_start_point(0.0, 0.0, 0.0))
    technology = _append_node(
        operation,
        PGMX_NS,
        "Technology",
        attrib={f"{{{XSI_NS}}}type": "MillingTechnology"},
    )
    _append_node(technology, PGMX_NS, "Feedrate", "0")
    _append_node(technology, PGMX_NS, "CutSpeed", "0")
    _append_node(technology, PGMX_NS, "Spindle", "0")
    _append_object_ref(
        operation,
        PGMX_NS,
        "ToolKey",
        spec.tool_id,
        spec.tool_object_type,
        include_name=True,
        name_text=spec.tool_name,
    )
    _append_node(operation, PGMX_NS, "OvercutLength", "0")
    _append_node(operation, DRILLING_NS, "CuttingDepth", "0")
    machining_strategy = _append_node(
        operation,
        DRILLING_NS,
        "MachiningStrategy",
        attrib={f"{{{XSI_NS}}}type": "b:SingleStepDrilling"},
    )
    _set_xmlns(machining_strategy, "b", BASE_MODEL_NS)
    return operation


def _build_toolpath(
    toolpath_type: str,
    curve_spec: _CurveSpec,
    *,
    generated_member_keys: Sequence[str] = (),
) -> ET.Element:
    toolpath = ET.Element(
        _qname(BASE_MODEL_NS, "Toolpath"),
        {f"{{{XSI_NS}}}type": "b:CutterLocationTrajectory"},
    )
    _set_xmlns(toolpath, "b", BASE_MODEL_NS)
    _append_node(toolpath, BASE_MODEL_NS, "Attributes", "")
    _append_node(toolpath, BASE_MODEL_NS, "Priority", "true")
    _append_node(toolpath, BASE_MODEL_NS, "Type", toolpath_type)
    _append_node(toolpath, BASE_MODEL_NS, "Direction", "true")
    toolpath.append(_build_curve_holder("BasicCurve", curve_spec, generated_member_keys=generated_member_keys))
    toolpath.append(_build_vector_holder("ToolAxis", 1.0, 0.0, 0.0))
    return toolpath


def _build_generated_approach_curve(
    state: PgmxState,
    spec,
    toolpath_start: tuple[float, float, float],
    toolpath_end: tuple[float, float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    approach = _normalize_approach_spec(spec.approach)
    clearance_z = state.depth + spec.security_plane
    cut_z = toolpath_start[2]
    direction_x, direction_y = _resolve_toolpath_direction(
        (toolpath_start[0], toolpath_start[1]),
        (toolpath_end[0], toolpath_end[1]),
        direction=direction,
    )
    if not approach.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_start[0], toolpath_start[1], clearance_z, cut_z)

    if approach.approach_type == "Line" and approach.mode == "Quote":
        pre_entry_distance = _linear_lead_distance(spec.tool_width, approach.radius_multiplier)
        pre_entry_x = toolpath_start[0] - (direction_x * pre_entry_distance)
        pre_entry_y = toolpath_start[1] - (direction_y * pre_entry_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, clearance_z),
                    (pre_entry_x, pre_entry_y, cut_z),
                ),
                _build_toolpath_description(
                    (pre_entry_x, pre_entry_y, cut_z),
                    (toolpath_start[0], toolpath_start[1], cut_z),
                ),
            ]
        )

    if approach.approach_type == "Line" and approach.mode == "Down":
        return _build_down_line_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Quote":
        return _build_quote_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=approach.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    if approach.approach_type == "Arc" and approach.mode == "Down":
        return _build_down_arc_entry_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            entry_point=toolpath_start,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=approach.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un approach habilitado con "
        f"type={approach.approach_type} y mode={approach.mode}."
    )


def _build_generated_approach_curve_for_profile(
    state: PgmxState,
    spec,
    toolpath_profile: GeometryProfileSpec,
) -> _CurveSpec:
    """Construye el approach a partir de una trayectoria efectiva y su tangente de entrada."""

    toolpath_start, toolpath_end = _profile_endpoint_points_3d(toolpath_profile)
    _, _, start_direction, _ = _profile_entry_exit_context(toolpath_profile)
    return _build_generated_approach_curve(
        state,
        spec,
        toolpath_start,
        toolpath_end,
        direction=start_direction,
    )


def _build_generated_lift_curve(
    state: PgmxState,
    spec,
    toolpath_start: tuple[float, float, float],
    toolpath_end: tuple[float, float, float],
    direction: Optional[tuple[float, float]] = None,
) -> _CurveSpec:
    retract = _normalize_retract_spec(spec.retract)
    clearance_z = state.depth + spec.security_plane
    cut_z = toolpath_end[2]
    direction_x, direction_y = _resolve_toolpath_direction(
        (toolpath_start[0], toolpath_start[1]),
        (toolpath_end[0], toolpath_end[1]),
        direction=direction,
    )
    if not retract.is_enabled:
        return _build_vertical_toolpath_curve(toolpath_end[0], toolpath_end[1], cut_z, clearance_z)

    if retract.retract_type == "Line" and retract.mode == "Quote":
        post_exit_distance = (spec.tool_width / 2.0) * retract.radius_multiplier
        post_exit_x = toolpath_end[0] + (direction_x * post_exit_distance)
        post_exit_y = toolpath_end[1] + (direction_y * post_exit_distance)
        return _composite_curve_spec(
            [
                _build_toolpath_description(
                    (toolpath_end[0], toolpath_end[1], cut_z),
                    (post_exit_x, post_exit_y, cut_z),
                ),
                _build_toolpath_description(
                    (post_exit_x, post_exit_y, cut_z),
                    (post_exit_x, post_exit_y, clearance_z),
                ),
            ]
        )

    if retract.retract_type == "Line" and retract.mode == "Up":
        return _build_up_line_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Quote":
        return _build_quote_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            side_of_feature=spec.side_of_feature,
            arc_side=retract.arc_side,
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    if retract.retract_type == "Arc" and retract.mode == "Up":
        return _build_up_arc_exit_curve(
            clearance_z=clearance_z,
            cut_z=cut_z,
            exit_point=toolpath_end,
            direction=(direction_x, direction_y),
            tool_width=spec.tool_width,
            radius_multiplier=retract.radius_multiplier,
        )

    raise ValueError(
        "No hay una sintesis generica validada para un retract habilitado con "
        f"type={retract.retract_type} y mode={retract.mode}."
    )


def _build_generated_lift_curve_for_profile(
    state: PgmxState,
    spec,
    toolpath_profile: GeometryProfileSpec,
) -> _CurveSpec:
    """Construye el lift a partir de una trayectoria efectiva y su tangente de salida."""

    toolpath_start, toolpath_end = _profile_endpoint_points_3d(toolpath_profile)
    _, _, _, end_direction = _profile_entry_exit_context(toolpath_profile)
    return _build_generated_lift_curve(
        state,
        spec,
        toolpath_start,
        toolpath_end,
        direction=end_direction,
    )


def _should_activate_cnc_correction(spec) -> bool:
    return not _strategy_is_multilevel(spec.milling_strategy)


def _spec_uses_closed_profile(spec) -> bool:
    if isinstance(spec, (_HydratedCircleMillingSpec, CircleMillingSpec, _HydratedSquaringMillingSpec, SquaringMillingSpec)):
        return True
    points = getattr(spec, "points", None)
    if points is None:
        return False
    return _is_closed_polyline_points(points)


def _build_milling_strategy_node(spec) -> ET.Element:
    strategy = _normalize_milling_strategy_spec(spec.milling_strategy)
    if strategy is None:
        return ET.Element(_qname(PGMX_NS, "MachiningStrategy"), {f"{{{XSI_NS}}}nil": "true"})
    if isinstance(strategy, ContourParallelMillingStrategySpec):
        raise NotImplementedError(
            "ContourParallelMillingStrategySpec esta soportada solo para lectura; "
            "la sintesis de Vaciado/ClosedPocket todavia no esta implementada."
        )

    if isinstance(strategy, UnidirectionalMillingStrategySpec):
        strategy_type = "b:UnidirectionalMilling"
        stroke_connection_strategy = _serialize_unidirectional_connection_mode(
            _resolve_unidirectional_connection_mode(
                strategy,
                is_closed_profile=_spec_uses_closed_profile(spec),
            )
        )
    elif isinstance(strategy, BidirectionalMillingStrategySpec):
        strategy_type = "b:BidirectionalMilling"
        stroke_connection_strategy = "Straghtline"
    else:
        strategy_type = "b:HelicMilling"
        stroke_connection_strategy = "Straghtline"

    node = ET.Element(
        _qname(PGMX_NS, "MachiningStrategy"),
        {f"{{{XSI_NS}}}type": strategy_type},
    )
    _set_xmlns(node, "b", STRATEGY_NS)
    if isinstance(strategy, HelicalMillingStrategySpec):
        _append_node(node, PGMX_NS, "AllowMultiplePasses", "false")
    else:
        _append_node(node, PGMX_NS, "AllowMultiplePasses", "true" if strategy.allow_multiple_passes else "false")
    _append_node(node, PGMX_NS, "Overlap", "0")
    if isinstance(strategy, HelicalMillingStrategySpec):
        _append_node(node, STRATEGY_NS, "AllowsFinishCutting", "true" if strategy.allows_finish_cutting else "false")
    _append_node(node, STRATEGY_NS, "AxialCuttingDepth", _compact_number(strategy.axial_cutting_depth))
    _append_node(node, STRATEGY_NS, "AxialFinishCuttingDepth", _compact_number(strategy.axial_finish_cutting_depth))
    _append_node(node, STRATEGY_NS, "Cutmode", "Climb")
    _append_node(node, STRATEGY_NS, "RadialCuttingDepth", "0")
    _append_node(node, STRATEGY_NS, "RadialFinishCuttingDepth", "0")
    _append_node(node, STRATEGY_NS, "StrokeConnectionStrategy", stroke_connection_strategy)
    return node


def _build_line_operation(
    state: PgmxState,
    spec,
    operation_id: str,
    approach_curve: _CurveSpec,
    approach_curve_member_keys: Sequence[str] = (),
    lift_curve: Optional[_CurveSpec] = None,
    lift_curve_member_keys: Sequence[str] = (),
    trajectory_curve: Optional[_CurveSpec] = None,
    trajectory_curve_member_keys: Sequence[str] = (),
    toolpath_start: Optional[tuple[float, float]] = None,
    toolpath_end: Optional[tuple[float, float]] = None,
) -> ET.Element:
    operation = ET.Element(
        _qname(PGMX_NS, "Operation"),
        {f"{{{XSI_NS}}}type": "a:BottomAndSideFinishMilling"},
    )
    _set_xmlns(operation, "a", MILLING_NS)
    _append_key(operation, operation_id, "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling")
    _append_blank_name(operation)
    _append_node(
        operation,
        PGMX_NS,
        "ActivateCNCCorrection",
        "true" if _should_activate_cnc_correction(spec) else "false",
    )
    _append_node(operation, PGMX_NS, "Attributes", "")
    _append_node(operation, PGMX_NS, "ToolDirection", attrib={f"{{{XSI_NS}}}nil": "true"})
    toolpath_list = _append_node(operation, PGMX_NS, "ToolpathList")
    _set_xmlns(toolpath_list, "b", BASE_MODEL_NS)
    clearance_z = state.depth + spec.security_plane
    cut_z = _toolpath_cut_z(state, spec)
    if toolpath_start is None or toolpath_end is None:
        (toolpath_start_x, toolpath_start_y), (toolpath_end_x, toolpath_end_y) = _offset_line_for_toolpath(spec)
    else:
        toolpath_start_x, toolpath_start_y = toolpath_start
        toolpath_end_x, toolpath_end_y = toolpath_end
    toolpath_list.append(
        _build_toolpath(
            "Approach",
            approach_curve,
            generated_member_keys=approach_curve_member_keys,
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "TrajectoryPath",
            trajectory_curve
            or spec.trajectory_curve
            or _trimmed_curve_spec(
                _build_toolpath_description(
                    (toolpath_start_x, toolpath_start_y, cut_z),
                    (toolpath_end_x, toolpath_end_y, cut_z),
                )
            ),
            generated_member_keys=trajectory_curve_member_keys,
        )
    )
    toolpath_list.append(
        _build_toolpath(
            "Lift",
            lift_curve
            or spec.lift_curve
            or _trimmed_curve_spec(
                _build_toolpath_description(
                    (toolpath_end_x, toolpath_end_y, cut_z),
                    (toolpath_end_x, toolpath_end_y, clearance_z),
                )
            ),
            generated_member_keys=lift_curve_member_keys,
        )
    )
    _append_node(operation, PGMX_NS, "ToolpathPriority", "true")
    _append_node(operation, PGMX_NS, "AdditionalToolKeys", "")
    _append_node(operation, PGMX_NS, "ApproachSecurityPlane", _compact_number(spec.security_plane))
    _append_node(operation, PGMX_NS, "Head", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(operation, PGMX_NS, "HeadRotation", "0")
    _append_node(operation, PGMX_NS, "MachineFunctions", "")
    _append_node(operation, PGMX_NS, "RetractSecurityPlane", _compact_number(spec.security_plane))
    operation.append(_build_start_point(0.0, 0.0, 0.0))
    technology = _append_node(
        operation,
        PGMX_NS,
        "Technology",
        attrib={f"{{{XSI_NS}}}type": "MillingTechnology"},
    )
    _append_node(technology, PGMX_NS, "Feedrate", "0")
    _append_node(technology, PGMX_NS, "CutSpeed", "0")
    _append_node(technology, PGMX_NS, "Spindle", "0")
    _append_object_ref(
        operation,
        PGMX_NS,
        "ToolKey",
        spec.tool_id,
        "ScmGroup.XCam.ToolDataModel.Tool.CuttingTool",
        include_name=True,
        name_text=spec.tool_name,
    )
    _append_node(operation, PGMX_NS, "OvercutLength", _compact_number(_operation_overcut_length(spec)))
    approach = _append_node(
        operation,
        PGMX_NS,
        "Approach",
        attrib={f"{{{XSI_NS}}}type": "b:BaseApproachStrategy"},
    )
    _set_xmlns(approach, "b", STRATEGY_NS)
    _append_node(approach, STRATEGY_NS, "ApproachArcSide", spec.approach.arc_side)
    _append_node(approach, STRATEGY_NS, "ApproachMode", spec.approach.mode)
    _append_node(approach, STRATEGY_NS, "ApproachType", spec.approach.approach_type)
    _append_node(approach, STRATEGY_NS, "IsEnabled", "true" if spec.approach.is_enabled else "false")
    _append_node(approach, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.approach.radius_multiplier))
    _append_node(approach, STRATEGY_NS, "Speed", _compact_number(spec.approach.speed))
    retract = _append_node(
        operation,
        PGMX_NS,
        "Retract",
        attrib={f"{{{XSI_NS}}}type": "b:BaseRetractStrategy"},
    )
    _set_xmlns(retract, "b", STRATEGY_NS)
    _append_node(retract, STRATEGY_NS, "IsEnabled", "true" if spec.retract.is_enabled else "false")
    _append_node(retract, STRATEGY_NS, "OverLap", _compact_number(spec.retract.overlap))
    _append_node(retract, STRATEGY_NS, "RadiusMultiplier", _compact_number(spec.retract.radius_multiplier))
    _append_node(retract, STRATEGY_NS, "RetractArcSide", spec.retract.arc_side)
    _append_node(retract, STRATEGY_NS, "RetractMode", spec.retract.mode)
    _append_node(retract, STRATEGY_NS, "RetractType", spec.retract.retract_type)
    _append_node(retract, STRATEGY_NS, "Speed", _compact_number(spec.retract.speed))
    operation.append(_build_milling_strategy_node(spec))
    _append_node(operation, PGMX_NS, "AllowanceBottom", "0")
    _append_node(operation, PGMX_NS, "AllowanceSide", "0")
    return operation


def _build_working_step(
    feature_name: str,
    step_id: str,
    feature_id: str,
    operation_id: str,
    feature_object_type: str = "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature",
    operation_object_type: str = "ScmGroup.XCam.MachiningDataModel.Milling.BottomAndSideFinishMilling",
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "a:MachiningWorkingStep"},
    )
    _set_xmlns(step, "a", PGMX_NS)
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep")
    _append_blank_name(step).text = feature_name
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")
    feature_ref = _append_object_ref(
        step,
        PGMX_NS,
        "ManufacturingFeatureID",
        feature_id,
        feature_object_type,
    )
    operation_ref = _append_object_ref(
        step,
        PGMX_NS,
        "OperationID",
        operation_id,
        operation_object_type,
    )
    _set_xmlns(feature_ref, "b", UTILITY_NS)
    _set_xmlns(operation_ref, "b", UTILITY_NS)
    return step


def _build_xn_step(
    step_id: str,
    workpiece_id: str,
    workpiece_object_type: str,
    spec: XnSpec,
) -> ET.Element:
    step = ET.Element(
        _qname(BASE_MODEL_NS, "Executable"),
        {f"{{{XSI_NS}}}type": "Xn"},
    )
    _append_key(step, step_id, "ScmGroup.XCam.MachiningDataModel.Xn")
    _append_blank_name(step).text = "Xn"
    _append_node(step, BASE_MODEL_NS, "Description", "")
    _append_node(step, BASE_MODEL_NS, "IsEnabled", "true")
    _append_node(step, BASE_MODEL_NS, "Priority", "0")

    if spec.y is None:
        geometry_ref = _append_node(step, BASE_MODEL_NS, "GeometryID")
        _append_node(geometry_ref, UTILITY_NS, "ID", "0")
        _append_node(geometry_ref, UTILITY_NS, "ObjectType", attrib={f"{{{XSI_NS}}}nil": "true"})
        _set_xmlns(geometry_ref, "a", UTILITY_NS)
    else:
        _append_node(step, BASE_MODEL_NS, "GeometryID", attrib={f"{{{XSI_NS}}}nil": "true"})

    workpiece_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "WorkpieceID",
        workpiece_id,
        workpiece_object_type,
    )
    _set_xmlns(workpiece_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "Reference", spec.reference)
    _append_node(step, BASE_MODEL_NS, "Speed", "0")
    _append_node(step, BASE_MODEL_NS, "SpindleEnable", "Off")

    tool_ref = _append_object_ref(
        step,
        BASE_MODEL_NS,
        "Tool",
        "0",
        "System.Object",
        include_name=True,
        name_text="",
    )
    _set_xmlns(tool_ref, "a", UTILITY_NS)

    _append_node(step, BASE_MODEL_NS, "X", _compact_number(spec.x))
    if spec.y is None:
        _append_node(step, BASE_MODEL_NS, "Y", attrib={f"{{{XSI_NS}}}nil": "true"})
    else:
        _append_node(step, BASE_MODEL_NS, "Y", _compact_number(spec.y))
    return step


def _build_depth_expression(
    expression_id: str,
    feature_id: str,
    inner_field_name: str,
    depth_variable_name: str,
    referenced_object_type: str = "ScmGroup.XCam.MachiningDataModel.Milling.GeneralProfileFeature",
) -> ET.Element:
    expression = ET.Element(_qname(PARAMETRIC_NS, "Expression"))
    _append_key(expression, expression_id, "ScmGroup.XCam.MachiningDataModel.Parametrics.Expression")
    _append_blank_name(expression)
    property_node = _append_node(
        expression,
        PARAMETRIC_NS,
        "Property",
        attrib={f"{{{XSI_NS}}}type": "a:CompositeField"},
    )
    _set_xmlns(property_node, "a", PARAMETRIC_NS)
    _append_node(property_node, PARAMETRIC_NS, "Index", "-1")
    _append_node(property_node, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(property_node, PARAMETRIC_NS, "Name", "Depth")
    inner_field = _append_node(property_node, PARAMETRIC_NS, "InnerField")
    _append_node(inner_field, PARAMETRIC_NS, "Index", "-1")
    _append_node(inner_field, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(inner_field, PARAMETRIC_NS, "Name", inner_field_name)
    _append_object_ref(
        expression,
        PARAMETRIC_NS,
        "ReferencedObject",
        feature_id,
        referenced_object_type,
    )
    _append_node(expression, PARAMETRIC_NS, "Value", depth_variable_name)
    return expression


def _build_drilling_pattern_depth_expression(
    expression_id: str,
    feature_id: str,
    inner_field_name: str,
    depth_variable_name: str,
) -> ET.Element:
    expression = ET.Element(_qname(PARAMETRIC_NS, "Expression"))
    _append_key(expression, expression_id, "ScmGroup.XCam.MachiningDataModel.Parametrics.Expression")
    _append_blank_name(expression)
    property_node = _append_node(
        expression,
        PARAMETRIC_NS,
        "Property",
        attrib={f"{{{XSI_NS}}}type": "a:CompositeField"},
    )
    _set_xmlns(property_node, "a", PARAMETRIC_NS)
    _append_node(property_node, PARAMETRIC_NS, "Index", "-1")
    _append_node(property_node, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(property_node, PARAMETRIC_NS, "Name", "BaseFeature")

    depth_field = _append_node(
        property_node,
        PARAMETRIC_NS,
        "InnerField",
        attrib={f"{{{XSI_NS}}}type": "a:CompositeField"},
    )
    _set_xmlns(depth_field, "a", PARAMETRIC_NS)
    _append_node(depth_field, PARAMETRIC_NS, "Index", "-1")
    _append_node(depth_field, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(depth_field, PARAMETRIC_NS, "Name", "Depth")

    final_field = _append_node(depth_field, PARAMETRIC_NS, "InnerField")
    _append_node(final_field, PARAMETRIC_NS, "Index", "-1")
    _append_node(final_field, PARAMETRIC_NS, "Key", attrib={f"{{{XSI_NS}}}nil": "true"})
    _append_node(final_field, PARAMETRIC_NS, "Name", inner_field_name)

    _append_object_ref(
        expression,
        PARAMETRIC_NS,
        "ReferencedObject",
        feature_id,
        "ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
    )
    _append_node(expression, PARAMETRIC_NS, "Value", depth_variable_name)
    return expression


def _append_line_milling(root: ET.Element, state: PgmxState, spec: _HydratedLineMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None
    generated_toolpath_profile = _build_line_toolpath_profile(state, spec)
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    trajectory_curve_member_keys: tuple[str, ...] = ()
    next_generated_aux_id = int(end_expression_id or step_id) + 1
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
        member_count = len(trajectory_curve.member_serializations)
        trajectory_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            "ScmGroup.XCam.MachiningDataModel.Geometry.GeomTrimmedCurve",
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys or trajectory_curve_member_keys,
            toolpath_start=toolpath_start,
            toolpath_end=toolpath_end,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _append_slot_milling(root: ET.Element, state: PgmxState, spec: _HydratedSlotMillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar la ranura.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None
    generated_toolpath_profile = _build_line_toolpath_profile(state, spec)
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec))
    features.append(
        _build_slot_side_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            lift_curve=lift_curve,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys,
            toolpath_start=toolpath_start,
            toolpath_end=toolpath_end,
        )
    )
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.Milling.SlotSide",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _append_curve_profile_milling(
    root: ET.Element,
    state: PgmxState,
    spec,
    generated_geometry_curve: _CurveSpec,
    generated_toolpath_profile: GeometryProfileSpec,
) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el fresado.")

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _workpiece_depth_name(workpiece)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_feature_depth_expressions(spec)

    geometry_member_count = len(generated_geometry_curve.member_serializations)
    reserved_ids = _reserve_ids(
        root,
        geometry_member_count + (6 if uses_depth_expressions else 4),
        spec.preferred_id_start,
    )
    geometry_id = reserved_ids[0]
    generated_geometry_member_keys: tuple[str, ...] = ()
    if generated_geometry_curve.geometry_type == "GeomCompositeCurve" and not generated_geometry_curve.member_keys:
        generated_geometry_member_keys = tuple(reserved_ids[1 : 1 + geometry_member_count])

    operation_index = 1 + geometry_member_count
    operation_id = reserved_ids[operation_index]
    feature_id = reserved_ids[operation_index + 1]
    step_id = reserved_ids[operation_index + 2]
    start_expression_id = reserved_ids[operation_index + 3] if uses_depth_expressions else None
    end_expression_id = reserved_ids[operation_index + 4] if uses_depth_expressions else None

    generated_trajectory_curve = _curve_spec_from_profile_geometry(generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or generated_trajectory_curve
    start_point, end_point, _, _ = _profile_entry_exit_context(generated_toolpath_profile)

    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)

    next_generated_aux_id = int(end_expression_id or step_id) + 1
    trajectory_curve_member_keys: tuple[str, ...] = ()
    if trajectory_curve.geometry_type == "GeomCompositeCurve" and not trajectory_curve.member_keys:
        if trajectory_curve.member_serializations == generated_geometry_curve.member_serializations:
            trajectory_curve_member_keys = generated_geometry_curve.member_keys or generated_geometry_member_keys
        else:
            member_count = len(trajectory_curve.member_serializations)
            trajectory_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
            next_generated_aux_id += member_count

    approach_curve_member_keys: tuple[str, ...] = ()
    if approach_curve.geometry_type == "GeomCompositeCurve" and not approach_curve.member_keys:
        member_count = len(approach_curve.member_serializations)
        approach_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    lift_curve_member_keys: tuple[str, ...] = ()
    if lift_curve.geometry_type == "GeomCompositeCurve" and not lift_curve.member_keys:
        member_count = len(lift_curve.member_serializations)
        lift_curve_member_keys = tuple(str(next_generated_aux_id + offset) for offset in range(member_count))
        next_generated_aux_id += member_count

    geometries.append(
        _build_polyline_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            generated_geometry_curve,
            generated_member_keys=generated_geometry_member_keys,
        )
    )
    features.append(
        _build_profile_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
            _geometry_object_type(generated_geometry_curve.geometry_type),
        )
    )
    operations.append(
        _build_line_operation(
            state,
            spec,
            operation_id,
            approach_curve,
            approach_curve_member_keys=approach_curve_member_keys,
            lift_curve=lift_curve,
            lift_curve_member_keys=lift_curve_member_keys,
            trajectory_curve=trajectory_curve,
            trajectory_curve_member_keys=trajectory_curve.member_keys or trajectory_curve_member_keys,
            toolpath_start=start_point,
            toolpath_end=end_point,
        )
    )
    elements.append(_build_working_step(spec.feature_name, step_id, feature_id, operation_id))
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(_build_depth_expression(start_expression_id, feature_id, "StartDepth", depth_variable_name))
        expressions.append(_build_depth_expression(end_expression_id, feature_id, "EndDepth", depth_variable_name))


def _append_polyline_milling(root: ET.Element, state: PgmxState, spec: _HydratedPolylineMillingSpec) -> None:
    if spec.geometry_curve is not None:
        generated_geometry_curve = spec.geometry_curve
    elif _is_closed_polyline_points(spec.points):
        generated_geometry_curve = _curve_spec_from_profile_geometry(
            _build_closed_polyline_geometry_profile(spec.points, z_value=0.0)
        )
    else:
        generated_geometry_curve = _composite_curve_spec(_build_open_polyline_descriptions(spec.points))
    generated_toolpath_profile = _build_polyline_toolpath_profile(state, spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        generated_geometry_curve,
        generated_toolpath_profile,
    )


def _append_circle_milling(root: ET.Element, state: PgmxState, spec: _HydratedCircleMillingSpec) -> None:
    generated_geometry_curve = spec.geometry_curve or _curve_spec_from_profile_geometry(
        build_circle_geometry_profile(
            spec.center_x,
            spec.center_y,
            spec.radius,
            z_value=0.0,
            winding=spec.winding,
        )
    )
    generated_toolpath_profile = _build_circle_toolpath_profile(state, spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        generated_geometry_curve,
        generated_toolpath_profile,
    )


def _append_squaring_milling(root: ET.Element, state: PgmxState, spec: _HydratedSquaringMillingSpec) -> None:
    generated_geometry_profile = _build_squaring_geometry_profile(state, spec, z_value=0.0)
    generated_toolpath_profile = _build_squaring_toolpath_profile(state, spec)
    _append_curve_profile_milling(
        root,
        state,
        spec,
        spec.geometry_curve or _curve_spec_from_profile_geometry(generated_geometry_profile),
        generated_toolpath_profile,
    )


def _append_drilling(root: ET.Element, state: PgmxState, spec: _HydratedDrillingSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el taladro.")

    _validate_drilling_center(state, spec)
    _drilling_feature_depth_value(state, spec)

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _drilling_axis_variable_name(workpiece, spec.plane_name)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_drilling_depth_expressions(spec)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None

    geometries.append(
        _build_point_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            spec.center_x,
            spec.center_y,
            0.0,
        )
    )
    features.append(
        _build_drilling_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
        )
    )
    operations.append(_build_drilling_operation(state, spec, operation_id))
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            operation_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(
            _build_depth_expression(
                start_expression_id,
                feature_id,
                "StartDepth",
                depth_variable_name,
                referenced_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            )
        )
        expressions.append(
            _build_depth_expression(
                end_expression_id,
                feature_id,
                "EndDepth",
                depth_variable_name,
                referenced_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            )
        )


def _validate_drilling_pattern_center(state: PgmxState, spec: _HydratedDrillingPatternSpec) -> None:
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


def _append_drilling_pattern(root: ET.Element, state: PgmxState, spec: _HydratedDrillingPatternSpec) -> None:
    geometries = root.find("./{*}Geometries")
    features = root.find("./{*}Features")
    operations = root.find("./{*}Operations")
    expressions = root.find("./{*}Expressions")
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if any(node is None for node in (geometries, features, operations, expressions, elements, workpiece)):
        raise ValueError("La plantilla no contiene todas las colecciones requeridas para sintetizar el patron.")

    _validate_drilling_pattern_center(state, spec)
    _drilling_feature_depth_value(state, spec.base_drilling)

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    depth_variable_name = _drilling_axis_variable_name(workpiece, spec.plane_name)
    plane_id, plane_object_type = _find_plane_ref(root, spec.plane_name)
    uses_depth_expressions = _uses_drilling_depth_expressions(spec.base_drilling)
    reserved_ids = _reserve_ids(root, 6 if uses_depth_expressions else 4)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    start_expression_id = reserved_ids[4] if uses_depth_expressions else None
    end_expression_id = reserved_ids[5] if uses_depth_expressions else None

    geometries.append(
        _build_point_geometry(
            geometry_id,
            plane_id,
            plane_object_type,
            spec.center_x,
            spec.center_y,
            0.0,
        )
    )
    features.append(
        _build_drilling_pattern_feature(
            state,
            spec,
            feature_id,
            geometry_id,
            operation_id,
            workpiece_id,
            workpiece_object_type,
        )
    )
    operations.append(_build_drilling_operation(state, spec.base_drilling, operation_id))
    elements.append(
        _build_working_step(
            spec.feature_name,
            step_id,
            feature_id,
            operation_id,
            feature_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.RoundHole",
            operation_object_type="ScmGroup.XCam.MachiningDataModel.Drilling.DrillingOperation",
        )
    )
    if uses_depth_expressions and start_expression_id is not None and end_expression_id is not None:
        expressions.append(
            _build_drilling_pattern_depth_expression(
                start_expression_id,
                feature_id,
                "StartDepth",
                depth_variable_name,
            )
        )
        expressions.append(
            _build_drilling_pattern_depth_expression(
                end_expression_id,
                feature_id,
                "EndDepth",
                depth_variable_name,
            )
        )


# ============================================================================
# Public read/build API
# ============================================================================

def read_pgmx_state(path: Path) -> PgmxState:
    """Lee un baseline Maestro y devuelve el estado basico de pieza, origen y area.

    No interpreta mecanizados. Sirve para reutilizar dimensiones reales y para
    tomar un baseline o un `source_pgmx_path` como punto de partida.
    """

    root, _, _ = _load_pgmx_container(path)

    variables = root.find("./{*}Variables")
    variable_values: dict[str, float] = {}
    if variables is not None:
        for variable in list(variables):
            name = _text(variable, "./{*}Name").lower()
            if not name:
                continue
            variable_values[name] = _safe_float(_text(variable, "./{*}Value"), 0.0)

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError(f"El archivo '{path}' no contiene WorkPiece.")

    piece_name = _text(workpiece, "./{*}Name", path.stem) or path.stem
    length = variable_values.get("dx1", _safe_float(_text(workpiece, "./{*}Length"), 0.0))
    width = variable_values.get("dy1", _safe_float(_text(workpiece, "./{*}Width"), 0.0))
    depth = variable_values.get("dz1", _safe_float(_text(workpiece, "./{*}Depth"), 0.0))

    setup_placement = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )
    if setup_placement is None:
        raise ValueError(f"El archivo '{path}' no contiene WorkpieceSetup/Placement.")

    origin_x = _safe_float(_text(setup_placement, "./{*}_xP"), 0.0)
    origin_y = _safe_float(_text(setup_placement, "./{*}_yP"), 0.0)
    origin_z = _safe_float(_text(setup_placement, "./{*}_zP"), 0.0)
    execution_fields = _normalize_execution_fields(
        _text(root, "./{*}MachiningParameters/{*}ExecutionFields", "HG")
    )

    return PgmxState(
        piece_name=piece_name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        execution_fields=execution_fields,
    )


def read_pgmx_geometries(path: Path) -> tuple[GeometryProfileSpec, ...]:
    """Lee y clasifica las geometrías presentes en la sección `Geometries`.

    Esta API se usa para inventariar familias manuales de Maestro y para dejar
    una base explicita de sintesis futura sin depender del nombre del archivo.
    """

    root, _, _ = _load_pgmx_container(path)
    profiles: list[GeometryProfileSpec] = []
    for geometry in root.findall("./{*}Geometries/{*}GeomGeometry"):
        profile = _extract_geometry_profile(geometry)
        if profile is not None:
            profiles.append(profile)
    return tuple(profiles)


def _merge_state(
    base_state: PgmxState,
    piece_name: Optional[str],
    length: Optional[float],
    width: Optional[float],
    depth: Optional[float],
    origin_x: Optional[float],
    origin_y: Optional[float],
    origin_z: Optional[float],
    execution_fields: Optional[str],
) -> PgmxState:
    return PgmxState(
        piece_name=base_state.piece_name if piece_name is None else piece_name,
        length=base_state.length if length is None else length,
        width=base_state.width if width is None else width,
        depth=base_state.depth if depth is None else depth,
        origin_x=base_state.origin_x if origin_x is None else origin_x,
        origin_y=base_state.origin_y if origin_y is None else origin_y,
        origin_z=base_state.origin_z if origin_z is None else origin_z,
        execution_fields=(
            base_state.execution_fields
            if execution_fields is None
            else _normalize_execution_fields(execution_fields)
        ),
    )


def _apply_piece_state(root: ET.Element, state: PgmxState) -> None:
    variables = root.find("./{*}Variables")
    if variables is not None:
        for variable in list(variables):
            value_node = variable.find("./{*}Value")
            _set_xmlns(value_node, "b", XSD_NS)
            name = _text(variable, "./{*}Name").lower()
            if name == "dx1":
                _set_text(value_node, _compact_number(state.length))
            elif name == "dy1":
                _set_text(value_node, _compact_number(state.width))
            elif name == "dz1":
                _set_text(value_node, _compact_number(state.depth))

    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if workpiece is None:
        raise ValueError("La plantilla no contiene WorkPiece.")
    _set_text(workpiece.find("./{*}Name"), state.piece_name)
    _set_text(workpiece.find("./{*}Length"), _compact_number(state.length))
    _set_text(workpiece.find("./{*}Width"), _compact_number(state.width))
    _set_text(workpiece.find("./{*}Depth"), _compact_number(state.depth))
    geometry = workpiece.find("./{*}Geometry")
    if geometry is not None:
        _set_text(geometry.find("./{*}Length"), _compact_number(state.length))
        _set_text(geometry.find("./{*}Width"), _compact_number(state.width))
        _set_text(geometry.find("./{*}Depth"), _compact_number(state.depth))

    plane_specs = {
        "Top": (state.length, state.width, 0.0, 0.0, state.depth),
        "Bottom": (state.length, state.width, 0.0, state.width, 0.0),
        "Right": (state.width, state.depth, state.length, 0.0, 0.0),
        "Left": (state.width, state.depth, 0.0, state.width, 0.0),
        "Front": (state.length, state.depth, 0.0, 0.0, 0.0),
        "Back": (state.length, state.depth, state.length, state.width, 0.0),
    }
    planes = root.find("./{*}Planes")
    if planes is not None:
        for plane in list(planes):
            plane_type = _text(plane, "./{*}Type") or _text(plane, "./{*}Name")
            spec = plane_specs.get(plane_type)
            if spec is None:
                continue
            x_dimension, y_dimension, x_origin, y_origin, z_origin = spec
            _set_text(plane.find("./{*}XDimension"), _compact_number(x_dimension))
            _set_text(plane.find("./{*}YDimension"), _compact_number(y_dimension))
            placement = plane.find("./{*}Placement")
            if placement is None:
                continue
            _set_text(placement.find("./{*}_xP"), _compact_number(x_origin))
            _set_text(placement.find("./{*}_yP"), _compact_number(y_origin))
            _set_text(placement.find("./{*}_zP"), _compact_number(z_origin))

    setup_placement = root.find(
        "./{*}Workplans/{*}MainWorkplan/{*}Setup/{*}WorkpieceSetups/{*}WorkpieceSetup/{*}Placement"
    )
    if setup_placement is None:
        raise ValueError("La plantilla no contiene WorkpieceSetup/Placement.")
    _set_text(setup_placement.find("./{*}_xP"), _compact_number(state.origin_x))
    _set_text(setup_placement.find("./{*}_yP"), _compact_number(state.origin_y))
    _set_text(setup_placement.find("./{*}_zP"), _compact_number(state.origin_z))

    execution_fields_node = root.find("./{*}MachiningParameters/{*}ExecutionFields")
    if execution_fields_node is None:
        raise ValueError("La plantilla no contiene MachiningParameters/ExecutionFields.")
    _set_text(execution_fields_node, state.execution_fields)


def _apply_line_millings(
    root: ET.Element,
    state: PgmxState,
    line_millings: Sequence[_HydratedLineMillingSpec],
) -> None:
    for line_milling in line_millings:
        _append_line_milling(root, state, line_milling)


def _apply_slot_millings(
    root: ET.Element,
    state: PgmxState,
    slot_millings: Sequence[_HydratedSlotMillingSpec],
) -> None:
    for slot_milling in slot_millings:
        _append_slot_milling(root, state, slot_milling)


def _apply_polyline_millings(
    root: ET.Element,
    state: PgmxState,
    polyline_millings: Sequence[_HydratedPolylineMillingSpec],
) -> None:
    for polyline_milling in polyline_millings:
        _append_polyline_milling(root, state, polyline_milling)


def _apply_circle_millings(
    root: ET.Element,
    state: PgmxState,
    circle_millings: Sequence[_HydratedCircleMillingSpec],
) -> None:
    for circle_milling in circle_millings:
        _append_circle_milling(root, state, circle_milling)


def _apply_squaring_millings(
    root: ET.Element,
    state: PgmxState,
    squaring_millings: Sequence[_HydratedSquaringMillingSpec],
) -> None:
    for squaring_milling in squaring_millings:
        _append_squaring_milling(root, state, squaring_milling)


def _apply_drillings(
    root: ET.Element,
    state: PgmxState,
    drillings: Sequence[_HydratedDrillingSpec],
) -> None:
    # Maestro guarda consistentemente los taladros multicara agrupados por
    # plano. Mantener ese orden reduce diferencias contra los ejemplos manuales
    # y evita mezclar caras arbitrariamente segun el orden de entrada.
    plane_priority = {
        "Top": 0,
        "Front": 1,
        "Back": 2,
        "Left": 3,
        "Right": 4,
    }
    ordered_drillings = sorted(
        enumerate(drillings),
        key=lambda item: (plane_priority.get(item[1].plane_name, 99), item[0]),
    )
    for _, drilling in ordered_drillings:
        _append_drilling(root, state, drilling)


def _drilling_plane_priority(plane_name: str) -> int:
    plane_priority = {
        "Top": 0,
        "Front": 1,
        "Back": 2,
        "Left": 3,
        "Right": 4,
    }
    return plane_priority.get(plane_name, 99)


def _apply_drilling_patterns(
    root: ET.Element,
    state: PgmxState,
    drilling_patterns: Sequence[_HydratedDrillingPatternSpec],
) -> None:
    ordered_drilling_patterns = sorted(
        enumerate(drilling_patterns),
        key=lambda item: (_drilling_plane_priority(item[1].plane_name), item[0]),
    )
    for _, drilling_pattern in ordered_drilling_patterns:
        _append_drilling_pattern(root, state, drilling_pattern)


HydratedMachiningSpec = Union[
    _HydratedLineMillingSpec,
    _HydratedSlotMillingSpec,
    _HydratedPolylineMillingSpec,
    _HydratedCircleMillingSpec,
    _HydratedSquaringMillingSpec,
    _HydratedDrillingSpec,
    _HydratedDrillingPatternSpec,
]


def _hydrate_machining_spec(
    spec: MachiningSpec,
    source_pgmx_path: Optional[Path],
) -> HydratedMachiningSpec:
    if isinstance(spec, SlotMillingSpec):
        return _hydrate_slot_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, LineMillingSpec):
        return _hydrate_line_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, PolylineMillingSpec):
        return _hydrate_polyline_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, CircleMillingSpec):
        return _hydrate_circle_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, SquaringMillingSpec):
        return _hydrate_squaring_milling_spec(spec, source_pgmx_path)
    if isinstance(spec, DrillingSpec):
        return _hydrate_drilling_spec(spec, source_pgmx_path)
    if isinstance(spec, DrillingPatternSpec):
        return _hydrate_drilling_pattern_spec(spec, source_pgmx_path)
    raise TypeError(f"Spec de mecanizado no soportado: {type(spec).__name__}")


def _append_hydrated_machining(
    root: ET.Element,
    state: PgmxState,
    spec: HydratedMachiningSpec,
) -> None:
    if isinstance(spec, _HydratedLineMillingSpec):
        _append_line_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedSlotMillingSpec):
        _append_slot_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedPolylineMillingSpec):
        _append_polyline_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedCircleMillingSpec):
        _append_circle_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedSquaringMillingSpec):
        _append_squaring_milling(root, state, spec)
        return
    if isinstance(spec, _HydratedDrillingSpec):
        _append_drilling(root, state, spec)
        return
    if isinstance(spec, _HydratedDrillingPatternSpec):
        _append_drilling_pattern(root, state, spec)
        return
    raise TypeError(f"Spec hidratado no soportado: {type(spec).__name__}")


def _split_hydrated_machinings(
    specs: Sequence[HydratedMachiningSpec],
) -> tuple[
    list[_HydratedLineMillingSpec],
    list[_HydratedSlotMillingSpec],
    list[_HydratedPolylineMillingSpec],
    list[_HydratedCircleMillingSpec],
    list[_HydratedSquaringMillingSpec],
    list[_HydratedDrillingSpec],
    list[_HydratedDrillingPatternSpec],
]:
    line_millings: list[_HydratedLineMillingSpec] = []
    slot_millings: list[_HydratedSlotMillingSpec] = []
    polyline_millings: list[_HydratedPolylineMillingSpec] = []
    circle_millings: list[_HydratedCircleMillingSpec] = []
    squaring_millings: list[_HydratedSquaringMillingSpec] = []
    drillings: list[_HydratedDrillingSpec] = []
    drilling_patterns: list[_HydratedDrillingPatternSpec] = []
    for spec in specs:
        if isinstance(spec, _HydratedLineMillingSpec):
            line_millings.append(spec)
        elif isinstance(spec, _HydratedSlotMillingSpec):
            slot_millings.append(spec)
        elif isinstance(spec, _HydratedPolylineMillingSpec):
            polyline_millings.append(spec)
        elif isinstance(spec, _HydratedCircleMillingSpec):
            circle_millings.append(spec)
        elif isinstance(spec, _HydratedSquaringMillingSpec):
            squaring_millings.append(spec)
        elif isinstance(spec, _HydratedDrillingSpec):
            drillings.append(spec)
        elif isinstance(spec, _HydratedDrillingPatternSpec):
            drilling_patterns.append(spec)
    return (
        line_millings,
        slot_millings,
        polyline_millings,
        circle_millings,
        squaring_millings,
        drillings,
        drilling_patterns,
    )


def _normalize_machining_order(value: Optional[Sequence[str]]) -> tuple[str, ...]:
    default_order = ("line", "slot", "polyline", "circle", "squaring", "drilling", "drilling_pattern")
    aliases = {
        "lines": "line",
        "line_milling": "line",
        "line_millings": "line",
        "slots": "slot",
        "slot_milling": "slot",
        "slot_millings": "slot",
        "canal": "slot",
        "canales": "slot",
        "ranura": "slot",
        "ranuras": "slot",
        "polyline_milling": "polyline",
        "polyline_millings": "polyline",
        "division": "polyline",
        "divisions": "polyline",
        "cutting": "polyline",
        "circle_milling": "circle",
        "circle_millings": "circle",
        "squaring_milling": "squaring",
        "squaring_millings": "squaring",
        "square": "squaring",
        "drilling": "drilling",
        "drilling_millings": "drilling",
        "drilling_pattern": "drilling_pattern",
        "drilling_patterns": "drilling_pattern",
        "hole_pattern": "drilling_pattern",
        "hole_patterns": "drilling_pattern",
        "pattern": "drilling_pattern",
        "patterns": "drilling_pattern",
        "patron": "drilling_pattern",
        "patrones": "drilling_pattern",
        "repeticion": "drilling_pattern",
        "repeticiones": "drilling_pattern",
    }
    ordered: list[str] = []
    for raw_item in value or default_order:
        normalized = aliases.get(str(raw_item or "").strip().lower(), str(raw_item or "").strip().lower())
        if normalized not in default_order or normalized in ordered:
            continue
        ordered.append(normalized)
    for item in default_order:
        if item not in ordered:
            ordered.append(item)
    return tuple(ordered)


def _ensure_xn_step(root: ET.Element, xn: XnSpec) -> None:
    elements = root.find("./{*}Workplans/{*}MainWorkplan/{*}Elements")
    workpiece = root.find("./{*}Workpieces/{*}WorkPiece")
    if elements is None or workpiece is None:
        raise ValueError("La plantilla no contiene MainWorkplan/Elements o WorkPiece para sintetizar Xn.")

    for executable in list(elements):
        if _xsi_type(executable) == "Xn":
            elements.remove(executable)

    workpiece_id = _text(workpiece, "./{*}Key/{*}ID")
    workpiece_object_type = _text(workpiece, "./{*}Key/{*}ObjectType")
    [step_id] = _reserve_ids(root, 1)
    elements.append(_build_xn_step(step_id, workpiece_id, workpiece_object_type, _normalize_xn_spec(xn)))


# ============================================================================
# Public machining builders
# ============================================================================

def build_line_milling_spec(
    line_x1: Optional[float],
    line_y1: Optional[float],
    line_x2: Optional[float],
    line_y2: Optional[float],
    line_feature_name: Optional[str],
    line_tool_id: Optional[str],
    line_tool_name: Optional[str],
    line_tool_width: Optional[float],
    line_security_plane: Optional[float],
    line_side_of_feature: Optional[str] = None,
    line_is_through: Optional[bool] = None,
    line_target_depth: Optional[float] = None,
    line_extra_depth: Optional[float] = None,
    line_approach_enabled: Optional[bool] = None,
    line_approach_type: Optional[str] = None,
    line_approach_mode: Optional[str] = None,
    line_approach_radius_multiplier: Optional[float] = None,
    line_approach_speed: Optional[float] = None,
    line_approach_arc_side: Optional[str] = None,
    line_retract_enabled: Optional[bool] = None,
    line_retract_type: Optional[str] = None,
    line_retract_mode: Optional[str] = None,
    line_retract_radius_multiplier: Optional[float] = None,
    line_retract_speed: Optional[float] = None,
    line_retract_arc_side: Optional[str] = None,
    line_retract_overlap: Optional[float] = None,
    line_milling_strategy: Optional[MillingStrategySpec] = None,
) -> Optional[LineMillingSpec]:
    """Construye un `LineMillingSpec` reusable para un fresado lineal.

    Devuelve `None` si la linea no viene informada, lo que simplifica el uso
    desde CLI y desde capas superiores que quieren tratar este mecanizado como
    opcional.
    """

    values = [line_x1, line_y1, line_x2, line_y2]
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("Para sintetizar el fresado lineal hay que indicar x1, y1, x2 e y2.")
    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(line_milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="LineMillingSpec",
    )
    return LineMillingSpec(
        start_x=float(line_x1),
        start_y=float(line_y1),
        end_x=float(line_x2),
        end_y=float(line_y2),
        feature_name=(line_feature_name or "Fresado").strip() or "Fresado",
        side_of_feature=_normalize_side_of_feature(line_side_of_feature),
        tool_id=(line_tool_id or "1902").strip() or "1902",
        tool_name=(line_tool_name or "E003").strip() or "E003",
        tool_width=9.52 if line_tool_width is None else float(line_tool_width),
        security_plane=20.0 if line_security_plane is None else float(line_security_plane),
        depth_spec=build_milling_depth_spec(
            is_through=line_is_through,
            target_depth=line_target_depth,
            extra_depth=line_extra_depth,
        ),
        approach=build_approach_spec(
            enabled=line_approach_enabled,
            approach_type=line_approach_type,
            mode=line_approach_mode,
            radius_multiplier=line_approach_radius_multiplier,
            speed=line_approach_speed,
            arc_side=line_approach_arc_side,
        ),
        retract=build_retract_spec(
            enabled=line_retract_enabled,
            retract_type=line_retract_type,
            mode=line_retract_mode,
            radius_multiplier=line_retract_radius_multiplier,
            speed=line_retract_speed,
            arc_side=line_retract_arc_side,
            overlap=line_retract_overlap,
        ),
        milling_strategy=normalized_strategy,
    )


def build_slot_milling_spec(
    *,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    side_of_feature: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    approach_enabled: Optional[bool] = None,
    approach_type: Optional[str] = None,
    approach_mode: Optional[str] = None,
    approach_radius_multiplier: Optional[float] = None,
    approach_speed: Optional[float] = None,
    approach_arc_side: Optional[str] = None,
    retract_enabled: Optional[bool] = None,
    retract_type: Optional[str] = None,
    retract_mode: Optional[str] = None,
    retract_radius_multiplier: Optional[float] = None,
    retract_speed: Optional[float] = None,
    retract_arc_side: Optional[str] = None,
    retract_overlap: Optional[float] = None,
    material_position: Optional[str] = None,
    side_offset: Optional[float] = None,
    end_radius: Optional[float] = None,
    slot_angle: Optional[float] = None,
) -> SlotMillingSpec:
    """Construye una ranura lineal `SlotSide` compatible con Sierra Vertical X."""

    depth_spec = build_milling_depth_spec(
        is_through=False if is_through is None and target_depth is None and extra_depth is None else is_through,
        target_depth=10.0 if is_through is None and target_depth is None and extra_depth is None else target_depth,
        extra_depth=extra_depth,
    )
    return _normalize_slot_milling_spec(
        SlotMillingSpec(
            start_x=float(start_x),
            start_y=float(start_y),
            end_x=float(end_x),
            end_y=float(end_y),
            feature_name=(feature_name or "Canal").strip() or "Canal",
            plane_name=_normalize_plane_name(plane_name),
            side_of_feature=_normalize_side_of_feature(side_of_feature),
            tool_id=(tool_id or "1899").strip() or "1899",
            tool_name=(tool_name or "082").strip() or "082",
            tool_width=3.8 if tool_width is None else float(tool_width),
            security_plane=20.0 if security_plane is None else float(security_plane),
            depth_spec=depth_spec,
            approach=build_approach_spec(
                enabled=approach_enabled,
                approach_type=approach_type,
                mode=approach_mode,
                radius_multiplier=approach_radius_multiplier,
                speed=approach_speed,
                arc_side=approach_arc_side,
            ),
            retract=build_retract_spec(
                enabled=retract_enabled,
                retract_type=retract_type,
                mode=retract_mode,
                radius_multiplier=retract_radius_multiplier,
                speed=retract_speed,
                arc_side=retract_arc_side,
                overlap=retract_overlap,
            ),
            material_position=(material_position or "Left").strip() or "Left",
            side_offset=0.0 if side_offset is None else float(side_offset),
            end_radius=60.0 if end_radius is None else float(end_radius),
            slot_angle=1.5707963267948966 if slot_angle is None else float(slot_angle),
        )
    )


def build_polyline_milling_spec(
    points: Sequence[tuple[float, float]],
    feature_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    side_of_feature: Optional[str] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    approach_enabled: Optional[bool] = None,
    approach_type: Optional[str] = None,
    approach_mode: Optional[str] = None,
    approach_radius_multiplier: Optional[float] = None,
    approach_speed: Optional[float] = None,
    approach_arc_side: Optional[str] = None,
    retract_enabled: Optional[bool] = None,
    retract_type: Optional[str] = None,
    retract_mode: Optional[str] = None,
    retract_radius_multiplier: Optional[float] = None,
    retract_speed: Optional[float] = None,
    retract_arc_side: Optional[str] = None,
    retract_overlap: Optional[float] = None,
    milling_strategy: Optional[MillingStrategySpec] = None,
) -> PolylineMillingSpec:
    """Construye un `PolylineMillingSpec` reusable para una polilinea lineal.

    Si `points` cierra sobre su primer punto, la polilinea se interpreta como
    contorno cerrado.
    """

    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="PolylineMillingSpec",
    )
    normalized_spec = PolylineMillingSpec(
        points=_normalize_polyline_points(points),
        feature_name=(feature_name or "Fresado").strip() or "Fresado",
        side_of_feature=_normalize_side_of_feature(side_of_feature),
        tool_id=(tool_id or "1902").strip() or "1902",
        tool_name=(tool_name or "E003").strip() or "E003",
        tool_width=9.52 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        ),
        approach=build_approach_spec(
            enabled=approach_enabled,
            approach_type=approach_type,
            mode=approach_mode,
            radius_multiplier=approach_radius_multiplier,
            speed=approach_speed,
            arc_side=approach_arc_side,
        ),
        retract=build_retract_spec(
            enabled=retract_enabled,
            retract_type=retract_type,
            mode=retract_mode,
            radius_multiplier=retract_radius_multiplier,
            speed=retract_speed,
            arc_side=retract_arc_side,
            overlap=retract_overlap,
        ),
        milling_strategy=normalized_strategy,
    )
    _validate_polyline_postprocessable_by_maestro(normalized_spec)
    return normalized_spec


def build_circle_milling_spec(
    *,
    center_x: float,
    center_y: float,
    radius: float,
    winding: Optional[str] = None,
    feature_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    side_of_feature: Optional[str] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    approach_enabled: Optional[bool] = None,
    approach_type: Optional[str] = None,
    approach_mode: Optional[str] = None,
    approach_radius_multiplier: Optional[float] = None,
    approach_speed: Optional[float] = None,
    approach_arc_side: Optional[str] = None,
    retract_enabled: Optional[bool] = None,
    retract_type: Optional[str] = None,
    retract_mode: Optional[str] = None,
    retract_radius_multiplier: Optional[float] = None,
    retract_speed: Optional[float] = None,
    retract_arc_side: Optional[str] = None,
    retract_overlap: Optional[float] = None,
    milling_strategy: Optional[MillingStrategySpec] = None,
) -> CircleMillingSpec:
    """Construye un `CircleMillingSpec` reusable para un fresado circular."""

    return _normalize_circle_milling_spec(
        CircleMillingSpec(
            center_x=float(center_x),
            center_y=float(center_y),
            radius=float(radius),
            winding=_normalize_geometry_winding(winding),
            feature_name=(feature_name or "Fresado").strip() or "Fresado",
            side_of_feature=_normalize_side_of_feature(side_of_feature),
            tool_id=(tool_id or "1902").strip() or "1902",
            tool_name=(tool_name or "E003").strip() or "E003",
            tool_width=9.52 if tool_width is None else float(tool_width),
            security_plane=20.0 if security_plane is None else float(security_plane),
            depth_spec=build_milling_depth_spec(
                is_through=is_through,
                target_depth=target_depth,
                extra_depth=extra_depth,
            ),
            approach=build_approach_spec(
                enabled=approach_enabled,
                approach_type=approach_type,
                mode=approach_mode,
                radius_multiplier=approach_radius_multiplier,
                speed=approach_speed,
                arc_side=approach_arc_side,
            ),
            retract=build_retract_spec(
                enabled=retract_enabled,
                retract_type=retract_type,
                mode=retract_mode,
                radius_multiplier=retract_radius_multiplier,
                speed=retract_speed,
                arc_side=retract_arc_side,
                overlap=retract_overlap,
            ),
            milling_strategy=_normalize_milling_strategy_spec(milling_strategy),
        )
    )


def build_squaring_milling_spec(
    *,
    start_edge: Optional[str] = None,
    winding: Optional[str] = None,
    start_coordinate: Optional[float] = None,
    feature_name: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_width: Optional[float] = None,
    security_plane: Optional[float] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    approach_enabled: Optional[bool] = None,
    approach_type: Optional[str] = None,
    approach_mode: Optional[str] = None,
    approach_radius_multiplier: Optional[float] = None,
    approach_speed: Optional[float] = None,
    approach_arc_side: Optional[str] = None,
    retract_enabled: Optional[bool] = None,
    retract_type: Optional[str] = None,
    retract_mode: Optional[str] = None,
    retract_radius_multiplier: Optional[float] = None,
    retract_speed: Optional[float] = None,
    retract_arc_side: Optional[str] = None,
    retract_overlap: Optional[float] = None,
    milling_strategy: Optional[MillingStrategySpec] = None,
) -> SquaringMillingSpec:
    """Construye un `SquaringMillingSpec` reusable para escuadrar la pieza."""

    has_explicit_depth = any(value is not None for value in (is_through, target_depth, extra_depth))
    depth_spec = (
        build_milling_depth_spec(is_through=True, extra_depth=1.0)
        if not has_explicit_depth
        else build_milling_depth_spec(
            is_through=is_through,
            target_depth=target_depth,
            extra_depth=extra_depth,
        )
    )

    has_explicit_approach = any(
        value is not None
        for value in (
            approach_enabled,
            approach_type,
            approach_mode,
            approach_radius_multiplier,
            approach_speed,
            approach_arc_side,
        )
    )
    approach_spec = (
        build_approach_spec(
            enabled=True,
            approach_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
        )
        if not has_explicit_approach
        else build_approach_spec(
            enabled=approach_enabled,
            approach_type=approach_type,
            mode=approach_mode,
            radius_multiplier=approach_radius_multiplier,
            speed=approach_speed,
            arc_side=approach_arc_side,
        )
    )

    has_explicit_retract = any(
        value is not None
        for value in (
            retract_enabled,
            retract_type,
            retract_mode,
            retract_radius_multiplier,
            retract_speed,
            retract_arc_side,
            retract_overlap,
        )
    )
    retract_spec = (
        build_retract_spec(
            enabled=True,
            retract_type="Arc",
            mode="Quote",
            radius_multiplier=2.0,
            speed=-1.0,
            arc_side="Automatic",
            overlap=0.0,
        )
        if not has_explicit_retract
        else build_retract_spec(
            enabled=retract_enabled,
            retract_type=retract_type,
            mode=retract_mode,
            radius_multiplier=retract_radius_multiplier,
            speed=retract_speed,
            arc_side=retract_arc_side,
            overlap=retract_overlap,
        )
    )

    normalized_strategy = _ensure_milling_strategy_allowed(
        _normalize_milling_strategy_spec(milling_strategy),
        allowed_types=(UnidirectionalMillingStrategySpec, BidirectionalMillingStrategySpec),
        context="SquaringMillingSpec",
    )
    return SquaringMillingSpec(
        start_edge=_normalize_squaring_start_edge(start_edge),
        winding=_normalize_geometry_winding(winding),
        start_coordinate=None if start_coordinate is None else float(start_coordinate),
        feature_name=(feature_name or "Fresado").strip() or "Fresado",
        tool_id=(tool_id or "1900").strip() or "1900",
        tool_name=(tool_name or "E001").strip() or "E001",
        tool_width=18.36 if tool_width is None else float(tool_width),
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        approach=approach_spec,
        retract=retract_spec,
        milling_strategy=normalized_strategy,
    )


def build_drilling_spec(
    *,
    center_x: float,
    center_y: float,
    diameter: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    security_plane: Optional[float] = None,
    is_through: Optional[bool] = None,
    target_depth: Optional[float] = None,
    extra_depth: Optional[float] = None,
    drill_family: Optional[str] = None,
    tool_resolution: Optional[str] = None,
    tool_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> DrillingSpec:
    """Construye un `DrillingSpec` reusable para taladros puntuales."""

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
    return DrillingSpec(
        center_x=float(center_x),
        center_y=float(center_y),
        diameter=float(diameter),
        feature_name=(feature_name or "Taladrado").strip() or "Taladrado",
        plane_name=normalized_plane_name,
        security_plane=20.0 if security_plane is None else float(security_plane),
        depth_spec=depth_spec,
        drill_family=effective_drill_family,
        tool_resolution=_normalize_tool_resolution(tool_resolution or "Auto"),
        tool_id=(tool_id or "0").strip() or "0",
        tool_name=(tool_name or "").strip(),
    )


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
    depth_spec = MillingDepthSpec(
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


# ============================================================================
# Public execution API
# ============================================================================

def build_synthesis_request(
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    *,
    source_pgmx_path: Optional[Path] = None,
    piece: Optional[PgmxState] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    execution_fields: Optional[str] = None,
    line_millings: Optional[Sequence[LineMillingSpec]] = None,
    slot_millings: Optional[Sequence[SlotMillingSpec]] = None,
    polyline_millings: Optional[Sequence[PolylineMillingSpec]] = None,
    circle_millings: Optional[Sequence[CircleMillingSpec]] = None,
    squaring_millings: Optional[Sequence[SquaringMillingSpec]] = None,
    drillings: Optional[Sequence[DrillingSpec]] = None,
    drilling_patterns: Optional[Sequence[DrillingPatternSpec]] = None,
    ordered_machinings: Optional[Sequence[MachiningSpec]] = None,
    machining_order: Optional[Sequence[str]] = None,
    xn: Optional[XnSpec] = None,
) -> PgmxSynthesisRequest:
    """Arma una solicitud reusable de sintesis para el flujo principal.

    Orden recomendado de uso:
    1. leer o definir la pieza
    2. construir `LineMillingSpec`, `SlotMillingSpec`, `PolylineMillingSpec`,
       `CircleMillingSpec`, `SquaringMillingSpec`, `DrillingSpec` y
       `DrillingPatternSpec`, y
       opcionalmente `XnSpec`
    3. construir el request
    4. ejecutar `synthesize_request(...)`

    Soporte de contenedores baseline:
    - `baseline_path`: `.pgmx`, `Pieza.xml` o carpeta que contenga `Pieza.xml`
      Si no se indica, usa `DEFAULT_BASELINE_DIR`.
    - `source_pgmx_path`: `.pgmx`, `Pieza.xml` o carpeta usada como plantilla de serializacion
    """

    if output_path is None:
        raise ValueError("`output_path` es obligatorio para construir un `PgmxSynthesisRequest`.")

    effective_baseline_path = Path(baseline_path) if baseline_path is not None else DEFAULT_BASELINE_DIR
    effective_output_path = Path(output_path)

    base_piece = piece or (
        read_pgmx_state(source_pgmx_path) if source_pgmx_path else read_pgmx_state(effective_baseline_path)
    )
    effective_execution_fields = execution_fields
    if effective_execution_fields is None and piece is None:
        effective_execution_fields = "HG"
    target_piece = _merge_state(
        base_piece,
        piece_name,
        length,
        width,
        depth,
        origin_x,
        origin_y,
        origin_z,
        effective_execution_fields,
    )
    return PgmxSynthesisRequest(
        baseline_path=effective_baseline_path,
        output_path=effective_output_path,
        piece=target_piece,
        source_pgmx_path=source_pgmx_path,
        line_millings=tuple(line_millings or ()),
        slot_millings=tuple(slot_millings or ()),
        polyline_millings=tuple(polyline_millings or ()),
        circle_millings=tuple(circle_millings or ()),
        squaring_millings=tuple(squaring_millings or ()),
        drillings=tuple(drillings or ()),
        drilling_patterns=tuple(drilling_patterns or ()),
        ordered_machinings=tuple(ordered_machinings or ()),
        machining_order=_normalize_machining_order(machining_order),
        xn=_normalize_xn_spec(xn),
    )


def synthesize_request(request: PgmxSynthesisRequest) -> PgmxSynthesisResult:
    """Ejecuta una solicitud de sintesis y escribe el `.pgmx` resultante.

    Esta es la funcion principal para el flujo programatico.
    """

    baseline_root, baseline_entries, _ = _load_pgmx_container(request.baseline_path)
    hydrated_line_millings = [
        _hydrate_line_milling_spec(line_milling, request.source_pgmx_path)
        for line_milling in request.line_millings
    ]
    hydrated_slot_millings = [
        _hydrate_slot_milling_spec(slot_milling, request.source_pgmx_path)
        for slot_milling in request.slot_millings
    ]
    hydrated_polyline_millings = [
        _hydrate_polyline_milling_spec(polyline_milling, request.source_pgmx_path)
        for polyline_milling in request.polyline_millings
    ]
    hydrated_circle_millings = [
        _hydrate_circle_milling_spec(circle_milling, request.source_pgmx_path)
        for circle_milling in request.circle_millings
    ]
    hydrated_squaring_millings = [
        _hydrate_squaring_milling_spec(squaring_milling, request.source_pgmx_path)
        for squaring_milling in request.squaring_millings
    ]
    hydrated_drillings = [
        _hydrate_drilling_spec(drilling, request.source_pgmx_path)
        for drilling in request.drillings
    ]
    hydrated_drilling_patterns = [
        _hydrate_drilling_pattern_spec(drilling_pattern, request.source_pgmx_path)
        for drilling_pattern in request.drilling_patterns
    ]
    hydrated_ordered_machinings = [
        _hydrate_machining_spec(spec, request.source_pgmx_path)
        for spec in request.ordered_machinings
    ]
    (
        ordered_line_millings,
        ordered_slot_millings,
        ordered_polyline_millings,
        ordered_circle_millings,
        ordered_squaring_millings,
        ordered_drillings,
        ordered_drilling_patterns,
    ) = _split_hydrated_machinings(hydrated_ordered_machinings)
    normalized_xn = _normalize_xn_spec(request.xn)
    _validate_tool_sinking_lengths(
        request.piece,
        hydrated_line_millings + ordered_line_millings,
        hydrated_slot_millings + ordered_slot_millings,
        hydrated_polyline_millings + ordered_polyline_millings,
        hydrated_circle_millings + ordered_circle_millings,
        hydrated_squaring_millings + ordered_squaring_millings,
        hydrated_drillings + ordered_drillings,
        hydrated_drilling_patterns + ordered_drilling_patterns,
    )

    _apply_piece_state(baseline_root, request.piece)
    for spec in hydrated_ordered_machinings:
        _append_hydrated_machining(baseline_root, request.piece, spec)
    apply_group = {
        "line": lambda: _apply_line_millings(
            baseline_root,
            request.piece,
            hydrated_line_millings,
        ),
        "slot": lambda: _apply_slot_millings(
            baseline_root,
            request.piece,
            hydrated_slot_millings,
        ),
        "polyline": lambda: _apply_polyline_millings(
            baseline_root,
            request.piece,
            hydrated_polyline_millings,
        ),
        "circle": lambda: _apply_circle_millings(
            baseline_root,
            request.piece,
            hydrated_circle_millings,
        ),
        "squaring": lambda: _apply_squaring_millings(
            baseline_root,
            request.piece,
            hydrated_squaring_millings,
        ),
        "drilling": lambda: _apply_drillings(
            baseline_root,
            request.piece,
            hydrated_drillings,
        ),
        "drilling_pattern": lambda: _apply_drilling_patterns(
            baseline_root,
            request.piece,
            hydrated_drilling_patterns,
        ),
    }
    for group_name in _normalize_machining_order(request.machining_order):
        apply_group[group_name]()
    _ensure_xn_step(baseline_root, normalized_xn)

    xml_bytes = _finalize_synthesized_pgmx_xml_bytes(
        ET.tostring(
            baseline_root,
            encoding="utf-8",
            xml_declaration=request.source_pgmx_path is None,
        )
    )
    _write_pgmx_zip(
        output_path=request.output_path,
        xml_bytes=xml_bytes,
        template_entries=baseline_entries,
        xml_entry_name=f"{request.output_path.stem}.xml",
    )
    return PgmxSynthesisResult(
        output_path=request.output_path,
        piece=request.piece,
        sha256=hashlib.sha256(request.output_path.read_bytes()).hexdigest(),
        line_millings=request.line_millings,
        slot_millings=request.slot_millings,
        polyline_millings=request.polyline_millings,
        circle_millings=request.circle_millings,
        squaring_millings=request.squaring_millings,
        drillings=request.drillings,
        drilling_patterns=request.drilling_patterns,
        ordered_machinings=request.ordered_machinings,
        machining_order=_normalize_machining_order(request.machining_order),
        xn=normalized_xn,
    )


def synthesize_pgmx(
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    source_pgmx_path: Optional[Path] = None,
    piece_name: Optional[str] = None,
    length: Optional[float] = None,
    width: Optional[float] = None,
    depth: Optional[float] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    line_milling: Optional[LineMillingSpec] = None,
    slot_milling: Optional[SlotMillingSpec] = None,
    polyline_milling: Optional[PolylineMillingSpec] = None,
    circle_milling: Optional[CircleMillingSpec] = None,
    squaring_milling: Optional[SquaringMillingSpec] = None,
    drilling: Optional[DrillingSpec] = None,
    drilling_pattern: Optional[DrillingPatternSpec] = None,
    xn: Optional[XnSpec] = None,
    execution_fields: Optional[str] = None,
) -> PgmxState:
    """Wrapper de compatibilidad para el flujo historico basado en argumentos sueltos.

    Para codigo nuevo conviene preferir `build_synthesis_request(...)` y
    `synthesize_request(...)`.
    """

    request = build_synthesis_request(
        baseline_path=baseline_path,
        output_path=output_path,
        source_pgmx_path=source_pgmx_path,
        piece_name=piece_name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        execution_fields=execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
        slot_millings=[slot_milling] if slot_milling is not None else (),
        polyline_millings=[polyline_milling] if polyline_milling is not None else (),
        circle_millings=[circle_milling] if circle_milling is not None else (),
        squaring_millings=[squaring_milling] if squaring_milling is not None else (),
        drillings=[drilling] if drilling is not None else (),
        drilling_patterns=[drilling_pattern] if drilling_pattern is not None else (),
        xn=xn,
    )
    return synthesize_request(request).piece


# ============================================================================
# CLI
# ============================================================================

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sintetiza un PGMX base a partir de un baseline Maestro (.pgmx, Pieza.xml o carpeta)."
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE_DIR),
        help=(
            "Ruta al baseline Maestro: `.pgmx`, `Pieza.xml` o carpeta contenedora. "
            "Si no se indica, usa `tools/maestro_baselines`."
        ),
    )
    parser.add_argument("--output", required=True, help="Ruta del .pgmx sintetizado de salida.")
    parser.add_argument(
        "--source-pgmx",
        "--source-template",
        dest="source_pgmx",
        help=(
            "Ruta a una plantilla manual de Maestro (`.pgmx`, `Pieza.xml` o carpeta) "
            "desde la cual copiar serializacion ya validada."
        ),
    )
    parser.add_argument("--piece-name", help="Nombre interno de la pieza dentro del .pgmx.")
    parser.add_argument("--length", type=float, help="Largo final de la pieza (dx1).")
    parser.add_argument("--width", type=float, help="Ancho final de la pieza (dy1).")
    parser.add_argument("--depth", type=float, help="Espesor final de la pieza (dz1).")
    parser.add_argument("--origin-x", type=float, help="Origen de mecanizado X.")
    parser.add_argument("--origin-y", type=float, help="Origen de mecanizado Y.")
    parser.add_argument("--origin-z", type=float, help="Origen de mecanizado Z.")
    parser.add_argument(
        "--execution-fields",
        "--area",
        dest="execution_fields",
        help="Area de Parametros de Maquina. Valores observados: A, EF, HG. Si no se indica, la sintesis usa HG.",
    )
    parser.add_argument("--line-x1", type=float, help="Coordenada X inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y1", type=float, help="Coordenada Y inicial de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-x2", type=float, help="Coordenada X final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-y2", type=float, help="Coordenada Y final de una linea sobre Top para sintetizar su fresado.")
    parser.add_argument("--line-feature-name", help="Nombre del feature/working step del fresado lineal.")
    parser.add_argument("--line-side-of-feature", help="Correccion de herramienta del fresado lineal: Center, Right o Left.")
    parser.add_argument("--line-tool-id", help="ID de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-name", help="Nombre de herramienta para el fresado lineal.")
    parser.add_argument("--line-tool-width", type=float, help="Ancho del perfil barrido para el fresado lineal.")
    parser.add_argument("--line-security-plane", type=float, help="Plano de seguridad usado en approach/retract.")
    parser.add_argument(
        "--line-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado lineal. Por defecto queda activado.",
    )
    parser.add_argument(
        "--line-target-depth",
        type=float,
        help="Profundidad fija del fresado lineal cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--line-extra-depth",
        type=float,
        help="Extra del fresado lineal cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--line-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1."
        ),
    )
    parser.add_argument("--line-approach-type", help="Tipo de approach. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-approach-mode",
        help="Modo de approach. Valores utiles: Down o Quote (UI Maestro: En Cota). Para Arc se valido Quote.",
    )
    parser.add_argument(
        "--line-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach lineal.",
    )
    parser.add_argument(
        "--line-approach-speed",
        type=float,
        help="Velocidad del approach. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-approach-arc-side",
        help="Lado del arco del approach. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado lineal. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro: Line/Quote/radio 2/speed -1/overlap 0."
        ),
    )
    parser.add_argument("--line-retract-type", help="Tipo de retract. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--line-retract-mode",
        help="Modo de retract. Valores utiles: Up o Quote (UI Maestro: En Cota). Para Arc se validaron Quote y Up.",
    )
    parser.add_argument(
        "--line-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract lineal.",
    )
    parser.add_argument(
        "--line-retract-speed",
        type=float,
        help="Velocidad del retract. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--line-retract-arc-side",
        help="Lado del arco del retract. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--line-retract-overlap",
        type=float,
        help="Sobreposicion del retract lineal.",
    )
    parser.add_argument("--circle-center-x", type=float, help="Coordenada X del centro del circulo sobre Top.")
    parser.add_argument("--circle-center-y", type=float, help="Coordenada Y del centro del circulo sobre Top.")
    parser.add_argument("--circle-radius", type=float, help="Radio del circulo a fresar sobre Top.")
    parser.add_argument("--circle-winding", help="Sentido del circulo: CounterClockwise/Antihorario o Clockwise/Horario.")
    parser.add_argument("--circle-feature-name", help="Nombre del feature/working step del fresado circular.")
    parser.add_argument("--circle-side-of-feature", help="Correccion de herramienta del fresado circular: Center, Right o Left.")
    parser.add_argument("--circle-tool-id", help="ID de herramienta para el fresado circular.")
    parser.add_argument("--circle-tool-name", help="Nombre de herramienta para el fresado circular.")
    parser.add_argument("--circle-tool-width", type=float, help="Ancho del perfil barrido para el fresado circular.")
    parser.add_argument("--circle-security-plane", type=float, help="Plano de seguridad usado en approach/retract del circulo.")
    parser.add_argument(
        "--circle-through",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Configura Pasante activado/desactivado del fresado circular. Por defecto queda activado.",
    )
    parser.add_argument(
        "--circle-target-depth",
        type=float,
        help="Profundidad fija del fresado circular cuando Pasante esta desactivado.",
    )
    parser.add_argument(
        "--circle-extra-depth",
        type=float,
        help="Extra del fresado circular cuando Pasante esta activado.",
    )
    parser.add_argument(
        "--circle-approach-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el approach del fresado circular. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro."
        ),
    )
    parser.add_argument("--circle-approach-type", help="Tipo de approach del circulo. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--circle-approach-mode",
        help="Modo de approach del circulo. Valores utiles: Down o Quote (UI Maestro: En Cota).",
    )
    parser.add_argument(
        "--circle-approach-radius-multiplier",
        type=float,
        help="Multiplicador de radio del approach circular.",
    )
    parser.add_argument(
        "--circle-approach-speed",
        type=float,
        help="Velocidad del approach del circulo. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--circle-approach-arc-side",
        help="Lado del arco del approach circular. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--circle-retract-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Habilita/deshabilita el retract del fresado circular. "
            "Si se habilita sin mas parametros, usa los defaults observados en Maestro."
        ),
    )
    parser.add_argument("--circle-retract-type", help="Tipo de retract del circulo. Actualmente validado: Line o Arc.")
    parser.add_argument(
        "--circle-retract-mode",
        help="Modo de retract del circulo. Valores utiles: Up o Quote (UI Maestro: En Cota).",
    )
    parser.add_argument(
        "--circle-retract-radius-multiplier",
        type=float,
        help="Multiplicador de radio del retract circular.",
    )
    parser.add_argument(
        "--circle-retract-speed",
        type=float,
        help="Velocidad del retract del circulo. Use -1 para el valor vacio/null que guarda Maestro.",
    )
    parser.add_argument(
        "--circle-retract-arc-side",
        help="Lado del arco del retract circular. Actualmente validado: Automatic.",
    )
    parser.add_argument(
        "--circle-retract-overlap",
        type=float,
        help="Sobreposicion del retract circular.",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output)
    line_milling = build_line_milling_spec(
        line_x1=args.line_x1,
        line_y1=args.line_y1,
        line_x2=args.line_x2,
        line_y2=args.line_y2,
        line_feature_name=args.line_feature_name,
        line_side_of_feature=args.line_side_of_feature,
        line_tool_id=args.line_tool_id,
        line_tool_name=args.line_tool_name,
        line_tool_width=args.line_tool_width,
        line_security_plane=args.line_security_plane,
        line_is_through=args.line_through,
        line_target_depth=args.line_target_depth,
        line_extra_depth=args.line_extra_depth,
        line_approach_enabled=args.line_approach_enabled,
        line_approach_type=args.line_approach_type,
        line_approach_mode=args.line_approach_mode,
        line_approach_radius_multiplier=args.line_approach_radius_multiplier,
        line_approach_speed=args.line_approach_speed,
        line_approach_arc_side=args.line_approach_arc_side,
        line_retract_enabled=args.line_retract_enabled,
        line_retract_type=args.line_retract_type,
        line_retract_mode=args.line_retract_mode,
        line_retract_radius_multiplier=args.line_retract_radius_multiplier,
        line_retract_speed=args.line_retract_speed,
        line_retract_arc_side=args.line_retract_arc_side,
        line_retract_overlap=args.line_retract_overlap,
    )
    circle_args = (args.circle_center_x, args.circle_center_y, args.circle_radius)
    if all(value is None for value in circle_args):
        circle_milling = None
    elif any(value is None for value in circle_args):
        raise ValueError(
            "Para sintetizar el fresado circular hay que indicar center_x, center_y y radius."
        )
    else:
        circle_milling = build_circle_milling_spec(
            center_x=float(args.circle_center_x),
            center_y=float(args.circle_center_y),
            radius=float(args.circle_radius),
            winding=args.circle_winding,
            feature_name=args.circle_feature_name,
            tool_id=args.circle_tool_id,
            tool_name=args.circle_tool_name,
            tool_width=args.circle_tool_width,
            security_plane=args.circle_security_plane,
            side_of_feature=args.circle_side_of_feature,
            is_through=args.circle_through,
            target_depth=args.circle_target_depth,
            extra_depth=args.circle_extra_depth,
            approach_enabled=args.circle_approach_enabled,
            approach_type=args.circle_approach_type,
            approach_mode=args.circle_approach_mode,
            approach_radius_multiplier=args.circle_approach_radius_multiplier,
            approach_speed=args.circle_approach_speed,
            approach_arc_side=args.circle_approach_arc_side,
            retract_enabled=args.circle_retract_enabled,
            retract_type=args.circle_retract_type,
            retract_mode=args.circle_retract_mode,
            retract_radius_multiplier=args.circle_retract_radius_multiplier,
            retract_speed=args.circle_retract_speed,
            retract_arc_side=args.circle_retract_arc_side,
            retract_overlap=args.circle_retract_overlap,
        )
    request = build_synthesis_request(
        baseline_path=Path(args.baseline),
        output_path=output_path,
        source_pgmx_path=Path(args.source_pgmx) if args.source_pgmx else None,
        piece_name=args.piece_name,
        length=args.length,
        width=args.width,
        depth=args.depth,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        origin_z=args.origin_z,
        execution_fields=args.execution_fields,
        line_millings=[line_milling] if line_milling is not None else (),
        circle_millings=[circle_milling] if circle_milling is not None else (),
    )
    result = synthesize_request(request)

    summary = {
        "output": str(output_path),
        "piece_name": result.piece.piece_name,
        "length": _compact_number(result.piece.length),
        "width": _compact_number(result.piece.width),
        "depth": _compact_number(result.piece.depth),
        "origin_x": _compact_number(result.piece.origin_x),
        "origin_y": _compact_number(result.piece.origin_y),
        "origin_z": _compact_number(result.piece.origin_z),
        "execution_fields": result.piece.execution_fields,
        "sha256": result.sha256,
    }
    if line_milling is not None:
        summary["line_milling"] = {
            "feature_name": line_milling.feature_name,
            "start": [_compact_number(line_milling.start_x), _compact_number(line_milling.start_y)],
            "end": [_compact_number(line_milling.end_x), _compact_number(line_milling.end_y)],
            "side_of_feature": line_milling.side_of_feature,
            "tool_id": line_milling.tool_id,
            "tool_name": line_milling.tool_name,
            "tool_width": _compact_number(line_milling.tool_width),
            "security_plane": _compact_number(line_milling.security_plane),
            "approach": {
                "is_enabled": line_milling.approach.is_enabled,
                "approach_type": line_milling.approach.approach_type,
                "mode": line_milling.approach.mode,
                "radius_multiplier": _compact_number(line_milling.approach.radius_multiplier),
                "speed": _compact_number(line_milling.approach.speed),
                "arc_side": line_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": line_milling.retract.is_enabled,
                "retract_type": line_milling.retract.retract_type,
                "mode": line_milling.retract.mode,
                "radius_multiplier": _compact_number(line_milling.retract.radius_multiplier),
                "speed": _compact_number(line_milling.retract.speed),
                "arc_side": line_milling.retract.arc_side,
                "overlap": _compact_number(line_milling.retract.overlap),
            },
        }
    if circle_milling is not None:
        summary["circle_milling"] = {
            "feature_name": circle_milling.feature_name,
            "center": [_compact_number(circle_milling.center_x), _compact_number(circle_milling.center_y)],
            "radius": _compact_number(circle_milling.radius),
            "winding": circle_milling.winding,
            "side_of_feature": circle_milling.side_of_feature,
            "tool_id": circle_milling.tool_id,
            "tool_name": circle_milling.tool_name,
            "tool_width": _compact_number(circle_milling.tool_width),
            "security_plane": _compact_number(circle_milling.security_plane),
            "approach": {
                "is_enabled": circle_milling.approach.is_enabled,
                "approach_type": circle_milling.approach.approach_type,
                "mode": circle_milling.approach.mode,
                "radius_multiplier": _compact_number(circle_milling.approach.radius_multiplier),
                "speed": _compact_number(circle_milling.approach.speed),
                "arc_side": circle_milling.approach.arc_side,
            },
            "retract": {
                "is_enabled": circle_milling.retract.is_enabled,
                "retract_type": circle_milling.retract.retract_type,
                "mode": circle_milling.retract.mode,
                "radius_multiplier": _compact_number(circle_milling.retract.radius_multiplier),
                "speed": _compact_number(circle_milling.retract.speed),
                "arc_side": circle_milling.retract.arc_side,
                "overlap": _compact_number(circle_milling.retract.overlap),
            },
        }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
