"""Renderizado de bloques de taladro lateral (Side Drill) para ISO Xilog Plus."""

from __future__ import annotations

from dataclasses import dataclass
from pgmx.synthesis.drilling.single import DrillSpec

from ._machine import (
    SIDE_APPROACH_FLOOR, SIDE_FACE, SIDE_SPINDLE,
    TLC_LATERAL_CUT, Z_PARK,
    effective_side_feed,
    or_ofx, or_ofy, side_shf,
    side_transition_g53_z,
)
from ._reader import PieceCtx, side_effective_depth


@dataclass
class _SideDrillState:
    spindle: int
    etk0: int | None = None
    current_face: str | None = None
    prev_approach: float = 0.0
    prev_perp: float = 0.0
    # security_plane del último taladro de la cara en curso (para el max de transición)
    prev_security_plane: float = 20.0


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_side_drill(
    drills: list[DrillSpec],
    ctx: PieceCtx,
    prev_family: str | None,  # None=side is first family, "top", "router"
    top_spindle: int,
    prev_tlc: float = 0.0,  # ToolOffsetLength del tool que venía (top/router): piso del g53
) -> list[str]:
    if not drills:
        return []

    state = _SideDrillState(spindle=top_spindle)
    lines: list[str] = []
    is_first_in_program = (prev_family is None)
    total_side_holes = len(drills)

    for drill in drills:
        face = drill.plane_name
        fd = SIDE_FACE[face]
        depth = side_effective_depth(drill, ctx)  # pasante → dimensión cruzada del panel
        approach, perp, z_height, cut = _hole_coords(drill, ctx, depth)
        feed = effective_side_feed(drill.feedrate)  # spindle lateral fijo; peck se ignora (N011)

        face_changed = (face != state.current_face)

        if face_changed:
            first_face_ever = is_first_in_program and (state.current_face is None)

            if first_face_ever:
                # Side is first family: preamble already set up the G40.
                # Operation body starts directly with ETK[6] setup + cut with MLV=2.
                lines += _first_face_setup_side_only(face, ctx, fd)
                # G4F0.500 for side-only programs with 2+ holes
                if total_side_holes >= 2:
                    lines.append("G4F0.500")
                lines += _cut_first_hole_side_only(face, approach, perp, z_height, cut, feed, ctx)
            elif state.current_face is None:
                # First side face, but another family preceded it
                lines += _face_after_other_family(face, ctx, fd, prev_family, drill.security_plane, prev_tlc)
                # Top→Side and Router→Side transitions do NOT get G4F0.500
                lines += _cut_first_hole_in_body(face, approach, perp, z_height, cut, feed, ctx)
            else:
                # Face-to-face transition within side drill
                lines += _face_change(face, ctx, fd, state, drill.security_plane)
                # Face changes DO NOT get G4F0.500 (empirically: B005 Right, B008)
                lines += _cut_first_hole_in_body(face, approach, perp, z_height, cut, feed, ctx)

            state.current_face = face
            state.etk0 = fd.etk0
            state.spindle = SIDE_SPINDLE
        else:
            # Same face — repositioning with passthrough move
            lines += _same_face_cut_block(
                face, approach, perp, z_height, cut, feed,
                state.prev_approach, state.prev_perp,
                ctx,
            )

        state.prev_approach = approach
        state.prev_perp = perp
        state.prev_security_plane = drill.security_plane

    return lines


# ---------------------------------------------------------------------------
# Hole coordinate formulas per face
# ---------------------------------------------------------------------------

def _hole_coords(
    drill: DrillSpec, ctx: PieceCtx, depth: float,
) -> tuple[float, float, float, float]:
    """(approach, perp, z_height, cut) — all in MLV2 frame.

    El plano retraído (approach) usa el `security_plane` de la OPERACIÓN con piso 5 (N014 sp≥5:
    -70/-75/-95; N016 sp=2 → -70 = -(TLC_CUT+5)). El corte avanza con la profundidad:
    cut = borde ∓ TLC_CUT ± depth (independiente de sp). (El 20 fijo anterior era sobreajuste:
    N001/N011 todos con sp=20 por defecto.)
    """
    face = drill.plane_name
    cx, cy = drill.center_x, drill.center_y
    sp = max(drill.security_plane, SIDE_APPROACH_FLOOR)

    if face == "Left":
        return -(TLC_LATERAL_CUT + sp), -cx, cy, -TLC_LATERAL_CUT + depth
    if face == "Right":
        edge = ctx.length + TLC_LATERAL_CUT
        return edge + sp, cx, cy, edge - depth
    if face == "Front":
        return -(TLC_LATERAL_CUT + sp), cx, cy, -TLC_LATERAL_CUT + depth
    # Back
    edge = ctx.width + TLC_LATERAL_CUT
    return edge + sp, -cx, cy, edge - depth


