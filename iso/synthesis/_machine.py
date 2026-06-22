"""Constantes de máquina SCM Group validadas contra ISO Maestro (lotes N001-N003)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

# ---------------------------------------------------------------------------
# Constantes globales de máquina
# ---------------------------------------------------------------------------

OR_OFY: float = -1515599.976      # Or[0].ofY en µm (posición Y de mesa)
SHF_Y_MACHINE: float = -1515.600  # En mm; equivalente a OR_OFY/1000

TLC_LATERAL: float = 37.0         # Tool Length Constant cabezales laterales
SECURITY_SIDE: float = 20.0       # Margen de seguridad taladro lateral (mm)
SIDE_SECURITY_FLOOR: float = 5.0  # Piso del plano de seguridad efectivo (validado N003)

Z_PARK: float = 201.0             # Park Z de máquina (Params.cfg [ax2] AP_PARKQTA/1000)
X_PARK: float = -3700.0           # Park X de máquina

OR_OFX: float = -310000.0         # Or[0].ofX en µm (constante)


# ---------------------------------------------------------------------------
# Datos por diámetro (Top Drill)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _TopToolData:
    etk6: int
    etk0: int
    spindle: int   # rpm
    feed: float    # mm/min
    tlc: float     # ToolOffsetLength mm (def.tlgx ToolOffsetLength)
    shf_x: float   # MLV2
    shf_y: float   # MLV2
    shf_z: float   # MLV2


TOP_TOOL: dict[float, _TopToolData] = {
    5.0:  _TopToolData(etk6=5,  etk0=16, spindle=6000, feed=2000.0, tlc=77.0,
                       shf_x=-64.0, shf_y=0.0, shf_z=-0.950),
    8.0:  _TopToolData(etk6=1,  etk0=1,  spindle=6000, feed=2000.0, tlc=77.0,
                       shf_x=0.0,   shf_y=0.0, shf_z=0.0),
    15.0: _TopToolData(etk6=2,  etk0=2,  spindle=4000, feed=1000.0, tlc=77.0,
                       shf_x=0.0,   shf_y=32.0, shf_z=-0.200),
}


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
ROUTER_TLC: float = 107.2         # ToolOffsetLength E004 (def.tlgx XilogSpindleUnitTool)
ROUTER_SHF_X: float = 32.050
ROUTER_SHF_Y: float = -246.650
ROUTER_SHF_Z: float = -125.300
