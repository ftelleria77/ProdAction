"""N002 — Fixtures para validar el G53 Z de transición lateral y desacoplar la
base 83.000 de la geometría de pieza.

Contexto (derivado de N001):
  El G53 Z absoluto al cambiar a una cara lateral parece seguir
      g53_z = 83.000 + max(shf_z_origen, shf_z_destino)
  donde shf_z viene de spindles.cfg (Front/Back=66.50, Right=66.45, Left=66.30).
  Desde Top/Router el origen no aporta shf_z lateral, así que solo cuenta el dest.

  Pero N001 dejó fijos origin_z=25, depth=18, altura lateral=9, por lo que NO se
  puede saber si 83.000 es constante de máquina o esconde una dependencia
  geométrica (p.ej. 58+origin_z, 65+depth, 74+altura...).

Grupos:
  H — Discriminan la hipótesis del máximo (parejas donde origen > destino).
  I — Desacoplan la base 83.000 (varían origin_z, depth, origin_x/y).
  J — Varían la altura/posición del agujero lateral (no debería mover el G53).

FACE_PRIORITY (orden de ejecución que impone Maestro): Front=0, Left=1, Right=2, Back=3.
Por eso, para forzar una transición A→B hay que elegir A con prioridad menor que B.

Uso:
    py -m iso.machining_lab.n002_baselines.generate
    py -m iso.machining_lab.n002_baselines.generate --output-dir <ruta>

Salida por defecto:
    PGMX: S:\\Maestro\\Projects\\ProdAction\\N002_baselines\\
    ISO:  P:\\USBMIX\\ProdAction\\N002_baselines\\  (postprocesado por Maestro)
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
    build_drilling_spec,
    build_synthesis_request,
    synthesize_request,
)
from pgmx.synthesis.drilling.single import DrillingSpec

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N002_baselines"

# Geometría base (igual a N001 salvo donde se varía a propósito).
BASE_L = 300.0
BASE_W = 200.0
BASE_D = 18.0
BASE_OX = 5.0
BASE_OY = 5.0
BASE_OZ = 25.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _side(plane: str, along: float, height: float = 9.0,
          diameter: float = 8.0, depth: float = 28.0) -> DrillingSpec:
    """Taladro lateral.

    `along`  = posición a lo largo del canto (Front/Back→eje X; Left/Right→eje Y).
    `height` = altura del agujero dentro del espesor (mapea a Z de máquina).
    """
    return build_drilling_spec(
        feature_name=f"{plane.upper()}_A{along:g}_H{height:g}",
        plane_name=plane,
        center_x=along,
        center_y=height,
        diameter=diameter,
        target_depth=depth,
        tool_resolution="Auto",
    )


def _write(output_dir: Path, name: str, drillings: list[DrillingSpec], *,
           length: float = BASE_L, width: float = BASE_W, depth: float = BASE_D,
           origin_x: float = BASE_OX, origin_y: float = BASE_OY,
           origin_z: float = BASE_OZ) -> None:
    path = output_dir / f"{name}.pgmx"
    req = build_synthesis_request(
        output_path=path,
        piece_name=name,
        length=length,
        width=width,
        depth=depth,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        drillings=drillings,
    )
    synthesize_request(req)
    print(f"  {path.name}")


# ---------------------------------------------------------------------------
# Grupo H — Discriminan la hipótesis del máximo
# ---------------------------------------------------------------------------

def _group_h(output_dir: Path) -> None:
    """Parejas/tripletes donde el origen tiene shf_z mayor que el destino.

    Si g53 = 83 + max(orig, dest):
      Front→Right  → 83 + max(66.50, 66.45) = 149.500  (dest-only daría 149.450)
      Front→Left   → 149.500 (ya visto en N001 b008; control)
      Left→Right   → 83 + max(66.30, 66.45) = 149.450  (control N001 b005)
    """
    print("\n=== Grupo H: discriminar max(orig, dest) ===")

    # H001 — Front → Right : DISCRIMINA max(=149.500) vs dest-only(=149.450)
    _write(output_dir, "N_H001_front_then_right",
           [_side("Front", along=100.0), _side("Right", along=100.0)])

    # H002 — Front → Left → Right : dos transiciones en una pieza
    #   Front→Left = 83+max(66.50,66.30)=149.500 ; Left→Right = 83+max(66.30,66.45)=149.450
    _write(output_dir, "N_H002_front_left_right",
           [_side("Front", along=100.0), _side("Left", along=100.0),
            _side("Right", along=100.0)])

    # H003 — Right → Back : 83+max(66.45,66.50)=149.500 (dest domina; control inverso)
    _write(output_dir, "N_H003_right_then_back",
           [_side("Right", along=100.0), _side("Back", along=100.0)])

    # H004 — Front → Back → (Left vía prioridad no aplica) : Front→Back control
    #   Front(0)→Left(1)→Back(3): Front→Left=149.500, Left→Back=83+max(66.30,66.50)=149.500
    _write(output_dir, "N_H004_front_left_back",
           [_side("Front", along=100.0), _side("Left", along=100.0),
            _side("Back", along=100.0)])


# ---------------------------------------------------------------------------
# Grupo I — Desacoplan la base 83.000
# ---------------------------------------------------------------------------

def _group_i(output_dir: Path) -> None:
    """Misma transición Front→Left (esperado 149.500) variando SOLO la geometría.

    Si el G53 Z permanece 149.500 → 83.000 es constante de máquina.
    Si cambia → la base esconde una dependencia (origin_z, depth, origin_x/y).
    """
    print("\n=== Grupo I: desacoplar base 83.000 ===")

    # I001 — origin_z = 40 (vs 25)
    _write(output_dir, "N_I001_front_left_originz40",
           [_side("Front", along=100.0), _side("Left", along=100.0)],
           origin_z=40.0)

    # I002 — espesor depth = 30 (vs 18); altura del agujero a media pieza (15)
    _write(output_dir, "N_I002_front_left_depth30",
           [_side("Front", along=100.0, height=15.0),
            _side("Left", along=100.0, height=15.0)],
           depth=30.0)

    # I003 — origin_x/origin_y desplazados (50, 80)
    _write(output_dir, "N_I003_front_left_originxy",
           [_side("Front", along=100.0), _side("Left", along=100.0)],
           origin_x=50.0, origin_y=80.0)

    # I004 — combinación: origin_z=10, depth=25
    _write(output_dir, "N_I004_front_left_oz10_d25",
           [_side("Front", along=100.0, height=12.0),
            _side("Left", along=100.0, height=12.0)],
           origin_z=10.0, depth=25.0)

    # I005 — pieza grande: length=400, width=250 (afecta approach de Right/Back)
    _write(output_dir, "N_I005_front_left_L400W250",
           [_side("Front", along=120.0), _side("Left", along=120.0)],
           length=400.0, width=250.0)


# ---------------------------------------------------------------------------
# Grupo J — Altura/posición del agujero lateral
# ---------------------------------------------------------------------------

def _group_j(output_dir: Path) -> None:
    """Varían la altura (height) y la posición (along) del agujero lateral.

    El G53 Z de transición NO debería depender de la posición del agujero
    (la perforación real la fija después `G0 Z{height}`).
    """
    print("\n=== Grupo J: posición/altura del agujero ===")

    # J001 — altura del agujero = 14 (vs 9), espesor 18
    _write(output_dir, "N_J001_front_left_h14",
           [_side("Front", along=100.0, height=14.0),
            _side("Left", along=100.0, height=14.0)])

    # J002 — distinta posición a lo largo del canto
    _write(output_dir, "N_J002_front_left_along60",
           [_side("Front", along=60.0), _side("Left", along=150.0)])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera la serie N002 de fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir}")

    _group_h(output_dir)
    _group_i(output_dir)
    _group_j(output_dir)

    print("\nListo. Convierte todos los .pgmx con Maestro y deja los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