# ---------------------------------------------------------------------------
# MLV=1 SHF values per face
# ---------------------------------------------------------------------------

def _shf_mlv1(face: str, ctx: PieceCtx) -> tuple[float, float]:
    return side_shf(ctx, face)


# ---------------------------------------------------------------------------
# Face setup sequences
# ---------------------------------------------------------------------------

def _first_face_setup_side_only(face: str, ctx: PieceCtx, fd) -> list[str]:
    """Operation body for first face when side drill is the first family.

    The preamble already emitted the face-specific G40 and MLV=2/G17 footer.
    The operation body starts directly with ?%ETK[6]=N.
    """
    shf_x, shf_y = _shf_mlv1(face, ctx)
    return [
        f"?%ETK[6]={fd.etk6}",
        f"%Or[0].ofX={or_ofx(ctx, block=True):.3f}",
        f"%Or[0].ofY={or_ofy(ctx, block=True):.3f}",
        f"%Or[0].ofZ={ctx.DZ * 1000:.3f}",
        "MLV=1",
        f"SHF[X]={shf_x:.3f}",
        f"SHF[Y]={shf_y:.3f}",
        f"SHF[Z]={ctx.origin_z:.3f}",
        "MLV=2",
        "MLV=2",
        f"SHF[X]={fd.shf_x_mlv2:.3f}",
        f"SHF[Y]={fd.shf_y_mlv2:.3f}",
        f"SHF[Z]={fd.shf_z_mlv2:.3f}",
        "?%ETK[17]=257",
        f"S{SIDE_SPINDLE}M3",
        f"?%ETK[0]={fd.etk0}",
    ]


def _face_after_other_family(
    face: str, ctx: PieceCtx, fd, prev_family: str | None, dest_sp: float, head_tlc: float,
) -> list[str]:
    """First side face when top drill or router preceded. `head_tlc` = ToolOffsetLength del
    tool que se retrae (top vertical o router): es el piso del g53."""
    shf_x, shf_y = _shf_mlv1(face, ctx)

    if prev_family == "router":
        # G40 block FIRST, then router shutdown, then side drill entry
        return [
            "MLV=1",
            f"SHF[X]={shf_x:.3f}",
            f"SHF[Y]={shf_y:.3f}",
            f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
            f"?%ETK[8]={fd.etk8}",
            "G40",
            "MLV=0",
            f"G0 G53 Z{Z_PARK:.3f}",
            "MLV=2",
            "G61",
            "MLV=0",
            "?%ETK[13]=0",
            "?%ETK[18]=0",
            f"G0 G53 Z{Z_PARK:.3f}",
            "G64",
            "MLV=1",
            f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
            "MLV=2",
            "G17",
            f"?%ETK[6]={fd.etk6}",
            "MLV=2",
            f"SHF[X]={fd.shf_x_mlv2:.3f}",
            f"SHF[Y]={fd.shf_y_mlv2:.3f}",
            f"SHF[Z]={fd.shf_z_mlv2:.3f}",
            "?%ETK[17]=257",
            f"S{SIDE_SPINDLE}M3",
            f"?%ETK[0]={fd.etk0}",
        ]

    # Top→Side (no %Or needed, already set from top drill setup).
    # Solo el destino aporta mandril lateral (el cabezal venía del top drill).
    # El SHF[X/Y/Z] previo al G40 solo lo necesitan Left/Back; Front/Right ya tienen el SHF
    # correcto del top drill (mismo patrón que la restauración del epílogo). (N016: top→Front
    # NO lo lleva; N001 c001 top→Left SÍ.)
    g53_z = side_transition_g53_z(ctx.DZ, [(face, dest_sp)], head_tlc)
    pre_g40 = [
        "MLV=1",
        f"SHF[X]={shf_x:.3f}",
        f"SHF[Y]={shf_y:.3f}",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
    ] if face in ("Left", "Back") else []
    return pre_g40 + [
        f"?%ETK[8]={fd.etk8}",
        "G40",
        "MLV=1",
        f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={fd.etk6}",
        "MLV=0",
        f"G0 G53 Z{g53_z:.3f}",
        "MLV=2",
        "MLV=2",
        f"SHF[X]={fd.shf_x_mlv2:.3f}",
        f"SHF[Y]={fd.shf_y_mlv2:.3f}",
        f"SHF[Z]={fd.shf_z_mlv2:.3f}",
        f"?%ETK[0]={fd.etk0}",
    ]


