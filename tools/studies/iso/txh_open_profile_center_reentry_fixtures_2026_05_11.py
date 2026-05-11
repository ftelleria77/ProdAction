"""Generate open-profile re-entry PGMX fixtures with center cutter correction.

This batch mirrors the ``Pieza_192..198`` study shape, but changes the second
open E001 profile from side compensation to ``Center`` while keeping the same
polyline trace and router/top/router transition path.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.studies.iso.txh_open_profile_reentry_fixtures_2026_05_11 import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    EXPECTED_ISO_DIR,
    Fixture,
    _ordered_machinings,
)
from tools.synthesize_pgmx import build_synthesis_request, synthesize_request  # noqa: E402


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_199",
            purpose="Control: line E001 -> four top drill 005/D5 -> open profile E001 Center Arc/Down-Up.",
            first_router_family="line_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
            reentry_side="Center",
        ),
        Fixture(
            name="Pieza_200",
            purpose="Cocina-like: profile E001 -> top drill 005/D5 -> open profile E001 Center Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(5.0,),
            reentry_side="Center",
        ),
        Fixture(
            name="Pieza_201",
            purpose="Cocina-like: profile E001 -> four top drill 005/D5 -> open profile E001 Center Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
            reentry_side="Center",
        ),
        Fixture(
            name="Pieza_202",
            purpose="Top-tool control: profile E001 -> top drill 001/D8 -> open profile E001 Center Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(8.0,),
            reentry_side="Center",
        ),
        Fixture(
            name="Pieza_203",
            purpose="Speed control: profile E001 -> top drill 002/D15 -> open profile E001 Center Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(15.0,),
            reentry_side="Center",
        ),
        Fixture(
            name="Pieza_204",
            purpose="Approach control: profile E001 -> four top drill 005/D5 -> open profile E001 Center without approach/retract.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
            reentry_side="Center",
            reentry_approach_enabled=False,
        ),
        Fixture(
            name="Pieza_205",
            purpose="Approach control: line E001 -> four top drill 005/D5 -> open profile E001 Center without approach/retract.",
            first_router_family="line_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
            reentry_side="Center",
            reentry_approach_enabled=False,
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
            ordered_machinings=_ordered_machinings(fixture),
        )
        result = synthesize_request(request)
        expected_iso_path = EXPECTED_ISO_DIR / f"{fixture.name.lower()}.iso"
        rows.append(
            {
                "id": f"P-TXH-OPEN-CENTER-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition_path": fixture.transition_path,
                "first_router_family": fixture.first_router_family,
                "first_router_tool": "E001",
                "top_diameters": ";".join(f"{diameter:g}" for diameter in fixture.top_diameters),
                "top_chain_case": fixture.top_chain_case,
                "second_router_family": "open_profile",
                "second_router_tool": "E001",
                "second_router_side": fixture.reentry_side,
                "second_router_depth_case": "through_extra_1",
                "second_router_approach": fixture.reentry_approach_case,
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "Pieza_199_205_TXH_open_profile_center_reentry_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition_path",
        "first_router_family",
        "first_router_tool",
        "top_diameters",
        "top_chain_case",
        "second_router_family",
        "second_router_tool",
        "second_router_side",
        "second_router_depth_case",
        "second_router_approach",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate center-correction open-profile re-entry PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_199..205 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} center-correction open-profile fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['first_router_family']}->{row['top_chain_case']}->"
            f"{row['second_router_side']}/{row['second_router_approach']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
