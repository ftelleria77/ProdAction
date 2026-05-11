"""Generate PGMX fixtures for T-BH-004 side-drill to top-drill study.

The batch extends the historical ``Pieza_*.pgmx`` sequence with the complete
directed matrix from the four horizontal side drills to the seven vertical top
drills. Manual Maestro/CNC ISO output is still required before these variants
are used as closed evidence.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

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

SIDE_FACES = ("Front", "Right", "Back", "Left")
SIDE_TOOLS = {
    "Front": "058",
    "Right": "060",
    "Back": "059",
    "Left": "061",
}
SIDE_LABELS = {
    "Front": "anterior/delantera/frontal",
    "Right": "lateral derecha",
    "Back": "posterior/trasera",
    "Left": "lateral izquierda",
}


@dataclass(frozen=True)
class TopTool:
    name: str
    diameter: float
    drill_family: str
    speed: int


TOP_TOOLS = (
    TopTool("001", 8.0, "Flat", 6000),
    TopTool("002", 15.0, "Flat", 4000),
    TopTool("003", 20.0, "Flat", 4000),
    TopTool("004", 35.0, "Flat", 4000),
    TopTool("005", 5.0, "Flat", 6000),
    TopTool("006", 4.0, "Flat", 6000),
    TopTool("007", 5.0, "Conical", 6000),
)


@dataclass(frozen=True)
class Fixture:
    index: int
    name: str
    side_face: str
    top_tool: TopTool
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def speed_case(self) -> str:
        if self.top_tool.speed == 6000:
            return "same_speed_6000"
        return "speed_change_6000_to_4000"

    @property
    def transition(self) -> str:
        return f"{self.side_face}->{self.top_tool.name}"


def _side_span(fixture: Fixture) -> float:
    if fixture.side_face in {"Front", "Back"}:
        return fixture.length
    return fixture.width


def _side_drill(fixture: Fixture) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TBH004_{fixture.index:02d}_{fixture.side_face.upper()}_D8",
        plane_name=fixture.side_face,
        center_x=round(_side_span(fixture) * 0.5, 3),
        center_y=fixture.depth / 2.0,
        diameter=8.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _top_drill(fixture: Fixture) -> DrillingSpec:
    tool_offset = fixture.index % len(TOP_TOOLS)
    return build_drilling_spec(
        feature_name=f"TBH004_{fixture.index:02d}_TOP_{fixture.top_tool.name}_D{fixture.top_tool.diameter:g}",
        plane_name="Top",
        center_x=120.0 + (tool_offset * 25.0),
        center_y=140.0,
        diameter=fixture.top_tool.diameter,
        target_depth=10.0,
        drill_family=fixture.top_tool.drill_family,
        tool_resolution="Auto",
    )


def build_fixtures() -> tuple[Fixture, ...]:
    fixtures: list[Fixture] = []
    index = 1
    for side_face in SIDE_FACES:
        for top_tool in TOP_TOOLS:
            fixtures.append(
                Fixture(
                    index=index,
                    name=f"Pieza_{122 + index:03d}",
                    side_face=side_face,
                    top_tool=top_tool,
                )
            )
            index += 1
    return tuple(fixtures)


def generate(output_dir: Path, *, force: bool = False) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
        if output_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing fixture: {output_path}")

        machinings = (
            _side_drill(fixture),
            _top_drill(fixture),
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
            ordered_machinings=machinings,
        )
        result = synthesize_request(request)
        expected_iso_path = EXPECTED_ISO_DIR / f"{fixture.name.lower()}.iso"
        rows.append(
            {
                "id": f"P-TBH004-{fixture.index:03d}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition": fixture.transition,
                "side_face": fixture.side_face,
                "side_face_label": SIDE_LABELS[fixture.side_face],
                "side_tool": SIDE_TOOLS[fixture.side_face],
                "top_tool": fixture.top_tool.name,
                "top_diameter": f"{fixture.top_tool.diameter:g}",
                "top_drill_family": fixture.top_tool.drill_family,
                "expected_speed_case": fixture.speed_case,
                "sha256": result.sha256,
                "purpose": (
                    "T-BH-004: isolate side drill "
                    f"{SIDE_TOOLS[fixture.side_face]}/{fixture.side_face} -> "
                    f"top drill {fixture.top_tool.name}/D{fixture.top_tool.diameter:g}."
                ),
            }
        )

    manifest_path = output_dir / "Pieza_123_150_TBH004_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition",
        "side_face",
        "side_face_label",
        "side_tool",
        "top_tool",
        "top_diameter",
        "top_drill_family",
        "expected_speed_case",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T-BH-004 side-to-top PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_123..150 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-BH-004 fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['side_face']}->{row['top_tool']} "
            f"{row['expected_speed_case']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
