"""Slot milling contracts for PGMX synthesis."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..common.depth import (
    MillingDepthSpec,
    _normalize_milling_depth_spec,
    build_milling_depth_spec,
)
from ..common.geometry import (
    _CurveSpec,
    _build_identity_profile_placement,
    _curve_spec_from_profile_geometry,
    _profile_entry_exit_context,
)
from ..common.leads import (
    ApproachSpec,
    RetractSpec,
    _build_generated_approach_curve_for_profile,
    _build_generated_lift_curve_for_profile,
    _normalize_approach_spec,
    _normalize_retract_spec,
    build_approach_spec,
    build_retract_spec,
)
from ..common.piece import _normalize_plane_name, _workpiece_depth_name
from ..common.xml import (
    MILLING_NS,
    PGMX_NS,
    XSI_NS,
    _append_blank_name,
    _append_key,
    _append_node,
    _append_object_ref,
    _append_reference_key,
    _build_depth_expression,
    _build_property_expression,
    _build_working_step,
    _compact_number,
    _find_plane_ref,
    _qname,
    _reserve_ids,
    _set_xmlns,
    _text,
)
from ._common import (
    _feature_bottom_condition_type,
    _feature_depth_value,
    _normalize_side_of_feature,
    _toolpath_cut_z,
    _uses_feature_depth_expressions,
)
from ...tlgx import TlgxTool, load_tlgx
from .line import _build_line_geometry, _build_line_operation, _build_line_toolpath_profile

__all__ = [
    "ChannelSpec",
    "build_channel_spec",
    "_HydratedChannelSpec",
    "_append_channel",
    "_build_slot_side_feature",
    "_hydrate_channel_spec",
    "_normalize_channel_spec",
]


@lru_cache(maxsize=None)
def _tool_from_catalog(tool_name: str) -> TlgxTool:
    """La herramienta del catálogo `def.tlgx`, por NOMBRE.

    Por nombre y no por `tool_id`: Maestro **reasigna todos los identificadores**
    cada vez que regenera el catálogo (se vio dos veces el mismo día el
    2026-09-07, corridos +40 y +60). El `ID` sólo es coherente dentro del `.pgmx`
    que lleva su propio `def.tlgx` embebido. Ver `iso/docs/fixtures.md` §7.
    """

    catalogo = load_tlgx()
    tool = catalogo.get(tool_name)
    if tool is None:
        raise ValueError(
            f"La herramienta '{tool_name}' no existe en el catálogo de la máquina "
            f"(def.tlgx). Disponibles: {', '.join(sorted(catalogo))}."
        )
    return tool


@dataclass(frozen=True)
class ChannelSpec:
    """Ranura lineal `SlotSide` validada para Sierra Vertical X sobre `Top`."""

    start_x: float
    start_y: float
    end_x: float
    end_y: float
    feature_name: str = "Canal"
    plane_name: str = "Top"
    side_of_feature: str = "Center"
    tool_name: str = "082"
    # Derivados del catálogo en `_normalize_channel_spec`, NO son parámetros de
    # entrada: la ventana de Canal muestra `Anchura` en gris y el radio de extremo
    # no tiene campo. Ver `iso/docs/experiments/canal.md` §10 y §13.
    tool_id: str = ""
    tool_width: float = 0.0
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
    end_radius: float = 0.0            # derivado: radio del disco
    activate_cnc_correction: bool = False  # derivado: `false` con disco, `true` con fresa
    #: `Corrección en longitud` de la ventana (el cuarto botón de `Corrección
    #: herramienta`, que **se combina** con los otros tres). El manual de Xilog la
    #: llama «corrección en profundidad» y sólo la admite en fresas de disco.
    is_precise: bool = False
    #: `Invertir` de `Datos avanzados`. Da vuelta el RECORRIDO —no la geometría— y
    #: su único efecto en el ISO es que desaparece la cola del regreso, porque
    #: cambia cuál extremo es el punto final geométrico (`canal.md` §18).
    invert: bool = False
    #: `Canto a canto` de `Datos avanzados`: el canal deja de medir lo dibujado y
    #: cruza la pieza de borde a borde. El extremo pasa a `OpenSlotEndType`.
    edge_to_edge: bool = False
    #: `Extra dist. inicial` / `final`, que suman MAS ALLA del borde y aceptan
    #: negativos (recortan hacia adentro). Solo tienen efecto con `edge_to_edge`.
    overcut_length_input: float = 0.0
    overcut_length_output: float = 0.0
    slot_angle: float = 1.5707963267948966
    is_enabled_expr: Optional[str] = None

    @property
    def milling_strategy(self) -> None:
        return None


@dataclass(frozen=True)
class _HydratedChannelSpec:
    """Datos internos de serializacion que complementan un `ChannelSpec`."""

    spec: ChannelSpec
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
    def activate_cnc_correction(self) -> bool:
        return self.spec.activate_cnc_correction

    @property
    def is_precise(self) -> bool:
        return self.spec.is_precise

    @property
    def invert(self) -> bool:
        return self.spec.invert

    @property
    def edge_to_edge(self) -> bool:
        return self.spec.edge_to_edge

    @property
    def overcut_length_input(self) -> float:
        return self.spec.overcut_length_input

    @property
    def overcut_length_output(self) -> float:
        return self.spec.overcut_length_output

    @property
    def slot_angle(self) -> float:
        return self.spec.slot_angle

    @property
    def is_enabled_expr(self) -> Optional[str]:
        return self.spec.is_enabled_expr


def _acortamiento_en_longitud(state, spec) -> float:
    """El acortamiento por punta de `Corrección en longitud`, en mm.

    ``√( p · (2r − p) )`` — el avance horizontal que un disco de radio ``r``
    necesita para llegar a la profundidad ``p``. Derivado con dos profundidades
    sobre los ISO del lote D2 (`iso/docs/experiments/canal.md` §13 y §20), con
    coincidencia a quince dígitos.

    Sin `is_precise` la longitud pedida es la del FONDO de la ranura; con él, la
    de la superficie.
    """

    if not spec.is_precise:
        return 0.0
    radio = _tool_from_catalog(spec.tool_name).diameter / 2.0
    profundidad = float(state.depth) - float(_toolpath_cut_z(state, spec))
    if profundidad <= 0.0 or profundidad >= 2.0 * radio:
        return 0.0
    return math.sqrt(profundidad * (2.0 * radio - profundidad))


def _spec_acortada(state, spec):
    """La spec con los extremos corridos hacia adentro, para la TRAYECTORIA.

    La geometría de la feature NO se toca: sigue siendo la línea pedida. Lo que
    se acorta es el recorrido, que es lo que Maestro guarda acortado.
    """

    acortamiento = _acortamiento_en_longitud(state, spec)
    if acortamiento <= 0.0:
        return spec
    dx = float(spec.end_x) - float(spec.start_x)
    dy = float(spec.end_y) - float(spec.start_y)
    largo = math.hypot(dx, dy)
    if largo <= 2.0 * acortamiento:
        # ⛔ Maestro NO rechaza este caso: cruza los extremos y emite un corte
        # invertido de la longitud sobrante, en el lugar equivocado
        # (`canal.md` §23). Es el tercer caso de la excepción de fail-loud del
        # `CLAUDE.md` §4, y acá no se fabrica.
        raise ValueError(
            f"El canal mide {_compact_number(largo)} mm y `Corrección en longitud` "
            f"acorta {_compact_number(2.0 * acortamiento)} mm en total: los extremos "
            "se cruzarían. Maestro lo acepta y emite un corte invertido; no se sintetiza."
        )
    ux, uy = dx / largo, dy / largo
    return replace(
        spec,
        spec=replace(
            spec.spec,
            start_x=float(spec.start_x) + acortamiento * ux,
            start_y=float(spec.start_y) + acortamiento * uy,
            end_x=float(spec.end_x) - acortamiento * ux,
            end_y=float(spec.end_y) - acortamiento * uy,
        ),
    )


def _spec_canto_a_canto(state, spec):
    """La spec extendida de borde a borde de la pieza, con las distancias extra.

    Medido en el Grupo 10 (`canal.md` seccion 18): con `Canto a canto` el canal
    **ignora los extremos dibujados** y cruza la pieza entera; `Extra dist.
    inicial` corre el extremo del punto de INICIO geometrico y `Extra dist. final`
    el del FINAL, los dos mas alla del borde, y **aceptan negativos** (recortan
    hacia adentro).

    📌 **Diferencia declarada con Maestro, funcionalmente identica.** Maestro
    parametriza la geometria de la feature dejando el punto base en el borde y
    corriendo el rango --`8 -20 410 | 1 0 200 0 1 0 0`--; nosotros dejamos el rango
    en `[0, largo]` y movemos el punto base --`8 0 430 | 1 -20 200 0 1 0 0`--. Es
    **el mismo segmento**, y es la forma que Maestro usa para las otras tres
    curvas del mismo archivo. Vale la decision del 2026-08-16: el `.pgmx` se juzga
    funcionalmente identico, no byte a byte.
    """

    if not spec.edge_to_edge:
        return spec
    dx = float(spec.end_x) - float(spec.start_x)
    dy = float(spec.end_y) - float(spec.start_y)
    horizontal = math.isclose(dy, 0.0, abs_tol=1e-9)
    vertical = math.isclose(dx, 0.0, abs_tol=1e-9)
    if not (horizontal or vertical):
        # Los seis fixtures del Grupo 10 son horizontales. Una diagonal cortaria
        # el rectangulo de la pieza en otros puntos y no hay evidencia de como lo
        # resuelve Maestro: no se inventa.
        raise ValueError(
            "`Canto a canto` solo esta derivado para canales paralelos a un eje: "
            "no hay fixture de una diagonal."
        )
    extension = float(state.length) if horizontal else float(state.width)
    inicio = -float(spec.overcut_length_input) or 0.0  # sin cero negativo
    fin = extension + float(spec.overcut_length_output)
    if fin <= inicio:
        raise ValueError("Las distancias extra dejan el canal de longitud nula o negativa.")
    creciente = (dx > 0.0) if horizontal else (dy > 0.0)
    primero, ultimo = (inicio, fin) if creciente else (fin, inicio)
    nuevos = (
        {"start_x": primero, "end_x": ultimo}
        if horizontal
        else {"start_y": primero, "end_y": ultimo}
    )
    return replace(spec, spec=replace(spec.spec, **nuevos))


_LADO_OPUESTO = {"Left": "Right", "Right": "Left", "Center": "Center"}


def _spec_invertida(spec):
    """La spec con el recorrido dado vuelta, para la TRAYECTORIA.

    ⚠️ **También se invierte `side_of_feature`, y no es un descuido.** Maestro
    conserva el lado FÍSICO al invertir: `Corrección izquierda` + `Invertir` sigue
    dando `Y 201.9`, no `198.1` (medido en el Grupo 10). Como la compensación se
    calcula respecto de la dirección de recorrido, dar vuelta los extremos sin dar
    vuelta el lado movería la ranura al otro lado de la línea. Las dos inversiones
    juntas dejan el mismo desplazamiento con el recorrido al revés, que es lo que
    el `.pgmx` de Maestro guarda.

    El `SideOfFeature` que se SERIALIZA es el original: éste es un spec interno,
    sólo para generar el perfil.
    """

    if not spec.invert:
        return spec
    return replace(
        spec,
        spec=replace(
            spec.spec,
            start_x=float(spec.end_x),
            start_y=float(spec.end_y),
            end_x=float(spec.start_x),
            end_y=float(spec.start_y),
            side_of_feature=_LADO_OPUESTO.get(spec.side_of_feature, spec.side_of_feature),
        ),
    )


def _normalize_channel_spec(slot_milling: ChannelSpec) -> ChannelSpec:
    if math.isclose(float(slot_milling.start_x), float(slot_milling.end_x), abs_tol=1e-9) and math.isclose(
        float(slot_milling.start_y),
        float(slot_milling.end_y),
        abs_tol=1e-9,
    ):
        raise ValueError("La ranura no puede tener longitud cero.")
    tool_name = (slot_milling.tool_name or "082").strip() or "082"
    tool = _tool_from_catalog(tool_name)
    return replace(
        slot_milling,
        start_x=float(slot_milling.start_x),
        start_y=float(slot_milling.start_y),
        end_x=float(slot_milling.end_x),
        end_y=float(slot_milling.end_y),
        plane_name=_normalize_plane_name(slot_milling.plane_name),
        side_of_feature=_normalize_side_of_feature(slot_milling.side_of_feature),
        tool_id=tool.tool_id,
        tool_name=tool_name,
        tool_width=tool.cutting_width,
        security_plane=float(slot_milling.security_plane),
        depth_spec=_normalize_milling_depth_spec(slot_milling.depth_spec),
        approach=_normalize_approach_spec(slot_milling.approach),
        retract=_normalize_retract_spec(slot_milling.retract),
        material_position=(slot_milling.material_position or "Left").strip() or "Left",
        side_offset=float(slot_milling.side_offset),
        end_radius=tool.diameter / 2.0,
        activate_cnc_correction=tool.uses_cnc_correction,
        is_precise=bool(slot_milling.is_precise),
        invert=bool(slot_milling.invert),
        edge_to_edge=bool(slot_milling.edge_to_edge),
        overcut_length_input=float(slot_milling.overcut_length_input),
        overcut_length_output=float(slot_milling.overcut_length_output),
        slot_angle=float(slot_milling.slot_angle),
    )


def _hydrate_channel_spec(
    slot_milling: ChannelSpec,
    source_pgmx_path: Optional[Path],
) -> _HydratedChannelSpec:
    del source_pgmx_path
    return _HydratedChannelSpec(spec=_normalize_channel_spec(slot_milling))


def _build_slot_side_feature(
    state,
    spec: _HydratedChannelSpec,
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
    # El tipo de extremo lo elige la HERRAMIENTA: un disco deja el corte curvo de su
    # radio (`Woodruff`) y una fresa el extremo redondo de su punta (`Radiused`).
    # Medido sobre el par 082/E004 del Grupo 11 (`canal.md` §10).
    es_disco = _tool_from_catalog(spec.tool_name).is_blade
    for _ in range(2):
        slot_end = _append_node(
            end_conditions,
            MILLING_NS,
            "SlotEndType",
            attrib={
                f"{{{XSI_NS}}}type": (
                    "a:OpenSlotEndType"
                    if spec.edge_to_edge
                    else ("a:WoodruffSlotEndType" if es_disco else "a:RadiusedSlotEndType")
                )
            },
        )
        _set_xmlns(slot_end, "a", MILLING_NS)
        if es_disco and not spec.edge_to_edge:
            _append_node(slot_end, MILLING_NS, "Radius", _compact_number(spec.end_radius))
    _append_node(feature, PGMX_NS, "IsGeomSameDirection", "false" if spec.invert else "true")
    _append_node(feature, PGMX_NS, "IsPrecise", "true" if spec.is_precise else "false")
    _append_node(feature, PGMX_NS, "MaterialPosition", spec.material_position)
    # El typo «Lenght» es de Maestro.
    _append_node(feature, PGMX_NS, "OvercutLenghtInput", _compact_number(spec.overcut_length_input))
    _append_node(feature, PGMX_NS, "OvercutLenghtOutput", _compact_number(spec.overcut_length_output))
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


def _append_channel(root: ET.Element, state, spec: _HydratedChannelSpec) -> None:
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
    has_enabled_expr = spec.is_enabled_expr is not None
    n_total = 4 + (2 if uses_depth_expressions else 0) + has_enabled_expr
    reserved_ids = _reserve_ids(root, n_total, spec.preferred_id_start)
    geometry_id, operation_id, feature_id, step_id = reserved_ids[:4]
    i = 4
    start_expression_id = end_expression_id = None
    if uses_depth_expressions:
        start_expression_id = reserved_ids[i]; i += 1
        end_expression_id = reserved_ids[i]; i += 1
    enabled_expr_id = reserved_ids[i] if has_enabled_expr else None
    spec_extendida = _spec_canto_a_canto(state, spec)
    spec_trayectoria = _spec_invertida(_spec_acortada(state, spec_extendida))
    generated_toolpath_profile = _build_line_toolpath_profile(
        float(state.depth), _toolpath_cut_z(state, spec), spec_trayectoria
    )
    toolpath_start, toolpath_end, _, _ = _profile_entry_exit_context(generated_toolpath_profile)
    approach_curve = spec.approach_curve
    if approach_curve is None:
        approach_curve = _build_generated_approach_curve_for_profile(state, spec, generated_toolpath_profile)
    lift_curve = spec.lift_curve
    if lift_curve is None:
        lift_curve = _build_generated_lift_curve_for_profile(state, spec, generated_toolpath_profile)
    trajectory_curve = spec.trajectory_curve or _curve_spec_from_profile_geometry(generated_toolpath_profile)

    geometries.append(_build_line_geometry(geometry_id, plane_id, plane_object_type, spec_extendida))
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
    if has_enabled_expr and enabled_expr_id is not None:
        expressions.append(
            _build_property_expression(
                enabled_expr_id,
                step_id,
                "ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep",
                "IsEnabled",
                spec.is_enabled_expr,
            )
        )


def build_channel_spec(
    *,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    feature_name: Optional[str] = None,
    plane_name: Optional[str] = None,
    side_of_feature: Optional[str] = None,
    tool_name: Optional[str] = None,
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
    is_precise: Optional[bool] = None,
    invert: Optional[bool] = None,
    edge_to_edge: Optional[bool] = None,
    overcut_length_input: Optional[float] = None,
    overcut_length_output: Optional[float] = None,
    slot_angle: Optional[float] = None,
    is_enabled_expr: Optional[str] = None,
) -> ChannelSpec:
    """Construye una ranura lineal `SlotSide` compatible con Sierra Vertical X."""

    depth_spec = build_milling_depth_spec(
        is_through=False if is_through is None and target_depth is None and extra_depth is None else is_through,
        target_depth=10.0 if is_through is None and target_depth is None and extra_depth is None else target_depth,
        extra_depth=extra_depth,
    )
    return _normalize_channel_spec(
        ChannelSpec(
            start_x=float(start_x),
            start_y=float(start_y),
            end_x=float(end_x),
            end_y=float(end_y),
            feature_name=(feature_name or "Canal").strip() or "Canal",
            plane_name=_normalize_plane_name(plane_name),
            side_of_feature=_normalize_side_of_feature(side_of_feature),
            tool_name=(tool_name or "082").strip() or "082",
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
            is_precise=bool(is_precise),
            invert=bool(invert),
            edge_to_edge=bool(edge_to_edge),
            overcut_length_input=0.0 if overcut_length_input is None else float(overcut_length_input),
            overcut_length_output=0.0 if overcut_length_output is None else float(overcut_length_output),
            slot_angle=1.5707963267948966 if slot_angle is None else float(slot_angle),
            is_enabled_expr=None if is_enabled_expr is None else str(is_enabled_expr).strip() or None,
        )
    )
