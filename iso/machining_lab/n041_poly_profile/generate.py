r"""N041 - Eje B etapa 3: POLILINEAS de segmentos mixtos (rectos + arcos) — exploracion.

Primer lote de PolylineSpec (autoria estrenada 2026-07-08: composite de miembros
mixtos recta/arco, forma de las piezas de produccion FrenteCurvo/Estante). Doble proposito
(patron N031/N040): si Maestro postprocesa nuestra autoria TAL CUAL, la extension queda
validada; y los ISO ensenan el render del encadenamiento recta<->arco (transiciones internas,
sentido de cada arco, cierre del contorno).
Todo Center; correccion/leads/estrategia en lotes posteriores.
POSTPROCESAR TAL CUAL. Si Maestro rechaza o pide regenerar alguno, foto: es dato.
Uso: py -m iso.machining_lab.n041_poly_profile.generate
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_polyline_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N041_poly_profile"

def _poly(start, segments, **kw):
    return build_polyline_spec(
        start=start, segments=segments,
        tool_id=kw.pop("tool_id", "1903"), tool_name=kw.pop("tool_name", "E004"),
        tool_width=kw.pop("tool_width", 4.0),
        target_depth=kw.pop("target_depth", 5.0), **kw)

CASES = [
    # recta + recta (2 segmentos, control: sin arcos — debe igualar a PolylineSpec)
    ("ll",      _poly((20.0, 60.0), [((20.0, 140.0),), ((160.0, 140.0),)])),
    # recta -> arco -> recta (una "L" con esquina redondeada), arco CCW
    ("lar",     _poly((20.0, 60.0), [((20.0, 120.0),),
                                     ((80.0, 180.0), (80.0, 120.0), "CounterClockwise"),
                                     ((240.0, 180.0),)])),
    # idem con arco CW (concavidad opuesta)
    ("lar_cw",  _poly((20.0, 60.0), [((20.0, 120.0),),
                                     ((80.0, 180.0), (20.0, 180.0), "Clockwise"),
                                     ((240.0, 180.0),)])),
    # arco -> arco (dos cuartos: "S" suave)
    ("aa",      _poly((60.0, 100.0), [((120.0, 160.0), (120.0, 100.0), "CounterClockwise"),
                                      ((180.0, 220.0), (120.0, 220.0), "Clockwise")])),
    # arco primero (arranca en arco), luego recta
    ("ar_l",    _poly((210.0, 100.0), [((150.0, 160.0), (150.0, 100.0), "CounterClockwise"),
                                       ((60.0, 160.0),)])),
    # CONTORNO CERRADO: rectangulo con 2 esquinas redondeadas (espejo de FrenteCurvo/Estante)
    ("closed",  _poly((60.0, 40.0),
                      [((240.0, 40.0),),                                    # base
                       ((240.0, 140.0),),                                   # lado der
                       ((200.0, 180.0), (200.0, 140.0), "CounterClockwise"),# esquina der
                       ((100.0, 180.0),),                                   # techo
                       ((60.0, 140.0), (100.0, 140.0), "CounterClockwise"), # esquina izq
                       ((60.0, 40.0),)])),                                  # lado izq (cierra)
    # profundidad y pasante sobre el perfil lar
    ("prof10",  _poly((20.0, 60.0), [((20.0, 120.0),),
                                     ((80.0, 180.0), (80.0, 120.0), "CounterClockwise"),
                                     ((240.0, 180.0),)], target_depth=10.0)),
    ("th",      _poly((20.0, 60.0), [((20.0, 120.0),),
                                     ((80.0, 180.0), (80.0, 120.0), "CounterClockwise"),
                                     ((240.0, 180.0),)], target_depth=None, is_through=True, extra_depth=2.0)),
    # fresa ancha
    ("e001",    _poly((20.0, 60.0), [((20.0, 120.0),),
                                     ((80.0, 180.0), (80.0, 120.0), "CounterClockwise"),
                                     ((240.0, 180.0),)], tool_id="1900", tool_name="E001", tool_width=18.36)),
    # dos polilineas en un programa (transiciones)
    ("two",     None),
]

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    out = parser.parse_args(argv).output_dir; out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")
    for tag, spec in CASES:
        if tag == "two":
            polys = [_poly((20.0, 40.0), [((20.0, 90.0),), ((120.0, 90.0),)]),
                     _poly((160.0, 120.0), [((200.0, 160.0), (200.0, 120.0), "CounterClockwise"),
                                            ((260.0, 160.0),)])]
        else:
            polys = [spec]
        path = out / f"N_R_{tag}.pgmx"
        synthesize_request(build_synthesis_request(
            output_path=path, piece_name=f"N_R_{tag}", length=300.0, width=250.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0, polyline_millings=polys))
        print(f"  {path.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
