"""N003 — Mapear el piso de eff(security_plane) en el G53 Z de transición lateral.

Contexto: G53 Z = DZ + 20 + max( eff(sp_A)+shf_z_A, eff(sp_B)+shf_z_B ), donde
se sospecha eff(sp) = max(sp, 5) (piso de 5 mm, deducido de un solo punto sp=0).

Esta tanda barre security_plane bajos en una transición Front→Right (DZ=43, ambos
taladros con el MISMO sp → gana Front, shf_z=66.5):

    G53 esperado (si eff=max(sp,5)) = 43 + 20 + eff(sp) + 66.5
      sp=1 →134.5  sp=3 →134.5  sp=5 →134.5  sp=6 →135.5  sp=7 →136.5  sp=10 →139.5

Si el codo no está en 5, los valores bajos lo revelarán.

Uso:  py -m iso.machining_lab.n003_eff_floor.generate
Salida: S:\\Maestro\\Projects\\ProdAction\\N003_eff_floor\\  (postprocesar en Maestro)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso.paths import PGMX_ROOT  # noqa: E402
from pgmx.synthesis import build_drilling_spec, build_synthesis_request, synthesize_request  # noqa: E402

DEFAULT_OUTPUT_DIR = PGMX_ROOT / "N003_eff_floor"

SP_VALUES = [1, 3, 5, 6, 7, 10]


def _side(plane: str, along: float, sp: float) -> object:
    return build_drilling_spec(
        feature_name=f"{plane.upper()}_SP{sp:g}",
        plane_name=plane,
        center_x=along,
        center_y=9.0,
        diameter=8.0,
        target_depth=28.0,
        security_plane=float(sp),
        tool_resolution="Auto",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Barrido de security_plane para el piso de eff.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    out: Path = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output: {out}")

    for sp in SP_VALUES:
        name = f"N_K{sp:02d}_front_right_sp{sp:g}"
        path = out / f"{name}.pgmx"
        req = build_synthesis_request(
            output_path=path,
            piece_name=name,
            length=300.0, width=200.0, depth=18.0,
            origin_x=5.0, origin_y=5.0, origin_z=25.0,
            drillings=[_side("Front", 100.0, sp), _side("Right", 100.0, sp)],
        )
        synthesize_request(req)
        print(f"  {path.name}  (sp={sp}, G53 esperado si eff=max(sp,5): {43+20+max(sp,5)+66.5:.3f})")

    print("\nListo. Postprocesá los .pgmx en Maestro y dejá los .iso en el mismo directorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
