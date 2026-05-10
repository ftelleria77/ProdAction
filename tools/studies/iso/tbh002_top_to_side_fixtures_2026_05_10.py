"""Generate PGMX fixtures for T-BH-002 top-drill to side-drill study.

The generated files extend the historical ``Pieza_*.pgmx`` sequence and are
intended to be postprocessed manually in Maestro/CNC when the CNC environment is
available.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.synthesize_pgmx import (  # noqa: E402
    build_drilling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    top_diameter: float
    side_plane: str
    side_center_x: float
    side_center_y: float
    expected_speed_case: str
    length: float = 400.0
    width: float = 250.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"


def _top_drill(diameter: float):
    return build_drilling_spec(
        feature_name=f"TBH002_TOP_D{diameter:g}",
        plane_name="Top",
        center_x=80.0,
        center_y=60.0,
        diameter=diameter,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _side_drill(plane_name: str, center_x: float, center_y: float):
    return build_drilling_spec(
        feature_name=f"TBH002_{plane_name.upper()}_D8",
        plane_name=plane_name,
        center_x=center_x,
        center_y=center_y,
        diameter=8.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_098",
            purpose="T-BH-002: top drill 001/D8 to front side drill 058/D8; same 6000 rpm.",
            top_diameter=8.0,
            side_plane="Front",
            side_center_x=200.0,
            side_center_y=9.0,
            expected_speed_case="same_speed_6000",
        ),
        Fixture(
            name="Pieza_099",
            purpose="T-BH-002: top drill 001/D8 to right side drill 060/D8; same 6000 rpm.",
            top_diameter=8.0,
            side_plane="Right",
            side_center_x=125.0,
            side_center_y=9.0,
            expected_speed_case="same_speed_6000",
        ),
        Fixture(
            name="Pieza_100",
            purpose="T-BH-002: top drill 001/D8 to back side drill 059/D8; same 6000 rpm.",
            top_diameter=8.0,
            side_plane="Back",
            side_center_x=200.0,
            side_center_y=9.0,
            expected_speed_case="same_speed_6000",
        ),
        Fixture(
            name="Pieza_101",
            purpose="T-BH-002: top drill 001/D8 to left side drill 061/D8; same 6000 rpm.",
            top_diameter=8.0,
            side_plane="Left",
            side_center_x=125.0,
            side_center_y=9.0,
            expected_speed_case="same_speed_6000",
        ),
        Fixture(
            name="Pieza_102",
            purpose="T-BH-002 speed-control: top drill 002/D15 at 4000 rpm to front side drill 058/D8 at 6000 rpm.",
            top_diameter=15.0,
            side_plane="Front",
            side_center_x=200.0,
            side_center_y=9.0,
            expected_speed_case="speed_change_4000_to_6000",
        ),
    )


def generate(output_dir: Path, *, force: bool = False) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
        if output_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing fixture: {output_path}")

        request = build_synthesis_request(
            output_path=output_path,
            piece_name=fixture.name,
            length=fixture.length,
            width=fixture.width,
            depth=fixture.depth,
            origin_x=fixture.origin_x,
            origin_y=fixture.origin_y,
            origin_z=fixture.origin_z,
            execution_fields=fixture.execution_fields,
            drillings=(
                _top_drill(fixture.top_diameter),
                _side_drill(fixture.side_plane, fixture.side_center_x, fixture.side_center_y),
            ),
        )
        result = synthesize_request(request)
        rows.append(
            {
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "side_plane": fixture.side_plane,
                "top_diameter": f"{fixture.top_diameter:g}",
                "expected_speed_case": fixture.expected_speed_case,
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "Pieza_098_102_TBH002_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=[
                "name",
                "pgmx_path",
                "side_plane",
                "top_diameter",
                "expected_speed_case",
                "sha256",
                "purpose",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T-BH-002 top-to-side PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_098..102 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-BH-002 fixtures in {args.output_dir}")
    for row in rows:
        print(f"{row['name']} {row['side_plane']} {row['expected_speed_case']} {row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
