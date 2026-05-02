"""Archived minimal PGMX fixture batch for ISO reverse engineering.

These fixtures are intentionally small and comparable: each file changes one
variable at a time so Maestro-postprocessed ISO can reveal which value controls
`%Or`, `SHF`, `MLV`, `ETK`, park moves, and compensation behavior.

This module is retained for reproducibility of the 2026-05-03 minimal ISO
study. It is not part of the day-to-day synthesis workflow.

Recommended factory run:

    python -m tools.studies.iso.minimal_fixtures_2026_05_03 --output-dir "S:\\Maestro\\Projects\\ProdAction\\ISO\\minimal_fixtures_2026-05-03"
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
    build_line_milling_spec,
    build_synthesis_request,
    build_unidirectional_milling_strategy_spec,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = ROOT / "tmp" / "iso_minimal_fixtures"


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    length: float = 100.0
    width: float = 100.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"
    drillings: Sequence[object] = ()
    line_millings: Sequence[object] = ()


def _top_drill(x: float, y: float) -> object:
    return build_drilling_spec(
        feature_name="TOP_D5_DEPTH10",
        plane_name="Top",
        center_x=x,
        center_y=y,
        diameter=5.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _side_drill(plane_name: str) -> object:
    return build_drilling_spec(
        feature_name=f"{plane_name.upper()}_D8_DEPTH28",
        plane_name=plane_name,
        center_x=50.0,
        center_y=9.0,
        diameter=8.0,
        target_depth=28.0,
        tool_resolution="Auto",
    )


def _line_e004(y: float, *, ph5: bool = False) -> object:
    strategy = None
    if ph5:
        strategy = build_unidirectional_milling_strategy_spec(
            connection_mode="InPiece",
            axial_cutting_depth=5.0,
            axial_finish_cutting_depth=0.0,
        )

    return build_line_milling_spec(
        line_x1=20.0,
        line_y1=y,
        line_x2=80.0,
        line_y2=y,
        line_feature_name="LINE_E004_CENTER",
        line_tool_id="1903",
        line_tool_name="E004",
        line_tool_width=4.0,
        line_security_plane=20.0,
        line_side_of_feature="Center",
        line_is_through=True,
        line_extra_depth=1.0,
        line_milling_strategy=strategy,
    )


def build_fixtures() -> list[Fixture]:
    return [
        Fixture(
            name="ISO_MIN_001_TopDrill_Base",
            purpose="Base: 100x100x18, origin 5/5/25, HG, one top D5 drill at 50/50.",
            drillings=(_top_drill(50.0, 50.0),),
        ),
        Fixture(
            name="ISO_MIN_002_TopDrill_Y60",
            purpose="Only the top drilling Y moves from 50 to 60.",
            drillings=(_top_drill(50.0, 60.0),),
        ),
        Fixture(
            name="ISO_MIN_003_TopDrill_X60",
            purpose="Only the top drilling X moves from 50 to 60.",
            drillings=(_top_drill(60.0, 50.0),),
        ),
        Fixture(
            name="ISO_MIN_004_TopDrill_DY200",
            purpose="Only panel width changes from 100 to 200; drill stays centered.",
            width=200.0,
            drillings=(_top_drill(50.0, 100.0),),
        ),
        Fixture(
            name="ISO_MIN_005_TopDrill_DX200",
            purpose="Only panel length changes from 100 to 200; drill stays centered.",
            length=200.0,
            drillings=(_top_drill(100.0, 50.0),),
        ),
        Fixture(
            name="ISO_MIN_006_TopDrill_OriginY10",
            purpose="Only workpiece origin Y changes from 5 to 10.",
            origin_y=10.0,
            drillings=(_top_drill(50.0, 50.0),),
        ),
        Fixture(
            name="ISO_MIN_010_LeftDrill_Base",
            purpose="One lateral D8 drill on Left.",
            drillings=(_side_drill("Left"),),
        ),
        Fixture(
            name="ISO_MIN_011_RightDrill_Base",
            purpose="One lateral D8 drill on Right.",
            drillings=(_side_drill("Right"),),
        ),
        Fixture(
            name="ISO_MIN_012_FrontDrill_Base",
            purpose="One lateral D8 drill on Front.",
            drillings=(_side_drill("Front"),),
        ),
        Fixture(
            name="ISO_MIN_013_BackDrill_Base",
            purpose="One lateral D8 drill on Back.",
            drillings=(_side_drill("Back"),),
        ),
        Fixture(
            name="ISO_MIN_020_LineE004_Base",
            purpose="One through E004 center line at Y50.",
            line_millings=(_line_e004(50.0),),
        ),
        Fixture(
            name="ISO_MIN_021_LineE004_Y60",
            purpose="Only E004 line Y moves from 50 to 60.",
            line_millings=(_line_e004(60.0),),
        ),
        Fixture(
            name="ISO_MIN_022_LineE004_PH5",
            purpose="Same as base E004 line, but with unidirectional PH=5 strategy.",
            line_millings=(_line_e004(50.0, ph5=True),),
        ),
        Fixture(
            name="ISO_MIN_023_LineE004_OriginY10",
            purpose="Same as base E004 line, but workpiece origin Y changes from 5 to 10.",
            origin_y=10.0,
            line_millings=(_line_e004(50.0),),
        ),
    ]


def generate(output_dir: Path) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
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
            drillings=fixture.drillings,
            line_millings=fixture.line_millings,
        )
        result = synthesize_request(request)
        rows.append(
            {
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=["name", "pgmx_path", "sha256", "purpose"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate minimal PGMX fixtures for the ISO synthesis investigation."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where .pgmx fixtures and manifest.csv will be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir)
    print(f"Generated {len(rows)} PGMX fixtures in {args.output_dir}")
    for row in rows:
        print(f"{row['name']}  {row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
