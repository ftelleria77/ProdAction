r"""N059 - Sierra Vertical X mezclada con otras familias (transiciones del canal).

Levanta `_reader.py:392` (sierra combinada: hoy solo programas solo-sierra, N037). El
emisor viejo tiene TODA la evidencia de estas transiciones (T-BH-005..009: top↔canal,
lateral↔canal, canal→canal — 18 casos DeMarco) pero validada con comparación NORMALIZADA:
este lote las re-deriva byte a byte con el emisor ACTUAL. Incluye sondas de secuencia
(canal primero vs después) por el hallazgo estructural del ensayo (el ISO sigue la
secuencia FUENTE, no reagrupa).

Convención: pieza 300x300x18 origen 0/0/0; canal horizontal prof. 8; E003 para líneas.
Postprocesar TAL CUAL.

Uso: py -m iso.machining_lab.n059_sierra_transiciones.generate
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
    build_channel_spec, build_drill_spec, build_line_spec, build_synthesis_request,
    synthesize_request,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N059_sierra_transiciones"

PIECE = dict(piece_name="n059", length=300.0, width=300.0, depth=18.0,
             origin_x=0.0, origin_y=0.0, origin_z=0.0)


def _canal(y=150.0):
    return build_channel_spec(start_x=60.0, start_y=y, end_x=240.0, end_y=y,
                              target_depth=8.0)


def _linea(y=60.0):
    return build_line_spec(20.0, y, 280.0, y, None, "1902", "E003", 9.52, 30.0,
                           target_depth=5.0, is_through=False)


def _taladro_top(x=150.0, y=260.0):
    return build_drill_spec(center_x=x, center_y=y, diameter=8.0, plane_name="Top",
                            target_depth=10.0, tool_resolution="Auto")


def _taladro_left(x=100.0):
    return build_drill_spec(center_x=x, center_y=9.0, diameter=8.0, plane_name="Left",
                            target_depth=25.0, tool_resolution="Auto")


def _fixtures():
    yield "N_SW_canal_top", [_canal(), _taladro_top()]
    yield "N_SW_top_canal", [_taladro_top(), _canal()]          # sonda de secuencia
    yield "N_SW_canal_linea", [_canal(), _linea()]
    yield "N_SW_linea_canal", [_linea(), _canal()]              # sonda de secuencia
    yield "N_SW_canal_lateral", [_canal(), _taladro_left()]
    yield "N_SW_canal_top_canal", [_canal(100.0), _taladro_top(), _canal(220.0)]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, machinings in _fixtures():
        path = args.output_dir / f"{name}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, ordered_machinings=machinings, **PIECE))
        print(f"OK {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
