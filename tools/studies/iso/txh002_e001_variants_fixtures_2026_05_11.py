"""Generate PGMX fixtures for T-XH-002 E001 destination variants.

The batch extends the historical ``Pieza_*.pgmx`` sequence with isolated
boring-head -> router transitions.  It focuses on the E001 router re-entry
observed in Cocina, plus one E004 control case.
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
    build_line_milling_spec,
    build_slot_milling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")
EXPECTED_ISO_DIR = Path(r"P:\USBMIX\ProdAction\ISO")


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    boring_family: str
    router_tool: str
    top_diameters: tuple[float, ...] = ()
    side_plane: str = "Right"
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def transition(self) -> str:
        return f"{self.boring_family}->line_milling"

    @property
    def expected_speed_case(self) -> str:
        if self.boring_family == "slot_milling":
            return "slot_4000_to_router_18000"
        return "boring_6000_or_4000_to_router_18000"


def _router_line(fixture: Fixture) -> object:
    if fixture.router_tool == "E001":
        tool_id = "1900"
        tool_width = 18.36
    elif fixture.router_tool == "E004":
        tool_id = "1903"
        tool_width = 4.0
    else:
        raise ValueError(f"Unsupported router tool: {fixture.router_tool}")

    return build_line_milling_spec(
        line_x1=80.0,
        line_y1=70.0,
        line_x2=240.0,
        line_y2=70.0,
        line_feature_name=f"TXH002_{fixture.name}_{fixture.router_tool}_LINE",
        line_tool_id=tool_id,
        line_tool_name=fixture.router_tool,
        line_tool_width=tool_width,
        line_security_plane=20.0,
        line_side_of_feature="Center",
        line_is_through=False,
        line_target_depth=10.0,
        line_extra_depth=0.0,
        line_approach_enabled=False,
        line_retract_enabled=False,
    )


def _top_drill(fixture: Fixture, *, ordinal: int, diameter: float) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TXH002_{fixture.name}_TOP_D{diameter:g}_{ordinal}",
        plane_name="Top",
        center_x=250.0 + (ordinal * 30.0),
        center_y=180.0,
        diameter=diameter,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _side_drill(fixture: Fixture) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TXH002_{fixture.name}_{fixture.side_plane.upper()}_D8",
        plane_name=fixture.side_plane,
        center_x=fixture.length * 0.5,
        center_y=fixture.depth / 2.0,
        diameter=8.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _top_slot(fixture: Fixture) -> SlotMillingSpec:
    return build_slot_milling_spec(
        feature_name=f"TXH002_{fixture.name}_TOP_SLOT_082",
        start_x=120.0,
        start_y=140.0,
        end_x=300.0,
        end_y=140.0,
        plane_name="Top",
        side_of_feature="Center",
        tool_name="082",
        tool_width=3.8,
        security_plane=20.0,
        is_through=False,
        target_depth=10.0,
    )


def _boring_works(fixture: Fixture) -> tuple[object, ...]:
    if fixture.boring_family == "top_drill":
        return tuple(
            _top_drill(fixture, ordinal=ordinal, diameter=diameter)
            for ordinal, diameter in enumerate(fixture.top_diameters, start=1)
        )
    if fixture.boring_family == "side_drill":
        return (_side_drill(fixture),)
    if fixture.boring_family == "slot_milling":
        return (_top_slot(fixture),)
    raise ValueError(f"Unsupported boring family: {fixture.boring_family}")


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_165",
            purpose="T-XH-002: single top drill 005/D5 to router E001.",
            boring_family="top_drill",
            top_diameters=(5.0,),
            router_tool="E001",
        ),
        Fixture(
            name="Pieza_166",
            purpose="T-XH-002: two top drill 005/D5 operations to router E001.",
            boring_family="top_drill",
            top_diameters=(5.0, 5.0),
            router_tool="E001",
        ),
        Fixture(
            name="Pieza_167",
            purpose="T-XH-002: top drill 002/D15 at 4000 rpm to router E001.",
            boring_family="top_drill",
            top_diameters=(15.0,),
            router_tool="E001",
        ),
        Fixture(
            name="Pieza_168",
            purpose="T-XH-002 control: top drill 005/D5 to router E004.",
            boring_family="top_drill",
            top_diameters=(5.0,),
            router_tool="E004",
        ),
        Fixture(
            name="Pieza_169",
            purpose="T-XH-002: right side drill 060/D8 to router E001.",
            boring_family="side_drill",
            router_tool="E001",
            side_plane="Right",
        ),
        Fixture(
            name="Pieza_170",
            purpose="T-XH-002: top slot 082 to router E001.",
            boring_family="slot_milling",
            router_tool="E001",
        ),
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, ...]:
    return (*_boring_works(fixture), _router_line(fixture))


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
                "id": f"P-TXH002-{fixture.router_tool}-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition_id": "T-XH-002",
                "transition": fixture.transition,
                "router_tool": fixture.router_tool,
                "boring_family": fixture.boring_family,
                "top_diameters": ";".join(f"{diameter:g}" for diameter in fixture.top_diameters),
                "side_plane": fixture.side_plane if fixture.boring_family == "side_drill" else "",
                "expected_speed_case": fixture.expected_speed_case,
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "Pieza_165_170_TXH002_E001_variants_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition_id",
        "transition",
        "router_tool",
        "boring_family",
        "top_diameters",
        "side_plane",
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
    parser = argparse.ArgumentParser(description="Generate T-XH-002 E001 variant PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_165..170 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-XH-002 E001 variant fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['transition_id']} {row['transition']} "
            f"{row['router_tool']} {row['expected_speed_case']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
