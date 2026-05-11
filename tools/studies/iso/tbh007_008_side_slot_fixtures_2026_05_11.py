"""Generate PGMX fixtures for T-BH-007 and T-BH-008 side-slot study.

The batch extends the historical ``Pieza_*.pgmx`` sequence with directed
fixtures for the two remaining internal boring-head transitions involving the
vertical saw: side drill -> top slot and top slot -> side drill.
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
    SlotMillingSpec,
    build_drilling_spec,
    build_slot_milling_spec,
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
class Fixture:
    index: int
    name: str
    transition_id: str
    side_face: str
    order: str
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def transition(self) -> str:
        return f"{self.order}:{self.side_face}"

    @property
    def expected_speed_case(self) -> str:
        if self.transition_id == "T-BH-007":
            return "speed_change_6000_to_4000"
        return "speed_change_4000_to_6000"


def _side_span(fixture: Fixture) -> float:
    if fixture.side_face in {"Front", "Back"}:
        return fixture.length
    return fixture.width


def _side_drill(fixture: Fixture) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"{fixture.transition_id}_{fixture.index:02d}_{fixture.side_face.upper()}_D8",
        plane_name=fixture.side_face,
        center_x=round(_side_span(fixture) * 0.5, 3),
        center_y=fixture.depth / 2.0,
        diameter=8.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _top_slot(fixture: Fixture) -> SlotMillingSpec:
    offset = (fixture.index % 4) * 12.0
    return build_slot_milling_spec(
        feature_name=f"{fixture.transition_id}_{fixture.index:02d}_TOP_SLOT_082",
        start_x=120.0 + offset,
        start_y=140.0,
        end_x=300.0 + offset,
        end_y=140.0,
        plane_name="Top",
        side_of_feature="Center",
        tool_name="082",
        tool_width=3.8,
        security_plane=20.0,
        is_through=False,
        target_depth=10.0,
    )


def build_fixtures() -> tuple[Fixture, ...]:
    fixtures: list[Fixture] = []
    index = 1
    for side_face in SIDE_FACES:
        fixtures.append(
            Fixture(
                index=index,
                name=f"Pieza_{150 + index:03d}",
                transition_id="T-BH-007",
                side_face=side_face,
                order="side->slot",
            )
        )
        index += 1
    for side_face in SIDE_FACES:
        fixtures.append(
            Fixture(
                index=index,
                name=f"Pieza_{150 + index:03d}",
                transition_id="T-BH-008",
                side_face=side_face,
                order="slot->side",
            )
        )
        index += 1
    return tuple(fixtures)


def _ordered_machinings(fixture: Fixture) -> tuple[object, object]:
    side = _side_drill(fixture)
    slot = _top_slot(fixture)
    if fixture.transition_id == "T-BH-007":
        return side, slot
    return slot, side


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
            ordered_machinings=_ordered_machinings(fixture),
        )
        result = synthesize_request(request)
        expected_iso_path = EXPECTED_ISO_DIR / f"{fixture.name.lower()}.iso"
        rows.append(
            {
                "id": f"P-{fixture.transition_id.replace('-', '')}-{fixture.index:03d}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition_id": fixture.transition_id,
                "transition": fixture.transition,
                "side_face": fixture.side_face,
                "side_face_label": SIDE_LABELS[fixture.side_face],
                "side_tool": SIDE_TOOLS[fixture.side_face],
                "slot_tool": "082",
                "expected_speed_case": fixture.expected_speed_case,
                "sha256": result.sha256,
                "purpose": (
                    f"{fixture.transition_id}: isolate {fixture.order} "
                    f"with side drill {SIDE_TOOLS[fixture.side_face]}/{fixture.side_face} "
                    "and top slot saw 082."
                ),
            }
        )

    manifest_path = output_dir / "Pieza_151_158_TBH007_008_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition_id",
        "transition",
        "side_face",
        "side_face_label",
        "side_tool",
        "slot_tool",
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
    parser = argparse.ArgumentParser(description="Generate T-BH-007/008 side-slot PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_151..158 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-BH-007/008 fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['transition_id']} {row['transition']} "
            f"{row['expected_speed_case']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
