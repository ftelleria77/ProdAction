"""Generate router-tool mirror PGMX fixtures for ISO state synthesis.

Recommended run:

    py -3 -m tools.studies.iso.router_tool_mirror_fixtures_2026_05_07 --output-dir "S:\\Maestro\\Projects\\ProdAction\\ISO\\router_tool_mirror_fixtures_2026-05-07"
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.synthesize_pgmx import (  # noqa: E402
    build_circle_milling_spec,
    build_line_milling_spec,
    build_polyline_milling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(
    r"S:\Maestro\Projects\ProdAction\ISO\router_tool_mirror_fixtures_2026-05-07"
)
TOOL_CATALOG_PATH = ROOT / "tools" / "tool_catalog.csv"
TOOL_NAMES = ("E001", "E002", "E003", "E004", "E005", "E006", "E007")


@dataclass(frozen=True)
class ToolInfo:
    tool_id: str
    name: str
    width: float


@dataclass(frozen=True)
class Fixture:
    code: str
    purpose: str
    build_milling: Callable[[ToolInfo, str], object]


def _load_tools() -> dict[str, ToolInfo]:
    rows: dict[str, ToolInfo] = {}
    with TOOL_CATALOG_PATH.open(newline="", encoding="utf-8") as catalog_file:
        reader = csv.DictReader(catalog_file)
        for row in reader:
            name = (row.get("name") or "").strip()
            if name not in TOOL_NAMES:
                continue
            rows[name] = ToolInfo(
                tool_id=(row.get("id") or "").strip(),
                name=name,
                width=float((row.get("diameter") or "0").replace(",", ".")),
            )
    missing = [name for name in TOOL_NAMES if name not in rows]
    if missing:
        raise ValueError(f"Faltan herramientas en {TOOL_CATALOG_PATH}: {', '.join(missing)}")
    return rows


def _line_vertical(tool: ToolInfo, feature_name: str) -> object:
    return build_line_milling_spec(
        line_x1=200.0,
        line_y1=50.0,
        line_x2=200.0,
        line_y2=200.0,
        line_feature_name=feature_name,
        line_tool_id=tool.tool_id,
        line_tool_name=tool.name,
        line_tool_width=tool.width,
        line_security_plane=20.0,
        line_side_of_feature="Center",
        line_is_through=False,
        line_target_depth=15.0,
        line_extra_depth=0.0,
        line_approach_enabled=False,
        line_retract_enabled=False,
    )


def _open_polyline(tool: ToolInfo, feature_name: str) -> object:
    return build_polyline_milling_spec(
        points=((150.0, 0.0), (100.0, 150.0), (300.0, 100.0), (250.0, 250.0)),
        feature_name=feature_name,
        tool_id=tool.tool_id,
        tool_name=tool.name,
        tool_width=tool.width,
        security_plane=20.0,
        side_of_feature="Center",
        is_through=True,
        extra_depth=0.5,
        approach_enabled=False,
        retract_enabled=False,
    )


def _circle_ccw(tool: ToolInfo, feature_name: str) -> object:
    return _circle(tool, feature_name, "CounterClockwise")


def _circle_cw(tool: ToolInfo, feature_name: str) -> object:
    return _circle(tool, feature_name, "Clockwise")


def _circle(tool: ToolInfo, feature_name: str, winding: str) -> object:
    return build_circle_milling_spec(
        center_x=200.0,
        center_y=125.0,
        radius=50.0,
        winding=winding,
        feature_name=feature_name,
        tool_id=tool.tool_id,
        tool_name=tool.name,
        tool_width=tool.width,
        security_plane=20.0,
        side_of_feature="Center",
        is_through=True,
        extra_depth=0.5,
        approach_enabled=False,
        retract_enabled=False,
    )


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture("LINE_V_P15", "Vertical center line, target depth 15.", _line_vertical),
        Fixture("OPEN_POLY_THRU_E05", "Open polyline, through with extra depth 0.5.", _open_polyline),
        Fixture("CIRCLE_D100_CCW_THRU_E05", "Counterclockwise circle D100, through with extra depth 0.5.", _circle_ccw),
        Fixture("CIRCLE_D100_CW_THRU_E05", "Clockwise circle D100, through with extra depth 0.5.", _circle_cw),
    )


def generate(output_dir: Path) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tools = _load_tools()
    rows: list[dict[str, str]] = []

    for tool_name in TOOL_NAMES:
        tool = tools[tool_name]
        for fixture in build_fixtures():
            name = f"Pieza_Tool_{tool.name}_{fixture.code}"
            output_path = output_dir / f"{name}.pgmx"
            feature_name = name.removeprefix("Pieza_")
            request = build_synthesis_request(
                output_path=output_path,
                piece_name=name,
                length=400.0,
                width=250.0,
                depth=18.0,
                origin_x=5.0,
                origin_y=5.0,
                origin_z=25.0,
                execution_fields="HG",
                ordered_machinings=(fixture.build_milling(tool, feature_name),),
            )
            result = synthesize_request(request)
            rows.append(
                {
                    "name": name,
                    "tool": tool.name,
                    "tool_id": tool.tool_id,
                    "tool_width": f"{tool.width:.3f}",
                    "fixture": fixture.code,
                    "pgmx_path": str(result.output_path),
                    "sha256": result.sha256,
                    "purpose": fixture.purpose,
                }
            )

    manifest_path = output_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=[
                "name",
                "tool",
                "tool_id",
                "tool_width",
                "fixture",
                "pgmx_path",
                "sha256",
                "purpose",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate E00x router-tool mirror PGMX fixtures for ISO synthesis validation."
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
        print(f"{row['name']}  {row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
