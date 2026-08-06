r"""N056 - Familias de router MEZCLADAS + SONDAS DE SECUENCIA de familias.

Dos preguntas en un lote (re-priorizado por el ensayo general 2026-08-05, ~27 archivos
reales golpeando la mezcla; las producciones mezclan SIEMPRE):

1. MEZCLAS del router (`_reader.py:377`): línea/círculo/arco/polilínea/vaciado conviven
   en un programa real — hoy solo polilínea+línea con cambio de herramienta tiene fixture.
   Derivan las transiciones entre familias del electromandril.

2. SONDAS DE SECUENCIA (hallazgo estructural del ensayo, 6º punto ciego): la anatomía de
   `fajx 964` (DeMarco) muestra que el ISO SIGUE LA SECUENCIA FUENTE (side→top→side
   intercalado) — NO reagrupa Router→Top→Side como asume nuestro converter. Pero esa
   evidencia es del emisor de nov-2025: estas sondas le hacen la MISMA pregunta al
   emisor ACTUAL con fuentes que el corpus propio nunca pudo fabricar (el sintetizador
   agrupaba las familias — por eso el punto ciego). Cada sonda pone las familias en un
   orden que el reagrupado DESTRUIRÍA: el ISO resultante responde solo.

Convención: pieza 300x300x18 origen 0/0/0, security 30, ciegos -5/-6, E003 salvo nota.
Postprocesar TAL CUAL (regla 5a: la incógnita es solo el ISO).

Uso: py -m iso.machining_lab.n056_familias_mezcladas.generate
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
    build_arc_spec, build_circle_spec, build_contour_parallel_milling_strategy_spec,
    build_drill_spec, build_line_spec, build_pocket_spec, build_polyline_spec,
    build_synthesis_request, synthesize_request,
)

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N056_familias_mezcladas"

PIECE = dict(piece_name="n056", length=300.0, width=300.0, depth=18.0,
             origin_x=0.0, origin_y=0.0, origin_z=0.0)


def _linea(y=100.0, retract=False, x0=20.0, x1=280.0):
    kw = {}
    if retract:
        kw = dict(retract_enabled=True, retract_type="Arc", retract_mode="Quote",
                  retract_radius_multiplier=2.0, retract_arc_side="Automatic")
    return build_line_spec(x0, y, x1, y, None, "1902", "E003", 9.52, 30.0,
                           target_depth=5.0, is_through=False, **kw)


def _circulo():
    return build_circle_spec(center_x=150.0, center_y=200.0, radius=40.0,
                             tool_id="1902", tool_name="E003", tool_width=9.52,
                             security_plane=30.0, target_depth=5.0, is_through=False)


def _arco():
    return build_arc_spec(start_x=60.0, start_y=240.0, end_x=140.0, end_y=240.0,
                          center_x=100.0, center_y=240.0, winding="CounterClockwise",
                          tool_id="1902", tool_name="E003", tool_width=9.52,
                          security_plane=30.0, target_depth=5.0, is_through=False)


def _polilinea():
    return build_polyline_spec(points=[(40.0, 40.0), (260.0, 40.0), (260.0, 90.0)],
                               tool_id="1902", tool_name="E003", tool_width=9.52,
                               security_plane=30.0, target_depth=5.0, is_through=False)


def _vaciado():
    rect = [(80.0, 120.0), (220.0, 120.0), (220.0, 220.0), (80.0, 220.0), (80.0, 120.0)]
    return build_pocket_spec(contour_points=rect, tool_id="1900", tool_name="E001",
                             tool_width=18.36, security_plane=30.0, target_depth=6.0,
                             is_through=False,
                             milling_strategy=build_contour_parallel_milling_strategy_spec())


def _taladro_top(x=150.0, y=260.0):
    return build_drill_spec(center_x=x, center_y=y, diameter=8.0, plane_name="Top",
                            target_depth=10.0, tool_resolution="Auto")


def _taladro_left(x=100.0):
    return build_drill_spec(center_x=x, center_y=9.0, diameter=8.0, plane_name="Left",
                            target_depth=25.0, tool_resolution="Auto")


def _fixtures():
    # --- mezclas del router (guarda _reader.py:377) ---
    yield "N_MX_linea_circulo", [_linea(), _circulo()]
    yield "N_MX_circulo_polilinea", [_circulo(), _polilinea()]
    yield "N_MX_arco_linea", [_arco(), _linea()]
    yield "N_MX_vaciado_linea", [_vaciado(), _linea(y=260.0)]
    yield "N_MX_linea_arco_circulo", [_linea(), _arco(), _circulo()]
    # --- alejamiento en op NO-última SIN cambio de herramienta (converter.py:63) ---
    yield "N_MX_ret_no_ultima", [_linea(y=100.0, retract=True), _linea(y=250.0)]
    # --- SONDAS de secuencia de familias (¿el emisor ACTUAL reagrupa o sigue fuente?) ---
    yield "N_SEQ_taladro_linea", [_taladro_top(), _linea()]
    yield "N_SEQ_linea_taladro_linea", [_linea(y=100.0), _taladro_top(), _linea(y=250.0)]
    yield "N_SEQ_lateral_top_lateral", [_taladro_left(100.0), _taladro_top(),
                                        _taladro_left(200.0)]
    yield "N_SEQ_top_lateral_top", [_taladro_top(100.0, 260.0), _taladro_left(150.0),
                                    _taladro_top(200.0, 260.0)]
    yield "N_SEQ_lateral_linea", [_taladro_left(150.0), _linea()]


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
