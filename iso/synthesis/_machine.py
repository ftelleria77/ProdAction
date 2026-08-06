"""Constantes de máquina SCM Group validadas contra ISO Maestro (lotes N001-N003)."""

from __future__ import annotations
import struct
from dataclasses import dataclass
from typing import Sequence

from ._machine_config import (
    field_origin, maestro_setting_float, param_float, phead_float, phead_shf, spindle_shf,
)
from ._tool_catalog import tool_geometry


def _f32(x: float) -> float:
    """Redondeo a float32 (single precision), tal como Maestro guarda el origen del campo.
    Por eso los %Or[0] "raros" (-1515599.976) NO son calibración: son float32(origen)×1000."""
    return struct.unpack("f", struct.pack("f", x))[0]

# ---------------------------------------------------------------------------
# Constantes globales de máquina
# ---------------------------------------------------------------------------

# Campo de trabajo activo (el que mecaniza). Hoy SOLO HG está calibrado válido; EF/AB/DC tienen
# la calibración inicial invalidada por intervenciones técnicas (ver bitácora de la máquina).
# Cuando se recalibre EF, el pendular cambiará este valor (o lo elegirá la operación).
ACTIVE_FIELD: str = "HG"
# Campos con el modelo de origen/SHF/EDK derivado y byte-validado (N019/N020/N021) para TOP/router:
# los 4 de la grilla 2×2. Las CARAS laterales (side drills) por ahora solo en HG (falta derivar el
# SHF por-cara espejado para los otros campos) → guarda aparte en _reader.
SUPPORTED_FIELDS: tuple[str, ...] = ("HG", "EF", "DC", "AB")
# Caras laterales: el SHF por-cara (side_shf) ya está derivado y byte-validado en los 4 campos
# (N019/N020/N021). El toolpath/g53/MLV2 son field-independientes.
SIDE_SUPPORTED_FIELDS: tuple[str, ...] = ("HG", "EF", "DC", "AB")
# SHF[X]/SHF[Y] de máquina = origen (X, Y) del campo activo, leídos de fields.cfg (NO horneados).
# HG = (0.000, -1515.600); byte-idénticos a los SHF de Maestro. Simétricos: el origen X del campo
# entra en SHF[X] igual que el Y en SHF[Y] (SHF[X] = SHF_X_MACHINE - pieza, SHF[Y] = SHF_Y_MACHINE
# + pieza). Con HG.x = 0 el término X es 0 (no se ve); en EF (x=-3688) NO será 0 — falta validar
# con un fixture en un campo de X≠0 cómo entra exactamente ese offset (HG.x=0 hoy lo oculta).
SHF_X_MACHINE, SHF_Y_MACHINE = field_origin(ACTIVE_FIELD)

# ---------------------------------------------------------------------------
# Modelo del origen de trabajo por CAMPO (N019/N020/N021, grilla 2×2 espejada).
# Cada eje es independiente; el régimen depende del origen del campo en ese eje:
#   - "near" (field_coord == 0): lado del cero de máquina (Right en X, Back en Y). El origen es
#     DERIVADO de la pieza: SHF = -D; of[pre] = -D×1000; ofX[blk] = -(D+origin)×1000.
#   - "far"  (field_coord <  0): lado lejano (Left en X, Front en Y). El origen es la ESQUINA del
#     campo: SHF[pre] = field; SHF[blk] = field+origin; of = float32(field)×1000 (const).
# El selector EDK sigue el eje X: near-X→13, far-X→10. (Caras: SIDE_FACE es igual en todo campo.)
# `ctx` es un PieceCtx (duck-typed: .field/.DX/.DY/.origin_x/.origin_y). field_origin(area) toma
# el origen del 1er campo del par (HG→H, EF→E, DC→D, AB→A).


def or_ofx(ctx, block: bool) -> float:
    """%Or[0].ofX (µm) del campo. Near: -float32(D[+origin])×1000. Far: float32(field_x)×1000.

    El float32 en NEAR es del ensayo general (2026-08-05, 100 archivos DeMarco/Cazaux):
    Maestro emite `-1001400.024` para DX+origin=1001.4 — float32(1001.4)×1000, la MISMA
    regla ya derivada para el far/OR_OFY (todo origen pasa por single precision). Los
    lotes N no podían verlo: sus medidas (305, 310, 400…) son EXACTAS en float32 —
    quinto punto ciego por construcción del corpus propio."""
    fx, _ = field_origin(ctx.field)
    if fx == 0.0:
        return -_f32(ctx.DX + (ctx.origin_x if block else 0.0)) * 1000.0
    return _f32(fx) * 1000.0


