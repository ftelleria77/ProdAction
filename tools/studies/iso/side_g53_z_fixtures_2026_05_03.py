"""Generate side-drilling PGMX fixtures for G53 Z park investigation.

The batch isolates intermediate side-face park moves such as
`G0 G53 Z149.500` and `G0 G53 Z149.450` by varying side faces, local hole
positions, panel thickness, and workpiece origin.

Recommended factory run:

    python -m tools.studies.iso.side_g53_z_fixtures_2026_05_03 --output-dir "S:\\Maestro\\Projects\\ProdAction\\ISO\\side_g53_z_fixtures_2026-05-03"
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

from tools.pgmx_adapters import adapt_pgmx_path  # noqa: E402
from tools.synthesize_pgmx import (  # noqa: E402
    DrillingSpec,
    build_drilling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = ROOT / "tmp" / "iso_side_g53_z_fixtures"


@dataclass(frozen=True)
class PieceProfile:
    code: str
    length: float
    width: float
    depth: float
    origin_x: float
    origin_y: float
    origin_z: float


@dataclass(frozen=True)
class Fixture:
    name: str
    profile: PieceProfile
    purpose: str
    focus: str
    drillings: Sequence[DrillingSpec]


PROFILES = (
    PieceProfile("A", 400.0, 300.0, 25.0, 5.0, 5.0, 25.0),
    PieceProfile("B", 400.0, 300.0, 18.0, 10.0, 10.0, 40.0),
)

POSITION_CODES = ("Low", "Mid", "High")


def _face_span(profile: PieceProfile, plane_name: str) -> float:
    if plane_name in {"Front", "Back"}:
        return profile.length
    if plane_name in {"Left", "Right"}:
        return profile.width
    raise ValueError(f"Unsupported side face: {plane_name}")


def _face_position(profile: PieceProfile, plane_name: str, position_code: str) -> float:
    span = _face_span(profile, plane_name)
    positions = {
        "Low": span * 0.2,
        "Mid": span * 0.5,
        "High": span * 0.8,
    }
    return positions[position_code]


def _side_drill(profile: PieceProfile, plane_name: str, position_code: str) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"{plane_name.upper()}_D8_{position_code.upper()}",
        plane_name=plane_name,
        center_x=_face_position(profile, plane_name, position_code),
        center_y=profile.depth / 2.0,
        diameter=8.0,
        target_depth=28.0,
        tool_resolution="Auto",
    )


def _single_face_fixture(
    index: int,
    profile: PieceProfile,
    plane_name: str,
) -> Fixture:
    return Fixture(
        name=f"ISO_SIDEG53_{profile.code}_{index:03d}_{plane_name}_3Pos",
        profile=profile,
        purpose=f"{profile.code}: three D8 holes on {plane_name}, at 20/50/80 percent of local side span.",
        focus=f"same-face {plane_name} reentry without side-face change",
        drillings=tuple(
            _side_drill(profile, plane_name, position_code)
            for position_code in POSITION_CODES
        ),
    )


def _all_faces_fixture(
    index: int,
    profile: PieceProfile,
    position_code: str,
) -> Fixture:
    return Fixture(
        name=f"ISO_SIDEG53_{profile.code}_{index:03d}_AllFaces_{position_code}",
        profile=profile,
        purpose=(
            f"{profile.code}: one D8 hole on each side face at {position_code} "
            "position; sorted workplan should exercise Front->Back, Back->Left, Left->Right."
        ),
        focus="multi-face transition sequence: Front->Back, Back->Left, Left->Right",
        drillings=tuple(
            _side_drill(profile, plane_name, position_code)
            for plane_name in ("Front", "Back", "Left", "Right")
        ),
    )


def _transition_fixture(
    index: int,
    profile: PieceProfile,
    first_face: str,
    second_face: str,
) -> Fixture:
    return Fixture(
        name=f"ISO_SIDEG53_{profile.code}_{index:03d}_{first_face}_{second_face}_Mid",
        profile=profile,
        purpose=(
            f"{profile.code}: center D8 hole on {first_face} and {second_face}; "
            f"isolates the sorted transition {first_face}->{second_face}."
        ),
        focus=f"isolated transition: {first_face}->{second_face}",
        drillings=(
            _side_drill(profile, first_face, "Mid"),
            _side_drill(profile, second_face, "Mid"),
        ),
    )


def build_fixtures() -> list[Fixture]:
    fixtures: list[Fixture] = []
    for profile in PROFILES:
        base_index = 1 if profile.code == "A" else 101
        for offset, plane_name in enumerate(("Front", "Back", "Left", "Right")):
            fixtures.append(_single_face_fixture(base_index + offset, profile, plane_name))
        for offset, position_code in enumerate(POSITION_CODES, start=4):
            fixtures.append(_all_faces_fixture(base_index + offset, profile, position_code))
        fixtures.extend(
            (
                _transition_fixture(base_index + 7, profile, "Front", "Left"),
                _transition_fixture(base_index + 8, profile, "Front", "Right"),
                _transition_fixture(base_index + 9, profile, "Back", "Right"),
            )
        )
    return fixtures


def generate(output_dir: Path) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
        profile = fixture.profile
        request = build_synthesis_request(
            output_path=output_path,
            piece_name=fixture.name,
            length=profile.length,
            width=profile.width,
            depth=profile.depth,
            origin_x=profile.origin_x,
            origin_y=profile.origin_y,
            origin_z=profile.origin_z,
            execution_fields="HG",
            drillings=fixture.drillings,
        )
        result = synthesize_request(request)
        adaptation = adapt_pgmx_path(result.output_path)
        rows.append(
            {
                "name": fixture.name,
                "group": profile.code,
                "length": f"{profile.length:g}",
                "width": f"{profile.width:g}",
                "depth": f"{profile.depth:g}",
                "origin_x": f"{profile.origin_x:g}",
                "origin_y": f"{profile.origin_y:g}",
                "origin_z": f"{profile.origin_z:g}",
                "focus": fixture.focus,
                "purpose": fixture.purpose,
                "drillings": str(len(fixture.drillings)),
                "adapted": str(len(adaptation.adapted_entries)),
                "unsupported": str(len(adaptation.unsupported_entries)),
                "ignored": str(len(adaptation.ignored_entries)),
                "pgmx_path": str(result.output_path),
                "sha256": result.sha256,
            }
        )

    manifest_path = output_dir / "manifest.csv"
    fieldnames = [
        "name",
        "group",
        "length",
        "width",
        "depth",
        "origin_x",
        "origin_y",
        "origin_z",
        "focus",
        "purpose",
        "drillings",
        "adapted",
        "unsupported",
        "ignored",
        "pgmx_path",
        "sha256",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate side-drilling PGMX fixtures for G53 Z park investigation."
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
        print(f"{row['name']}  {row['sha256']}  unsupported={row['unsupported']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
