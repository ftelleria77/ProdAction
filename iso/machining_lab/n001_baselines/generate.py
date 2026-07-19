"""N001 — Fixtures de línea base para el convertidor PGMX→ISO.

Cada fixture aísla UNA variable. Corriendo todos en Maestro y analizando el
ISO resultante es posible derivar las reglas de conversión de forma empírica.

Grupos:
  A — Top drill: herramienta única / múltiple / múltiples agujeros
  B — Side drill: cada cara + combinaciones
  C — Transiciones entre familias
  D — Router básico (line milling)

Uso:
    python -m iso.machining_lab.n001_baselines.generate
    python -m iso.machining_lab.n001_baselines.generate --output-dir <ruta>

Salida por defecto:
    PGMX: S:\\Maestro\\Projects\\ProdAction\\N001_baselines\\
    ISO:  P:\\USBMIX\\ProdAction\\N001_baselines\\  (postprocesado por Maestro)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import (  # noqa: E402
    build_drill_spec,
    build_line_spec,
    build_synthesis_request,
    synthesize_request,
)
from pgmx.synthesis.drilling.single import DrillSpec
from pgmx.synthesis.milling.line import LineSpec

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N001_baselines"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PIECE_L = 300.0
PIECE_W = 200.0
PIECE_D = 18.0
ORIGIN_X = 5.0
ORIGIN_Y = 5.0
ORIGIN_Z = 25.0


def _drill_top(x: float, y: float, diameter: float = 5.0, depth: float = 10.0) -> object:
    return build_drill_spec(
        feature_name=f"TOP_D{diameter:g}_X{x:g}_Y{y:g}",
        plane_name="Top",
        center_x=x,
        center_y=y,
        diameter=diameter,
        target_depth=depth,
        tool_resolution="Auto",
    )


def _drill_side(plane: str, x: float, y: float = 9.0, diameter: float = 8.0, depth: float = 28.0) -> object:
    return build_drill_spec(
        feature_name=f"{plane.upper()}_D{diameter:g}_X{x:g}",
        plane_name=plane,
        center_x=x,
        center_y=y,
        diameter=diameter,
        target_depth=depth,
        tool_resolution="Auto",
    )


def _line_mill(y: float = 100.0) -> object:
    return build_line_spec(
        start_x=20.0,
        start_y=y,
        end_x=PIECE_L - 20.0,
        end_y=y,
        feature_name=f"LINE_Y{y:g}",
        tool_id="1903",
        tool_name="E004",
        tool_width=4.0,
        security_plane=20.0,
        side_of_feature="Center",
        is_through=False,
        target_depth=5.0,
    )


def _write(output_dir: Path, name: str, *operations: object) -> None:
    drills = [op for op in operations if isinstance(op, DrillSpec)]
    lines = [op for op in operations if isinstance(op, LineSpec)]
    path = output_dir / f"{name}.pgmx"
    req = build_synthesis_request(
        output_path=path,
        piece_name=name,
        length=PIECE_L,
        width=PIECE_W,
        depth=PIECE_D,
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        origin_z=ORIGIN_Z,
        drills=drills or None,
        lines=lines or None,
    )
    synthesize_request(req)
    print(f"  {path.name}")


# ---------------------------------------------------------------------------
# Grupo A — Top drill
# ---------------------------------------------------------------------------

def _group_a(output_dir: Path) -> None:
    """Taladros superiores: herramienta única, múltiple, múltiples agujeros."""
    print("\n=== Grupo A: Top drill ===")

    # A001 — baseline: 1 agujero, 1 herramienta, posición centrada
    _write(output_dir, "N_A001_top_1hole_D5",
           _drill_top(150.0, 100.0, diameter=5.0, depth=10.0))

    # A002 — distinto diámetro (= distinta herramienta)
    _write(output_dir, "N_A002_top_1hole_D8",
           _drill_top(150.0, 100.0, diameter=8.0, depth=10.0))

    # A003 — distinto diámetro, D15
    _write(output_dir, "N_A003_top_1hole_D15",
           _drill_top(150.0, 100.0, diameter=15.0, depth=10.0))

    # A004 — 2 agujeros, MISMA herramienta (D5)
    # → revela si Maestro emite 2 veces el setup de herramienta o solo 1
    _write(output_dir, "N_A004_top_2holes_D5_D5",
           _drill_top(80.0, 100.0, diameter=5.0, depth=10.0),
           _drill_top(220.0, 100.0, diameter=5.0, depth=10.0))

    # A005 — 2 agujeros, DISTINTA herramienta (D5 + D8)
    # → revela la secuencia de cambio de herramienta entre taladros
    _write(output_dir, "N_A005_top_2holes_D5_D8",
           _drill_top(80.0, 100.0, diameter=5.0, depth=10.0),
           _drill_top(220.0, 100.0, diameter=8.0, depth=10.0))

    # A006 — 3 agujeros, 3 herramientas distintas
    _write(output_dir, "N_A006_top_3holes_D5_D8_D15",
           _drill_top(80.0, 100.0, diameter=5.0, depth=10.0),
           _drill_top(150.0, 100.0, diameter=8.0, depth=10.0),
           _drill_top(220.0, 100.0, diameter=15.0, depth=10.0))

    # A007 — 2 agujeros, misma herramienta, profundidades distintas
    # → revela si la profundidad cambia algo en el setup
    _write(output_dir, "N_A007_top_2holes_D5_depth8_depth14",
           _drill_top(80.0, 100.0, diameter=5.0, depth=8.0),
           _drill_top(220.0, 100.0, diameter=5.0, depth=14.0))


# ---------------------------------------------------------------------------
# Grupo B — Side drill
# ---------------------------------------------------------------------------

def _group_b(output_dir: Path) -> None:
    """Taladros laterales: cada cara + combinaciones."""
    print("\n=== Grupo B: Side drill ===")

    # B001 — cara Left, 1 agujero
    _write(output_dir, "N_B001_left_1hole",
           _drill_side("Left", x=150.0, y=9.0, diameter=8.0, depth=28.0))

    # B002 — cara Right, 1 agujero
    _write(output_dir, "N_B002_right_1hole",
           _drill_side("Right", x=150.0, y=9.0, diameter=8.0, depth=28.0))

    # B003 — cara Front, 1 agujero
    _write(output_dir, "N_B003_front_1hole",
           _drill_side("Front", x=100.0, y=9.0, diameter=8.0, depth=28.0))

    # B004 — cara Back, 1 agujero
    _write(output_dir, "N_B004_back_1hole",
           _drill_side("Back", x=100.0, y=9.0, diameter=8.0, depth=28.0))

    # B005 — Left + Right (misma herramienta, caras opuestas en eje X)
    # → revela cómo Maestro cambia entre caras del mismo eje
    _write(output_dir, "N_B005_left_then_right",
           _drill_side("Left", x=150.0, y=9.0),
           _drill_side("Right", x=150.0, y=9.0))

    # B006 — Front + Back (misma herramienta, caras opuestas en eje Y)
    _write(output_dir, "N_B006_front_then_back",
           _drill_side("Front", x=100.0, y=9.0),
           _drill_side("Back", x=100.0, y=9.0))

    # B007 — Left + Left, 2 agujeros misma cara
    # → revela si hay diferencia entre 1 y 2 agujeros en la misma cara
    _write(output_dir, "N_B007_left_2holes",
           _drill_side("Left", x=60.0, y=9.0),
           _drill_side("Left", x=140.0, y=9.0))

    # B008 — Left + Front (caras distintas, ejes distintos)
    _write(output_dir, "N_B008_left_then_front",
           _drill_side("Left", x=150.0, y=9.0),
           _drill_side("Front", x=100.0, y=9.0))


# ---------------------------------------------------------------------------
# Grupo C — Transiciones entre familias
# ---------------------------------------------------------------------------

def _group_c(output_dir: Path) -> None:
    """Transiciones: top→side, side→top, top→router, router→top."""
    print("\n=== Grupo C: Transiciones ===")

    # C001 — Top + Left
    # → revela la secuencia de transición top_drill → side_drill
    _write(output_dir, "N_C001_top_then_left",
           _drill_top(150.0, 100.0, diameter=5.0, depth=10.0),
           _drill_side("Left", x=150.0, y=9.0))

    # C002 — Left + Top
    # → revela la secuencia de transición side_drill → top_drill
    _write(output_dir, "N_C002_left_then_top",
           _drill_side("Left", x=150.0, y=9.0),
           _drill_top(150.0, 100.0, diameter=5.0, depth=10.0))

    # C003 — Top + Left + Top (round trip)
    # → revela si el segundo top_drill difiere del primero
    _write(output_dir, "N_C003_top_left_top",
           _drill_top(150.0, 100.0, diameter=5.0, depth=10.0),
           _drill_side("Left", x=150.0, y=9.0),
           _drill_top(220.0, 100.0, diameter=5.0, depth=10.0))

    # C004 — Top + Router
    # → revela la transición top_drill → line_milling
    _write(output_dir, "N_C004_top_then_router",
           _drill_top(150.0, 100.0, diameter=5.0, depth=10.0),
           _line_mill(y=100.0))

    # C005 — Router + Top
    # → revela la transición line_milling → top_drill
    _write(output_dir, "N_C005_router_then_top",
           _line_mill(y=100.0),
           _drill_top(150.0, 100.0, diameter=5.0, depth=10.0))

    # C006 — Left + Router
    # → revela la transición side_drill → line_milling
    _write(output_dir, "N_C006_left_then_router",
           _drill_side("Left", x=150.0, y=9.0),
           _line_mill(y=100.0))

    # C007 — Router + Left
    # → revela la transición line_milling → side_drill
    _write(output_dir, "N_C007_router_then_left",
           _line_mill(y=100.0),
           _drill_side("Left", x=150.0, y=9.0))


# ---------------------------------------------------------------------------
# Grupo D — Router (line milling) aislado
# ---------------------------------------------------------------------------

def _group_d(output_dir: Path) -> None:
    """Router: baseline y variaciones de parámetros."""
    print("\n=== Grupo D: Router (line milling) ===")

    # D001 — baseline: 1 pasada lineal
    _write(output_dir, "N_D001_router_1pass",
           _line_mill(y=100.0))

    # D002 — 2 pasadas lineales paralelas
    # → revela si hay reset/setup entre pasadas del router
    _write(output_dir, "N_D002_router_2pass",
           _line_mill(y=80.0),
           _line_mill(y=120.0))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera fixtures para el nuevo motor ISO.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir}")

    _group_a(output_dir)
    _group_b(output_dir)
    _group_c(output_dir)
    _group_d(output_dir)

    print(f"\nListo. Convierte todos los .pgmx con Maestro y deja los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
