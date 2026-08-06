r"""N053 - Polilínea con arcos en los extremos + modos de lead C.N. restantes.

Lote re-priorizado por el ensayo general (2026-08-05): «polilínea + acercamiento Arco no
En cota/Automatic» y sus vecinas son la guarda MÁS golpeada por los corpus reales (~84
archivos: perfiles de cocina con esquinas redondeadas compensadas). Levanta las guardas
de `_validation.py` :447 (1er/último segmento en ARCO + corrección/lead) y
:462-:477 (velocidad propia, Arco En bajada/subida, retract Arco sin corrección, lead
Línea en modos no validados, lead Línea sin corrección).

Forma base: polilínea ABIERTA de 3 segmentos — recta, recta, con variantes que ponen un
ARCO como primer o último segmento (cuarto de círculo r=40). Perfil dentro de la pieza
convención 300x300x18. La incógnita es SOLO el ISO (regla 5a: los knobs ya son
autorables); Fermín postprocesa TAL CUAL.

Uso: py -m iso.machining_lab.n053_polilinea_extremos_arco.generate
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_polyline_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N053_polilinea_extremos_arco"

PIECE = dict(piece_name="n053", length=300.0, width=300.0, depth=18.0,
             origin_x=0.0, origin_y=0.0, origin_z=0.0)

# Geometrías (abiertas, dentro de la pieza, profundidad ciega -6):
#  RECTAS:      (60,60) -> (240,60) -> (240,200) -> (60,200)
#  ARCO_INICIO: arco 1º: (60,100)->(100,60) centro (100,100) CW, luego rectas
#  ARCO_FIN:    rectas y arco último: (240,160)->(200,200)? -> centro (200,160) CCW
SEGS_RECTAS = [((240.0, 60.0),), ((240.0, 200.0),), ((60.0, 200.0),)]
START_RECTAS = (60.0, 60.0)

START_ARCO_INI = (60.0, 100.0)
SEGS_ARCO_INI = [((100.0, 60.0), (100.0, 100.0), "CounterClockwise"),
                 ((240.0, 60.0),), ((240.0, 200.0),)]

START_ARCO_FIN = (60.0, 60.0)
SEGS_ARCO_FIN = [((200.0, 60.0),), ((200.0, 120.0),),
                 ((240.0, 160.0), (240.0, 120.0), "Clockwise")]


def _spec(start, segments, **kw):
    return build_polyline_spec(
        start=start, segments=segments,
        tool_id="1902", tool_name="E003", tool_width=9.52,
        security_plane=30.0, is_through=False, target_depth=6.0, **kw)


def _fixtures():
    lead_arc = dict(approach_enabled=True, approach_type="Arc", approach_mode="Quote",
                    approach_radius_multiplier=2.0, approach_arc_side="Automatic")
    ret_arc = dict(retract_enabled=True, retract_type="Arc", retract_mode="Quote",
                   retract_radius_multiplier=2.0, retract_arc_side="Automatic")
    yield "N_PA_arco_inicio_corr", _spec(START_ARCO_INI, SEGS_ARCO_INI, side_of_feature="Right")
    yield "N_PA_arco_fin_corr", _spec(START_ARCO_FIN, SEGS_ARCO_FIN, side_of_feature="Right")
    yield "N_PA_arco_inicio_lead", _spec(START_ARCO_INI, SEGS_ARCO_INI,
                                         side_of_feature="Right", **lead_arc)
    yield "N_PA_arco_fin_ret", _spec(START_ARCO_FIN, SEGS_ARCO_FIN,
                                     side_of_feature="Right", **ret_arc)
    yield "N_PA_lead_velocidad", _spec(START_RECTAS, SEGS_RECTAS, side_of_feature="Right",
                                       approach_enabled=True, approach_type="Arc",
                                       approach_mode="Quote", approach_radius_multiplier=2.0,
                                       approach_arc_side="Automatic", approach_speed=2.0)
    yield "N_PA_lead_arco_down", _spec(START_RECTAS, SEGS_RECTAS, side_of_feature="Right",
                                       approach_enabled=True, approach_type="Arc",
                                       approach_mode="Down", approach_radius_multiplier=2.0,
                                       approach_arc_side="Automatic")
    yield "N_PA_ret_arco_up", _spec(START_RECTAS, SEGS_RECTAS, side_of_feature="Right",
                                    retract_enabled=True, retract_type="Arc",
                                    retract_mode="Up", retract_radius_multiplier=2.0,
                                    retract_arc_side="Automatic")
    yield "N_PA_ret_arco_sin_corr", _spec(START_RECTAS, SEGS_RECTAS, **ret_arc)
    # (El acercamiento Línea En cota compensado YA está validado por N044 — el modo sin
    # fixture del lado Línea es el ALEJAMIENTO En cota, espejo del validado En subida.)
    yield "N_PA_ret_linea_quote", _spec(START_RECTAS, SEGS_RECTAS, side_of_feature="Right",
                                        retract_enabled=True, retract_type="Line",
                                        retract_mode="Quote",
                                        retract_radius_multiplier=2.0)
    yield "N_PA_lead_linea_sin_corr", _spec(START_RECTAS, SEGS_RECTAS,
                                            approach_enabled=True, approach_type="Line",
                                            approach_mode="Quote",
                                            approach_radius_multiplier=2.0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in _fixtures():
        path = args.output_dir / f"{name}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, polylines=[spec], **PIECE))
        print(f"OK {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