def or_ofy(ctx, block: bool) -> float:
    """%Or[0].ofY (µm) del campo. Near (back): -float32(DY[+origin_y])×1000. Far (front):
    float32(field_y)×1000. (El bloque suma origin_y en near, igual que ofX en near-X; en
    far no depende del bloque. El float32 en near: misma regla que or_ofx — simétrica y
    con la misma evidencia; los DY enteros del corpus son exactos en f32 y no la muestran.
    ofZ queda SIN f32: ningún archivo lo exhibió aún — los DZ reales son enteros.)"""
    _, fy = field_origin(ctx.field)
    if fy == 0.0:
        return -_f32(ctx.DY + (ctx.origin_y if block else 0.0)) * 1000.0
    return _f32(fy) * 1000.0


def shf_x(ctx, block: bool) -> float:
    """SHF[X] (mm) del campo. Near: -DX. Far: field_x [+origin_x en bloque]."""
    fx, _ = field_origin(ctx.field)
    return (fx - ctx.DX) if fx == 0.0 else (fx + (ctx.origin_x if block else 0.0))


def shf_y(ctx, block: bool) -> float:
    """SHF[Y] (mm) del campo. Near (back): -DY. Far (front): field_y [+origin_y en bloque]."""
    _, fy = field_origin(ctx.field)
    return (fy - ctx.DY) if fy == 0.0 else (fy + (ctx.origin_y if block else 0.0))


def edk_field(ctx) -> int:
    """Selector de campo EDK: sigue el eje X. Right (near-X)→13, Left (far-X)→10."""
    fx, _ = field_origin(ctx.field)
    return 13 if fx == 0.0 else 10


def side_shf(ctx, face: str) -> tuple[float, float]:
    """SHF[X]/SHF[Y] de MLV1 de un taladro LATERAL, por cara y por campo (N019/N020/N021).
    Mismo modelo near/far que el top, con el borde según la cara: en X la cara "especial" es Back
    (usa el borde opuesto al resto); en Y es Left. Near usa `field - borde`; far usa `field + borde`.
    Byte-idéntico al _shf_mlv1 de HG y generalizado a los 4 campos; el toolpath/g53/MLV2 no cambian."""
    fx, fy = field_origin(ctx.field)
    if fx == 0.0:
        sx = fx - (ctx.origin_x if face == "Back" else ctx.DX)
    else:
        sx = fx + (ctx.DX if face == "Back" else ctx.origin_x)
    if fy == 0.0:
        sy = fy - (ctx.origin_y if face == "Left" else ctx.DY)
    else:
        sy = fy + (ctx.DY if face == "Left" else ctx.origin_y)
    return sx, sy


# Margen de seguridad del g53 lateral (el +20 fijo). Candidato confirmado por Fermín: la Cabeza 1
# (boring head) tiene Configuración 1 Eje Z = -20 en pheads.cfg → SECURITY_SIDE = -(Config1 Z).
# Match exacto y byte-validado; revisar si esa config cambia.
SECURITY_SIDE: float = -phead_float(1, 5)  # Config1 Eje Z de la Cabeza 1 (índice 5) = -20 → 20
SIDE_APPROACH_FLOOR: float = 5.0   # Mínimo del plano de seguridad lateral (N016 sp=2 → -70; N017
                                   # Right/Back idem). Constante del ciclo de Maestro: no tiene clave
                                   # en Programaciones.settingsx (que sí trae SecurityDistance=20, el
                                   # default del sp) → Tier D. (El piso del g53 SÍ es derivado: el
                                   # ToolOffsetLength del tool que se retrae — N016/N017.)
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
SIDE_FEED_DEFAULT: float = _SIDE_TOOL.feed_default  # = min(descent_std, feed_std)×1000 = 2000 (058)
SIDE_SPINDLE: int = _SIDE_TOOL.spindle_std   # husillo lateral (058 spindle_std=6000); override ignorado (N011)

# Retorno "en la pieza" (InPiece) de la multipasada del fresado: la vuelta va a z_pasada + este
# valor. Sourced de Programaciones.settingsx MillingRetractDistance (= 10). (N025 uni_piece:
# pasada -4 → retorno +6; pasada -8 → +2.)
MILLING_RETRACT: float = maestro_setting_float("MillingRetractDistance")

# Park Z de máquina ← Params.cfg [ax2] (eje Z) AP_PARKQTA / 1000 (= 201). Es machine config:
# el Xn no tiene Z. (En [ax0]=X, AP_PARKQTA=0 → el X park NO sale de acá, sale del Xn; N015.)
Z_PARK: float = param_float("Params.cfg", "ax2", "AP_PARKQTA") / 1000.0

# Or[0].ofX (origen de trabajo X, en µm) NO es constante: depende de la pieza. Derivado con N018
# (geometría variada): preamble = -DX×1000; bloque de operación = -(DX + origin_x)×1000. El viejo
# OR_OFX=-310000 era sobreajuste a la pieza 305/5 (bug latente; daba -310000 para toda pieza).
# Se calcula inline en _preamble/_top_drill/_router/_side_drill. (ofY sí es constante: OR_OFY.)


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
def _top_tool(etk6: int, etk0: int) -> _TopToolData:
    g = tool_geometry(f"{etk6:03d}")
    shf_x, shf_y, shf_z = spindle_shf(etk6)  # = -(Offset X/Y/Z) del mandril (spindles.cfg)
    # spindle y feed por defecto salen del catálogo: spindle_std, y feed_default =
    # min(descent_std, feed_std)×1000. Ya NO horneados.
    return _TopToolData(
        etk6=etk6, etk0=etk0, spindle=g.spindle_std, feed=g.feed_default, tlc=g.tool_offset_length,
        shf_x=shf_x, shf_y=shf_y, shf_z=shf_z,
        max_feed=g.feed_max, max_spindle=g.spindle_max, max_sink=g.sinking_length,
    )


