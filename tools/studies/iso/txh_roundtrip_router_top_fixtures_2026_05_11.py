"""Generate PGMX fixtures for router -> top drill -> router roundtrips.

The batch extends the historical ``Pieza_*.pgmx`` sequence with isolated
roundtrip cases that separate same-router-tool re-entry from router-tool
changes after a top-drill operation.
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
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")
EXPECTED_ISO_DIR = Path(r"P:\USBMIX\ProdAction\ISO")


@dataclass(frozen=True)
class RouterTool:
    name: str
    tool_id: str
    width: float


ROUTER_TOOLS = {
    "E001": RouterTool(name="E001", tool_id="1900", width=18.36),
    "E004": RouterTool(name="E004", tool_id="1903", width=4.0),
}


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    first_router_tool: str
    top_diameter: float
    second_router_tool: str
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def transition(self) -> str:
        return "line_milling->top_drill->line_milling"

    @property
    def router_tool_case(self) -> str:
        if self.first_router_tool == self.second_router_tool:
            return "same_router_tool"
        return f"{self.first_router_tool}_to_{self.second_router_tool}"

    @property
    def top_tool_case(self) -> str:
        if self.top_diameter == 8.0:
            return "top_001_d8_6000"
        if self.top_diameter == 5.0:
            return "top_005_d5_6000"
        if self.top_diameter == 15.0:
            return "top_002_d15_4000"
        return f"top_d{self.top_diameter:g}"


def _router_line(fixture: Fixture, *, which: str, tool_name: str) -> object:
    tool = ROUTER_TOOLS[tool_name]
    y = 60.0 if which == "first" else 130.0
    return build_line_milling_spec(
        line_x1=80.0,
        line_y1=y,
        line_x2=240.0,
        line_y2=y,
        line_feature_name=f"TXH_RT_{fixture.name}_{which.upper()}_{tool.name}",
        line_tool_id=tool.tool_id,
        line_tool_name=tool.name,
        line_tool_width=tool.width,
        line_security_plane=20.0,
        line_side_of_feature="Center",
        line_is_through=False,
        line_target_depth=10.0,
        line_extra_depth=0.0,
        line_approach_enabled=False,
        line_retract_enabled=False,
    )


def _top_drill(fixture: Fixture) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"TXH_RT_{fixture.name}_TOP_D{fixture.top_diameter:g}",
        plane_name="Top",
        center_x=280.0,
        center_y=190.0,
        diameter=fixture.top_diameter,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_171",
            purpose="Roundtrip: router E001 -> top drill 005/D5 -> router E001.",
            first_router_tool="E001",
            top_diameter=5.0,
            second_router_tool="E001",
        ),
        Fixture(
            name="Pieza_172",
            purpose="Roundtrip control: router E001 -> top drill 001/D8 -> router E001.",
            first_router_tool="E001",
            top_diameter=8.0,
            second_router_tool="E001",
        ),
        Fixture(
            name="Pieza_173",
            purpose="Roundtrip speed control: router E001 -> top drill 002/D15 -> router E001.",
            first_router_tool="E001",
            top_diameter=15.0,
            second_router_tool="E001",
        ),
        Fixture(
            name="Pieza_174",
            purpose="Roundtrip: router E004 -> top drill 005/D5 -> router E004.",
            first_router_tool="E004",
            top_diameter=5.0,
            second_router_tool="E004",
        ),
        Fixture(
            name="Pieza_175",
            purpose="Roundtrip control: router E004 -> top drill 001/D8 -> router E004.",
            first_router_tool="E004",
            top_diameter=8.0,
            second_router_tool="E004",
        ),
        Fixture(
            name="Pieza_176",
            purpose="Roundtrip speed control: router E004 -> top drill 002/D15 -> router E004.",
            first_router_tool="E004",
            top_diameter=15.0,
            second_router_tool="E004",
        ),
        Fixture(
            name="Pieza_177",
            purpose="Roundtrip with router change: router E001 -> top drill 005/D5 -> router E004.",
            first_router_tool="E001",
            top_diameter=5.0,
            second_router_tool="E004",
        ),
        Fixture(
            name="Pieza_178",
            purpose="Roundtrip with router change: router E004 -> top drill 005/D5 -> router E001.",
            first_router_tool="E004",
            top_diameter=5.0,
            second_router_tool="E001",
        ),
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, object, object]:
    return (
        _router_line(fixture, which="first", tool_name=fixture.first_router_tool),
        _top_drill(fixture),
        _router_line(fixture, which="second", tool_name=fixture.second_router_tool),
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
                "id": f"P-TXH-RT-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition_path": fixture.transition,
                "first_router_tool": fixture.first_router_tool,
                "top_diameter": f"{fixture.top_diameter:g}",
                "second_router_tool": fixture.second_router_tool,
                "router_tool_case": fixture.router_tool_case,
                "top_tool_case": fixture.top_tool_case,
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / "Pieza_171_178_TXH_roundtrip_router_top_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition_path",
        "first_router_tool",
        "top_diameter",
        "second_router_tool",
        "router_tool_case",
        "top_tool_case",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate router-top-router roundtrip PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_171..178 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} router-top-router roundtrip fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['first_router_tool']}->{row['top_tool_case']}->"
            f"{row['second_router_tool']} {row['router_tool_case']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