def _face_change(
    face: str, ctx: PieceCtx, fd, state: _SideDrillState, dest_sp: float,
) -> list[str]:
    """Transition between two side-drill faces."""
    shf_x, shf_y = _shf_mlv1(face, ctx)
    # El G53 despeja AMBOS mandriles: cara que sale (state) y cara que entra.
    prev_face = state.current_face or face
    # Side→Side: el tool en el cabezal es la broca lateral → su ToolOffsetLength (TLC_LATERAL_CUT).
    g53_z = side_transition_g53_z(
        ctx.DZ,
        [(prev_face, state.prev_security_plane), (face, dest_sp)],
        TLC_LATERAL_CUT,
    )
    lines = [
        "MLV=1",
        f"SHF[X]={shf_x:.3f}",
        f"SHF[Y]={shf_y:.3f}",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        f"?%ETK[8]={fd.etk8}",
        "G40",
        "MLV=1",
        f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
        "MLV=2",
        "G17",
        f"?%ETK[6]={fd.etk6}",
        "MLV=0",
        f"G0 G53 Z{g53_z:.3f}",
        "MLV=2",
        "MLV=2",
        f"SHF[X]={fd.shf_x_mlv2:.3f}",
        f"SHF[Y]={fd.shf_y_mlv2:.3f}",
        f"SHF[Z]={fd.shf_z_mlv2:.3f}",
    ]
    if fd.etk0 != state.etk0:
        lines.append(f"?%ETK[0]={fd.etk0}")
    return lines


# ---------------------------------------------------------------------------
# Cut blocks
# ---------------------------------------------------------------------------

def _cut_first_hole_side_only(
    face: str, approach: float, perp: float, z_height: float, cut: float, feed: float,
    ctx: PieceCtx,
) -> list[str]:
    """First hole of a face in a side-only program.  Includes MLV=2 before G1 G9."""
    if face in ("Left", "Right"):
        return [
            f"G0 X{approach:.3f} Y{perp:.3f}",
            f"G0 Z{z_height:.3f}",
            "?%ETK[7]=3",
            "MLV=2",
            f"G1 G9 X{cut:.3f} F{feed:.3f}",
            f"G0 X{approach:.3f} Z{z_height:.3f}",
            "MLV=1",
            f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
            "?%ETK[7]=0",
        ]
    # Front or Back
    return [
        f"G0 X{perp:.3f} Y{approach:.3f}",
        f"G0 Z{z_height:.3f}",
        "?%ETK[7]=3",
        "MLV=2",
        f"G1 G9 Y{cut:.3f} F{feed:.3f}",
        f"G0 Y{approach:.3f} Z{z_height:.3f}",
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]


def _cut_first_hole_in_body(
    face: str, approach: float, perp: float, z_height: float, cut: float, feed: float,
    ctx: PieceCtx,
) -> list[str]:
    """First hole after an in-body G40 setup (Top→Side, Router→Side, or face change).
    No MLV=2 before G1 G9.
    """
    if face in ("Left", "Right"):
        return [
            f"G0 X{approach:.3f} Y{perp:.3f}",
            f"G0 Z{z_height:.3f}",
            "?%ETK[7]=3",
            f"G1 G9 X{cut:.3f} F{feed:.3f}",
            f"G0 X{approach:.3f} Z{z_height:.3f}",
            "MLV=1",
            f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
            "?%ETK[7]=0",
        ]
    # Front or Back
    return [
        f"G0 X{perp:.3f} Y{approach:.3f}",
        f"G0 Z{z_height:.3f}",
        "?%ETK[7]=3",
        f"G1 G9 Y{cut:.3f} F{feed:.3f}",
        f"G0 Y{approach:.3f} Z{z_height:.3f}",
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]


def _same_face_cut_block(
    face: str,
    approach: float, perp: float, z_height: float, cut: float, feed: float,
    prev_approach: float, prev_perp: float,
    ctx: PieceCtx,
) -> list[str]:
    """Subsequent hole on the same face (repositioning with passthrough)."""
    lines = [
        "MLV=1",
        f"SHF[Z]={ctx.origin_z:.3f}+%ETK[114]/1000",
        "MLV=2",
        "G17",
    ]
    if face in ("Left", "Right"):
        lines += [
            f"G0 X{approach:.3f} Y{prev_perp:.3f} Z{z_height:.3f}",
            f"G0 X{approach:.3f} Y{perp:.3f} Z{z_height:.3f}",
            "?%ETK[7]=3",
            f"G1 G9 X{cut:.3f} F{feed:.3f}",
            f"G0 X{approach:.3f} Z{z_height:.3f}",
        ]
    else:  # Front or Back
        lines += [
            f"G0 X{prev_perp:.3f} Y{approach:.3f} Z{z_height:.3f}",
            f"G0 X{perp:.3f} Y{approach:.3f} Z{z_height:.3f}",
            "?%ETK[7]=3",
            f"G1 G9 Y{cut:.3f} F{feed:.3f}",
            f"G0 Y{approach:.3f} Z{z_height:.3f}",
        ]
    lines += [
        "MLV=1",
        f"SHF[Z]={ctx.DZ:.3f}+%ETK[114]/1000",
        "?%ETK[7]=0",
    ]
    return lines
