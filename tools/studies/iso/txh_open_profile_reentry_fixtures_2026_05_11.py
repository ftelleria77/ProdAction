"""Generate PGMX fixtures for top-drill -> open-profile router re-entry.

The batch extends the historical ``Pieza_*.pgmx`` sequence with cases that
isolate the Cocina-like second router job: an open E001 profile on side Right
with Arc/Down approach and Arc/Up retract.
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
    build_line_milling_spec,
    build_polyline_milling_spec,
    build_squaring_milling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")
EXPECTED_ISO_DIR = Path(r"P:\USBMIX\ProdAction\ISO")


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    first_router_family: str
    top_diameters: tuple[float, ...]
    reentry_side: str = "Right"
    reentry_approach_enabled: bool = True
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def transition_path(self) -> str:
        return f"{self.first_router_family}->top_drill_chain->open_profile"

    @property
    def top_chain_case(self) -> str:
        tools = ";".join(_top_tool_name(diameter) for diameter in self.top_diameters)
        return f"{len(self.top_diameters)}x_{tools}"

    @property
    def reentry_approach_case(self) -> str:
        return "Arc_Down_Up" if self.reentry_approach_enabled else "disabled"


def _top_tool_name(diameter: float) -> str:
    if diameter == 8.0:
        return "001_D8"
    if diameter == 15.0:
        return "002_D15"
    if diameter == 5.0:
        return "005_D5"
    return f"D{diameter:g}"


def _line_milling(fixture: Fixture) -> object:
    return build_line_milling_spec(
        line_x1=80.0,
        line_y1=60.0,
        line_x2=240.0,
        line_y2=60.0,
        line_feature_name=f"TXH_OPEN_{fixture.name}_FIRST_E001_LINE",
        line_tool_id="1900",
        line_tool_name="E001",
        line_tool_width=18.36,
        line_security_plane=20.0,
        line_side_of_feature="Center",
        line_is_through=False,
        line_target_depth=10.0,
        line_extra_depth=0.0,
        line_approach_enabled=False,
        line_retract_enabled=False,
    )


def _profile_milling(fixture: Fixture) -> object:
    return build_squaring_milling_spec(
        winding="Clockwise",
        feature_name=f"TXH_OPEN_{fixture.name}_FIRST_PROFILE_E001",
        tool_id="1900",
        tool_name="E001",
        tool_width=18.36,
        security_plane=20.0,
        is_through=True,
        target_depth=None,
        extra_depth=1.0,
        approach_enabled=True,
        approach_type="Arc",
        approach_mode="Quote",
        approach_radius_multiplier=2.0,
        approach_speed=-1.0,
        approach_arc_side="Automatic",
        retract_enabled=True,
        retract_type="Arc",
        retract_mode="Quote",
        retract_radius_multiplier=2.0,
        retract_speed=-1.0,
        retract_arc_side="Automatic",
        retract_overlap=0.0,
    )


def _first_router_work(fixture: Fixture) -> object:
    if fixture.first_router_family == "line_milling":
        return _line_milling(fixture)
    if fixture.first_router_family == "profile_milling":
        return _profile_milling(fixture)
    raise ValueError(f"Unsupported router family: {fixture.first_router_family}")


def _top_drill(fixture: Fixture, *, ordinal: int, diameter: float) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TXH_OPEN_{fixture.name}_TOP_{_top_tool_name(diameter)}_{ordinal}",
        plane_name="Top",
        center_x=220.0 + (ordinal * 28.0),
        center_y=190.0,
        diameter=diameter,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _top_drills(fixture: Fixture) -> tuple[DrillingSpec, ...]:
    return tuple(
        _top_drill(fixture, ordinal=ordinal, diameter=diameter)
        for ordinal, diameter in enumerate(fixture.top_diameters, start=1)
    )


def _open_profile_reentry(fixture: Fixture) -> object:
    if fixture.reentry_approach_enabled:
        approach_kwargs = {
            "approach_enabled": True,
            "approach_type": "Arc",
            "approach_mode": "Down",
            "approach_radius_multiplier": 2.0,
            "approach_speed": -1.0,
            "approach_arc_side": "Automatic",
            "retract_enabled": True,
            "retract_type": "Arc",
            "retract_mode": "Up",
            "retract_radius_multiplier": 2.0,
            "retract_speed": -1.0,
            "retract_arc_side": "Automatic",
            "retract_overlap": 0.0,
        }
    else:
        approach_kwargs = {
            "approach_enabled": False,
            "retract_enabled": False,
        }

    return build_polyline_milling_spec(
        points=((-5.0, 44.0), (90.0, 44.0), (90.0, -5.0)),
        feature_name=f"TXH_OPEN_{fixture.name}_SECOND_OPEN_E001_{fixture.reentry_side}",
        tool_id="1900",
        tool_name="E001",
        tool_width=18.36,
        security_plane=20.0,
        side_of_feature=fixture.reentry_side,
        is_through=True,
        target_depth=None,
        extra_depth=1.0,
        **approach_kwargs,
    )


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_192",
            purpose="Control: line E001 -> four top drill 005/D5 -> open profile E001 Right Arc/Down-Up.",
            first_router_family="line_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
        ),
        Fixture(
            name="Pieza_193",
            purpose="Cocina-like: profile E001 -> top drill 005/D5 -> open profile E001 Right Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(5.0,),
        ),
        Fixture(
            name="Pieza_194",
            purpose="Cocina-like: profile E001 -> four top drill 005/D5 -> open profile E001 Right Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
        ),
        Fixture(
            name="Pieza_195",
            purpose="Top-tool control: profile E001 -> top drill 001/D8 -> open profile E001 Right Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(8.0,),
        ),
        Fixture(
            name="Pieza_196",
            purpose="Speed control: profile E001 -> top drill 002/D15 -> open profile E001 Right Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(15.0,),
        ),
        Fixture(
            name="Pieza_197",
            purpose="Side control: profile E001 -> four top drill 005/D5 -> open profile E001 Left Arc/Down-Up.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
            reentry_side="Left",
        ),
        Fixture(
            name="Pieza_198",
            purpose="Approach control: profile E001 -> four top drill 005/D5 -> open profile E001 Right without approach/retract.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
            reentry_approach_enabled=False,
        ),
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, ...]:
    return (
        _first_router_work(fixture),
        *_top_drills(fixture),
        _open_profile_reentry(fixture),
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
                "id": f"P-TXH-OPEN-{fixture.name[-3:]}",
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

    manifest_path = output_dir / "Pieza_192_198_TXH_open_profile_reentry_manifest.csv"
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
    parser = argparse.ArgumentParser(description="Generate top-drill to open-profile re-entry PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_192..198 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} open-profile re-entry fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['first_router_family']}->{row['top_chain_case']}->"
            f"{row['second_router_side']}/{row['second_router_approach']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
