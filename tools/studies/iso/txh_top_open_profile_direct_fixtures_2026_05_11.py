"""Generate direct top-drill -> open-profile router PGMX fixtures.

This mini batch isolates ``T-XH-002`` without a previous router job.  It keeps
the same open E001 polyline trace used by ``Pieza_192..205`` and varies only
the cutter compensation / approach state of the incoming router job.
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

from tools.studies.iso.txh_open_profile_reentry_fixtures_2026_05_11 import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    EXPECTED_ISO_DIR,
    Fixture as ReentryFixture,
    _open_profile_reentry,
    _top_drills,
)
from tools.synthesize_pgmx import build_synthesis_request, synthesize_request  # noqa: E402


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    reentry_side: str
    reentry_approach_enabled: bool = True
    top_diameters: tuple[float, ...] = (5.0,)
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def reentry_approach_case(self) -> str:
        return "Arc_Down_Up" if self.reentry_approach_enabled else "disabled"

    @property
    def top_chain_case(self) -> str:
        return "1x_005_D5"


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_206",
            purpose="Direct T-XH-002 control: top drill 005/D5 -> open profile E001 Right Arc/Down-Up.",
            reentry_side="Right",
        ),
        Fixture(
            name="Pieza_207",
            purpose="Direct T-XH-002 control: top drill 005/D5 -> open profile E001 Center Arc/Down-Up.",
            reentry_side="Center",
        ),
        Fixture(
            name="Pieza_208",
            purpose="Direct T-XH-002 control: top drill 005/D5 -> open profile E001 Center without approach/retract.",
            reentry_side="Center",
            reentry_approach_enabled=False,
        ),
    )


def _as_reentry_fixture(fixture: Fixture) -> ReentryFixture:
    return ReentryFixture(
        name=fixture.name,
        purpose=fixture.purpose,
        first_router_family="direct_top_drill",
        top_diameters=fixture.top_diameters,
        reentry_side=fixture.reentry_side,
        reentry_approach_enabled=fixture.reentry_approach_enabled,
        length=fixture.length,
        width=fixture.width,
        depth=fixture.depth,
        origin_x=fixture.origin_x,
        origin_y=fixture.origin_y,
        origin_z=fixture.origin_z,
        execution_fields=fixture.execution_fields,
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, ...]:
    reentry_fixture = _as_reentry_fixture(fixture)
    return (
        *_top_drills(reentry_fixture),
        _open_profile_reentry(reentry_fixture),
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
                "id": f"P-TXH-OPEN-DIRECT-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition_id": "T-XH-002",
                "transition_path": "top_drill_chain->open_profile",
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

    manifest_path = output_dir / "Pieza_206_208_TXH_top_open_profile_direct_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition_id",
        "transition_path",
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
    parser = argparse.ArgumentParser(description="Generate direct top-drill to open-profile PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_206..208 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} direct top/open-profile fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['transition_path']} "
            f"{row['second_router_side']}/{row['second_router_approach']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