TOP_TOOL: dict[float, _TopToolData] = {
    4.0:  _top_tool(etk6=6, etk0=32),
    5.0:  _top_tool(etk6=5, etk0=16),
    8.0:  _top_tool(etk6=1, etk0=1),
    15.0: _top_tool(etk6=2, etk0=2),
    20.0: _top_tool(etk6=3, etk0=4),
    35.0: _top_tool(etk6=4, etk0=8),
}

# Brocas cónicas (punta de lanza) por diámetro. Hoy la máquina solo tiene la tool 007
# en D5 (auto-seleccionada en D5 + pasante salvo override a punta plana). Valores N007;
# etk0=64=2^(etk6-1) mantiene el invariante. Instalar otras cónicas cambia config + def.tlgx.
#
# El discriminador plano/cónico es la punta (drill_family), que el adapter ahora deriva bien
# (de BottomCondition/IsFlat en pasantes). NO se usa la herramienta seleccionada: la forma
# canónica del .pgmx no trae herramienta (Maestro la resuelve al postprocesar). (N007)
TOP_TOOL_CONICAL: dict[float, _TopToolData] = {
    5.0:  _top_tool(etk6=7, etk0=64),
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
    shf_x_mlv2: float   # = -OffsetX del mandril (spindles.cfg), no horneado
    shf_y_mlv2: float   # = -OffsetY
    shf_z_mlv2: float   # = -OffsetZ


def _side_face(etk6: int, etk0: int, etk8: int) -> _SideFaceData:
    """Cara lateral: el SHF de máquina = -(Offset X/Y/Z) del mandril (= ETK[6]) en spindles.cfg.
    Los offsets son montaje de husillo (las 4 brocas son idénticas en def.tlgx)."""
    sx, sy, sz = spindle_shf(etk6)
    return _SideFaceData(etk6=etk6, etk0=etk0, etk8=etk8,
                         shf_x_mlv2=sx, shf_y_mlv2=sy, shf_z_mlv2=sz)


SIDE_FACE: dict[str, _SideFaceData] = {
    "Left":  _side_face(etk6=61, etk0=2147483648, etk8=3),
    "Right": _side_face(etk6=60, etk0=2147483648, etk8=2),
    "Front": _side_face(etk6=58, etk0=1073741824, etk8=5),
    "Back":  _side_face(etk6=59, etk0=1073741824, etk8=4),
}


def side_transition_g53_z(
    dz: float, faces: Sequence[tuple[str, float]], head_tlc: float,
) -> float:
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

    Fórmula (N016 Top→Side + N017 Right/Back, config canónica)::

        G53 Z = DZ + SECURITY_SIDE + max( head_tlc, max_i( sp_i + shf_z(cara_i) ) )

    El ``max`` interno despeja el peor caso (plano de seguridad + offset de mandril) de las
    caras de la transición; el piso es ``head_tlc`` = ToolOffsetLength del tool que está en el
    cabezal y se retrae (vertical 77 en Top→Side; lateral 65 en Side→Side; router 107.2). NO es
    una constante: sale del catálogo (N016/N017 confirman 77 con el top vertical).
    """
    worst = max(sp + SIDE_FACE[face].shf_z_mlv2 for face, sp in faces)
    return dz + SECURITY_SIDE + max(worst, head_tlc)

# Prioridad de ejecución por cara lateral (Maestro reordena por esta prioridad)
FACE_PRIORITY: dict[str, int] = {"Front": 0, "Left": 1, "Right": 2, "Back": 3}

# Router / cabezal (electromandril). Lo específico de la FRESA (slot ATC, ETK[9], spindle, TLC,
# feeds) se deriva por herramienta en `_router.py` (T{N}/ETK[9]={N} = E00N→N; resto del catálogo).
# Acá solo lo del CABEZAL (constante para toda fresa): ETK[6]/ETK[18] y el SHF.
ROUTER_ETK6: int = 1
ROUTER_ETK18: int = 1
# SHF del router = -(Configuración 0) de su cabeza en pheads.cfg. El router/electromandril es la
# Cabeza 3 (Cabezas Operadoras/PHEADS) → (32.05, -246.65, -125.30). No horneado.
ROUTER_PHEAD: int = 3
ROUTER_SHF_X, ROUTER_SHF_Y, ROUTER_SHF_Z = phead_shf(ROUTER_PHEAD)
