"""Generate PGMX fixtures for profile/line -> top chain -> line studies.

The batch extends the historical ``Pieza_*.pgmx`` sequence with isolated
roundtrip cases that separate the router family before ``T-XH-001`` from the
length and tool of the top-drill chain before ``T-XH-002``.
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
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def transition_path(self) -> str:
        return f"{self.first_router_family}->top_drill_chain->line_milling"

    @property
    def top_chain_case(self) -> str:
        tools = ";".join(_top_tool_name(diameter) for diameter in self.top_diameters)
        return f"{len(self.top_diameters)}x_{tools}"


def _top_tool_name(diameter: float) -> str:
    if diameter == 8.0:
        return "001_D8"
    if diameter == 15.0:
        return "002_D15"
    if diameter == 5.0:
        return "005_D5"
    return f"D{diameter:g}"


def _line_milling(fixture: Fixture, *, which: str) -> object:
    y = 60.0 if which == "first" else 130.0
    return build_line_milling_spec(
        line_x1=80.0,
        line_y1=y,
        line_x2=240.0,
        line_y2=y,
        line_feature_name=f"TXH_CHAIN_{fixture.name}_{which.upper()}_E001_LINE",
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
        winding="Antihorario",
        feature_name=f"TXH_CHAIN_{fixture.name}_PROFILE_E001",
        tool_id="1900",
        tool_name="E001",
        tool_width=18.36,
        security_plane=20.0,
        is_through=False,
        target_depth=10.0,
        extra_depth=0.0,
        approach_enabled=False,
        retract_enabled=False,
    )


def _first_router_work(fixture: Fixture) -> object:
    if fixture.first_router_family == "line_milling":
        return _line_milling(fixture, which="first")
    if fixture.first_router_family == "profile_milling":
        return _profile_milling(fixture)
    raise ValueError(f"Unsupported router family: {fixture.first_router_family}")


def _top_drill(fixture: Fixture, *, ordinal: int, diameter: float) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TXH_CHAIN_{fixture.name}_TOP_{_top_tool_name(diameter)}_{ordinal}",
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


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_179",
            purpose="Control chain: line E001 -> two top drill 005/D5 -> line E001.",
            first_router_family="line_milling",
            top_diameters=(5.0, 5.0),
        ),
        Fixture(
            name="Pieza_180",
            purpose="Control chain: line E001 -> four top drill 005/D5 -> line E001.",
            first_router_family="line_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
        ),
        Fixture(
            name="Pieza_181",
            purpose="Profile factor: profile E001 -> one top drill 005/D5 -> line E001.",
            first_router_family="profile_milling",
            top_diameters=(5.0,),
        ),
        Fixture(
            name="Pieza_182",
            purpose="Profile plus short chain: profile E001 -> two top drill 005/D5 -> line E001.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0),
        ),
        Fixture(
            name="Pieza_183",
            purpose="Profile plus Cocina-like chain: profile E001 -> four top drill 005/D5 -> line E001.",
            first_router_family="profile_milling",
            top_diameters=(5.0, 5.0, 5.0, 5.0),
        ),
        Fixture(
            name="Pieza_184",
            purpose="Profile top-tool control: profile E001 -> top drill 001/D8 -> line E001.",
            first_router_family="profile_milling",
            top_diameters=(8.0,),
        ),
        Fixture(
            name="Pieza_185",
            purpose="Profile speed control: profile E001 -> top drill 002/D15 -> line E001.",
            first_router_family="profile_milling",
            top_diameters=(15.0,),
        ),
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, ...]:
    return (
        _first_router_work(fixture),
        *_top_drills(fixture),
        _line_milling(fixture, which="second"),
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
                "id": f"P-TXH-CHAIN-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition_path": fixture.transition_path,
                "first_router_family": fixture.first_router_family,
                "first_router_tool": "E001",
                "top_diameters": ";".join(f"{diameter:g}" for diameter in fixture.top_diameters),
                "top_chain_case": fixture.top_chain_case,
                "second_router_family": "line_milling",
                "second_router_tool": "E001",
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "Pieza_179_185_TXH_profile_top_chain_manifest.csv"
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
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate profile/line-top-chain PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_179..185 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} profile/line top-chain fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['first_router_family']}->{row['top_chain_case']}->"
            f"{row['second_router_family']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
