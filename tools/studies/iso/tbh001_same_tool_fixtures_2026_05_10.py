"""Generate PGMX fixtures for T-BH-001 top-drill continuity study.

The batch extends the historical ``Pieza_*.pgmx`` sequence with controlled
``top drill -> top drill`` cases where the vertical drill does not change.
Manual Maestro/CNC ISO output is still required before these variants are used
as closed evidence.
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
    DrillingSpec,
    build_drilling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")
EXPECTED_ISO_DIR = Path(r"P:\USBMIX\ProdAction\ISO")


@dataclass(frozen=True)
class Hole:
    x: float
    y: float


@dataclass(frozen=True)
class Fixture:
    index: int
    name: str
    purpose: str
    diameter: float
    expected_tool: str
    expected_speed: int
    focus: str
    holes: Sequence[Hole]
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"


def _top_drill(fixture: Fixture, hole: Hole, ordinal: int) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TBH001_SAME_{fixture.index:02d}_{ordinal}_D{fixture.diameter:g}",
        plane_name="Top",
        center_x=hole.x,
        center_y=hole.y,
        diameter=fixture.diameter,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            index=1,
            name="Pieza_119",
            purpose="T-BH-001 same-tool: two D8 top drills on one row; tool 001 remains active.",
            diameter=8.0,
            expected_tool="001",
            expected_speed=6000,
            focus="same_tool_d8_row_reposition",
            holes=(Hole(80.0, 80.0), Hole(220.0, 80.0)),
        ),
        Fixture(
            index=2,
            name="Pieza_120",
            purpose="T-BH-001 same-tool: two D8 top drills on one column; tool 001 remains active.",
            diameter=8.0,
            expected_tool="001",
            expected_speed=6000,
            focus="same_tool_d8_column_reposition",
            holes=(Hole(120.0, 70.0), Hole(120.0, 190.0)),
        ),
        Fixture(
            index=3,
            name="Pieza_121",
            purpose="T-BH-001 same-tool: three D8 top drills; repeated same-tool continuation.",
            diameter=8.0,
            expected_tool="001",
            expected_speed=6000,
            focus="same_tool_d8_repeated_continuation",
            holes=(Hole(70.0, 70.0), Hole(180.0, 150.0), Hole(310.0, 210.0)),
        ),
        Fixture(
            index=4,
            name="Pieza_122",
            purpose="T-BH-001 same-tool: two D15 top drills; tool 002 remains active at 4000 rpm.",
            diameter=15.0,
            expected_tool="002",
            expected_speed=4000,
            focus="same_tool_d15_speed_4000",
            holes=(Hole(90.0, 90.0), Hole(260.0, 180.0)),
        ),
    )


def generate(output_dir: Path, *, force: bool = False) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
        if output_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing fixture: {output_path}")

        drillings = tuple(
            _top_drill(fixture, hole, ordinal)
            for ordinal, hole in enumerate(fixture.holes, start=1)
        )
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
            ordered_machinings=drillings,
        )
        result = synthesize_request(request)
        expected_iso_path = EXPECTED_ISO_DIR / f"{fixture.name.lower()}.iso"
        rows.append(
            {
                "id": f"P-TBH001-SAME-{fixture.index:03d}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition": "top_drill->top_drill",
                "variant": "same_tool",
                "expected_tool": fixture.expected_tool,
                "expected_speed": str(fixture.expected_speed),
                "diameter": f"{fixture.diameter:g}",
                "hole_count": str(len(fixture.holes)),
                "focus": fixture.focus,
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "Pieza_119_122_TBH001_same_tool_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition",
        "variant",
        "expected_tool",
        "expected_speed",
        "diameter",
        "hole_count",
        "focus",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T-BH-001 same-tool top-drill fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_119..122 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-BH-001 same-tool fixtures in {args.output_dir}")
    for row in rows:
        print(f"{row['name']} {row['focus']} tool={row['expected_tool']} {row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
