"""Constantes de máquina SCM Group validadas contra ISO Maestro (lotes N001-N003)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from ._tool_catalog import tool_geometry

# ---------------------------------------------------------------------------
# Constantes globales de máquina
# ---------------------------------------------------------------------------

OR_OFY: float = -1515599.976      # Or[0].ofY en µm (posición Y de mesa)
SHF_Y_MACHINE: float = -1515.600  # En mm; equivalente a OR_OFY/1000

TLC_LATERAL: float = 37.0         # Tool Length Constant cabezales laterales (g53/shf)
SECURITY_SIDE: float = 20.0       # Margen de seguridad taladro lateral (mm)
SIDE_SECURITY_FLOOR: float = 5.0  # Piso del plano de seguridad efectivo (validado N003)
# Geometría/límites de la broca lateral (058) — del catálogo (def.tlgx), no horneados.
# - tool_offset_length (65): offset del CORTE lateral. approach fijo = -(TLC_CUT+SEC);
#   cut = -TLC_CUT + depth. (N011: d28→-37, d15→-50)
# - sinking_length (30): hundimiento máximo. Pasante lateral atraviesa el panel (dim cruzada);
#   si la profundidad efectiva supera esto, Maestro da error.
# - feed_max (3000): tope de avance lateral.
_SIDE_TOOL = tool_geometry("058")
TLC_LATERAL_CUT: float = _SIDE_TOOL.tool_offset_length
SIDE_MAX_DEPTH: float = _SIDE_TOOL.sinking_length
SIDE_FEED_MAX: float = _SIDE_TOOL.feed_max
SIDE_FEED_DEFAULT: float = 2000.0  # mm/min sin override (MEDIDO del ISO; def.tlgx Std no es fiable)
SIDE_SPINDLE: int = 6000           # husillo lateral fijo; el override de spindle se ignora (N011)

Z_PARK: float = 201.0             # Park Z de máquina (Params.cfg [ax2] AP_PARKQTA/1000)
X_PARK: float = -3700.0           # Park X de máquina

OR_OFX: float = -310000.0         # Or[0].ofX en µm (constante)


# ---------------------------------------------------------------------------
# Datos por diámetro (Top Drill)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _TopToolData:
    etk6: int
    etk0: int       # máscara de husillo: medido = 2^(etk6-1) en los 6 puntos N004
    spindle: int   # rpm por defecto (sin override)
    feed: float    # mm/min por defecto (sin override)
    tlc: float     # ToolOffsetLength mm (def.tlgx ToolOffsetLength)
    shf_x: float   # MLV2
    shf_y: float   # MLV2
    shf_z: float   # MLV2
    max_feed: float    # tope de feed mm/min (def.tlgx FeedRate.Maximum×1000; clamp override). N010
    max_spindle: int   # tope de husillo rpm (def.tlgx SpindleSpeed.Maximum; clamp override). N010
    max_sink: float    # hundimiento máximo mm (def.tlgx SinkingLength). Profundidad/espesor > → error. N013


# Tabla por diámetro. Lo MEDIDO (no derivable del catálogo): etk6 (nº de herramienta),
# etk0 (máscara de husillo = 2^(etk6-1)), spindle/feed por defecto (def.tlgx Std no es fiable;
# se miden del ISO) y shf_x/y/z (offsets del husillo, viven en spindles.cfg). Lo de TRAZA/
# PROFUNDIDAD (tlc, max_sink, max_feed, max_spindle) NO se hornea: sale del tool_catalog.csv
# (= def.tlgx) vía `tool_geometry`. Para agregar un diámetro: medir etk0/feed/spindle/shf del
# ISO; el resto lo aporta el catálogo.
def _top_tool(etk6: int, etk0: int, spindle: int, feed: float,
              shf_x: float, shf_y: float, shf_z: float) -> _TopToolData:
    g = tool_geometry(f"{etk6:03d}")
    return _TopToolData(
        etk6=etk6, etk0=etk0, spindle=spindle, feed=feed, tlc=g.tool_offset_length,
        shf_x=shf_x, shf_y=shf_y, shf_z=shf_z,
        max_feed=g.feed_max, max_spindle=g.spindle_max, max_sink=g.sinking_length,
    )


TOP_TOOL: dict[float, _TopToolData] = {
    4.0:  _top_tool(etk6=6, etk0=32, spindle=6000, feed=2000.0, shf_x=-96.0, shf_y=0.0,  shf_z=-0.200),
    5.0:  _top_tool(etk6=5, etk0=16, spindle=6000, feed=2000.0, shf_x=-64.0, shf_y=0.0,  shf_z=-0.950),
    8.0:  _top_tool(etk6=1, etk0=1,  spindle=6000, feed=2000.0, shf_x=0.0,   shf_y=0.0,  shf_z=0.0),
    15.0: _top_tool(etk6=2, etk0=2,  spindle=4000, feed=1000.0, shf_x=0.0,   shf_y=32.0, shf_z=-0.200),
    20.0: _top_tool(etk6=3, etk0=4,  spindle=4000, feed=1000.0, shf_x=0.0,   shf_y=64.0, shf_z=-0.250),
    35.0: _top_tool(etk6=4, etk0=8,  spindle=4000, feed=1000.0, shf_x=-32.0, shf_y=0.0,  shf_z=-0.350),
}

# Brocas cónicas (punta de lanza) por diámetro. Hoy la máquina solo tiene la tool 007
# en D5 (auto-seleccionada en D5 + pasante salvo override a punta plana). Valores N007;
# etk0=64=2^(etk6-1) mantiene el invariante. Instalar otras cónicas cambia config + def.tlgx.
#
# El discriminador plano/cónico es la punta (drill_family), que el adapter ahora deriva bien
# (de BottomCondition/IsFlat en pasantes). NO se usa la herramienta seleccionada: la forma
# canónica del .pgmx no trae herramienta (Maestro la resuelve al postprocesar). (N007)
TOP_TOOL_CONICAL: dict[float, _TopToolData] = {
    5.0:  _top_tool(etk6=7, etk0=64, spindle=6000, feed=2000.0, shf_x=-128.0, shf_y=0.0, shf_z=0.0),
}

# Índice por etk6 (= ToolKey.Name del .pgmx con padding). Permite resolver por la
# herramienta ya seleccionada cuando el .pgmx la trae (forma post-tool-selection).
TOP_TOOL_BY_ETK6: dict[int, _TopToolData] = {
    t.etk6: t for t in (*TOP_TOOL.values(), *TOP_TOOL_CONICAL.values())
}


def top_tool_or_none(diameter: float, drill_family: str,
                     tool_name: str = "") -> _TopToolData | None:
    """Resuelve la herramienta vertical, o None si no está soportada.

    1) Si el .pgmx trae la herramienta resuelta (tool_name = etk6), se usa esa.
    2) Si no (forma canónica sin herramienta), se resuelve por punta + diámetro:
       `Conical` → tabla de cónicas; el resto → tabla plana.
    """
    if tool_name:
        try:
            etk6 = int(tool_name)
        except ValueError:
            etk6 = None
        if etk6 is not None and etk6 in TOP_TOOL_BY_ETK6:
            return TOP_TOOL_BY_ETK6[etk6]
    table = TOP_TOOL_CONICAL if drill_family == "Conical" else TOP_TOOL
    return table.get(diameter)


def resolve_top_tool(diameter: float, drill_family: str,
                     tool_name: str = "") -> _TopToolData:
    tool = top_tool_or_none(diameter, drill_family, tool_name)
    if tool is None:
        raise KeyError(f"herramienta vertical no soportada: Ø{diameter}, "
                       f"familia {drill_family!r}, tool {tool_name!r}")
    return tool


def effective_side_feed(feedrate: float) -> float:
    """Feed lateral (mm/min): sin override → default; con override → feedrate(m/min)×1000
    clampado al máximo lateral. El husillo lateral es fijo (SIDE_SPINDLE); el override de
    spindle se ignora (N011)."""
    if feedrate <= 0:
        return SIDE_FEED_DEFAULT
    return min(feedrate * 1000.0, SIDE_FEED_MAX)


def effective_top_feed_spindle(tool: _TopToolData, feedrate: float,
                               spindle: float) -> tuple[float, int]:
    """Feed (mm/min) y husillo (rpm) efectivos de un taladro vertical.

    Sin override (0) → defaults de la tool. Con override: feedrate viene en m/min →
    ×1000, y ambos se clampan al máximo de la tool (N009/N010: el feed clampa a
    max_feed; el husillo a max_spindle, igual que la corrección de la UI de Maestro).
    """
    feed = tool.feed if feedrate <= 0 else min(feedrate * 1000.0, tool.max_feed)
    rpm = tool.spindle if spindle <= 0 else min(int(round(spindle)), tool.max_spindle)
    return feed, rpm


# ---------------------------------------------------------------------------
# Datos por cara (Side Drill)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _SideFaceData:
    etk6: int
    etk0: int
    etk8: int
    shf_x_mlv2: float
    shf_y_mlv2: float
    shf_z_mlv2: float   # offset Z del mandril lateral (= -fpos5 de spindles.cfg)


SIDE_FACE: dict[str, _SideFaceData] = {
    "Left":  _SideFaceData(etk6=61, etk0=2147483648, etk8=3,
                           shf_x_mlv2=-118.0, shf_y_mlv2=-32.0,  shf_z_mlv2=66.3),
    "Right": _SideFaceData(etk6=60, etk0=2147483648, etk8=2,
                           shf_x_mlv2=-66.9,  shf_y_mlv2=-32.0,  shf_z_mlv2=66.45),
    "Front": _SideFaceData(etk6=58, etk0=1073741824, etk8=5,
                           shf_x_mlv2=32.0,   shf_y_mlv2=-21.75, shf_z_mlv2=66.5),
    "Back":  _SideFaceData(etk6=59, etk0=1073741824, etk8=4,
                           shf_x_mlv2=32.0,   shf_y_mlv2=29.5,   shf_z_mlv2=66.5),
}


def _eff_security_plane(security_plane: float) -> float:
    """Plano de seguridad efectivo: piso duro de 5 mm (codo validado en N003)."""
    return max(security_plane, SIDE_SECURITY_FLOOR)


def side_transition_g53_z(dz: float, faces: Sequence[tuple[str, float]]) -> float:
    """G53 Z absoluto de máquina al entrar a una cara lateral en una transición.

    Parameters
    ----------
    dz:
        ``ctx.DZ`` = ``origin_z + espesor`` (cota Z superior de la pieza).
    faces:
        Caras involucradas en la transición con su ``security_plane``:
        ``[(dest_face, dest_sp)]`` viniendo de Top/Router (el origen no aporta
        mandril lateral), o ``[(prev_face, prev_sp), (dest_face, dest_sp)]`` entre
        dos caras laterales.

    Fórmula validada empíricamente 20/20 (lotes N001 + N002 + N003)::

        G53 Z = DZ + SECURITY_SIDE + max_i( eff(sp_i) + shf_z(cara_i) )
        eff(sp) = max(sp, SIDE_SECURITY_FLOOR)

    El ``max`` despeja el peor caso de plano de seguridad + offset de mandril de
    las caras de la transición (la que sale y la que entra).
    """
    return dz + SECURITY_SIDE + max(
        _eff_security_plane(sp) + SIDE_FACE[face].shf_z_mlv2
        for face, sp in faces
    )

# Prioridad de ejecución por cara lateral (Maestro reordena por esta prioridad)
FACE_PRIORITY: dict[str, int] = {"Front": 0, "Left": 1, "Right": 2, "Back": 3}

# Router E004
ROUTER_ETK6: int = 1
ROUTER_ETK9: int = 4
ROUTER_ETK18: int = 1
ROUTER_SPINDLE: int = 18000
ROUTER_ATC_SLOT: int = 4
ROUTER_TLC: float = tool_geometry("E004").tool_offset_length  # del catálogo (def.tlgx), = 107.2
ROUTER_SHF_X: float = 32.050      # offsets del husillo (spindles.cfg), aún no sourced
ROUTER_SHF_Y: float = -246.650
ROUTER_SHF_Z: float = -125.300
