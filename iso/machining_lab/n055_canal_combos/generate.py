r"""N055 - Canal (Sierra Vertical X): leads, rebaba, lado y posición de material.

Re-priorizado por el ensayo general (2026-08-05): «canal con lado Right/Left» golpea ~47
archivos reales. Levanta `_validation.py` :301 (leads), :303 (rebaba), :305 (lado) y
:307 (posición de material Right). El «radio final»/«ángulo» del canal (:309) queda
FUERA de este lote: espera la captura C4 (¿son editables en la ventana?).

Canal convención: horizontal, dirección -x fixtured por N037 (acá se autora en +x y el
sintetizador normaliza), profundidad default 10, pieza 300x300x18.

Uso: py -m iso.machining_lab.n055_canal_combos.generate
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_channel_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N055_canal_combos"

PIECE = dict(piece_name="n055", length=300.0, width=300.0, depth=18.0,
             origin_x=0.0, origin_y=0.0, origin_z=0.0)
LINEA = dict(start_x=60.0, start_y=150.0, end_x=240.0, end_y=150.0, target_depth=8.0)


def _fixtures():
    yield "N_CH_approach", build_channel_spec(
        **LINEA, approach_enabled=True, approach_type="Arc", approach_mode="Quote",
        approach_radius_multiplier=2.0, approach_arc_side="Automatic")
    yield "N_CH_retract", build_channel_spec(
        **LINEA, retract_enabled=True, retract_type="Arc", retract_mode="Quote",
        retract_radius_multiplier=2.0, retract_arc_side="Automatic")
    yield "N_CH_rebaba_pos", build_channel_spec(**LINEA, side_offset=2.0)
    yield "N_CH_rebaba_neg", build_channel_spec(**LINEA, side_offset=-2.0)
    yield "N_CH_lado_left", build_channel_spec(**LINEA, side_of_feature="Left")
    yield "N_CH_lado_right", build_channel_spec(**LINEA, side_of_feature="Right")
    yield "N_CH_material_right", build_channel_spec(**LINEA, material_position="Right")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in _fixtures():
        path = args.output_dir / f"{name}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, channels=[spec], **PIECE))
        print(f"OK {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
