"""Generate router compensation mirror PGMX fixtures for ISO state synthesis.

Recommended run:

    py -3 -m tools.studies.iso.router_compensation_tool_mirror_fixtures_2026_05_07 --output-dir "S:\\Maestro\\Projects\\ProdAction\\ISO\\router_compensation_tool_mirror_fixtures_2026-05-07"
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
    build_polyline_milling_spec,
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(
    r"S:\Maestro\Projects\ProdAction\ISO\router_compensation_tool_mirror_fixtures_2026-05-07"
)
TOOL_CATALOG_PATH = ROOT / "tools" / "tool_catalog.csv"
TOOL_NAMES = ("E001", "E002", "E003", "E004", "E005", "E006", "E007")
POLYLINE_POINTS = ((150.0, 0.0), (100.0, 150.0), (300.0, 100.0), (250.0, 250.0))


@dataclass(frozen=True)
class ToolInfo:
    tool_id: str
    name: str
    width: float


@dataclass(frozen=True)
class Fixture:
    code: str
    side_of_feature: str
    approach_type: str
    retract_type: str
    purpose: str


def _load_tools() -> dict[str, ToolInfo]:
    rows: dict[str, ToolInfo] = {}
    with TOOL_CATALOG_PATH.open(newline="", encoding="utf-8-sig") as catalog_file:
        reader = csv.DictReader(catalog_file)
        for row in reader:
            name = (row.get("name") or "").strip()
            if name not in TOOL_NAMES:
                continue
            rows[name] = ToolInfo(
                tool_id=(row.get("tool_id") or "").strip(),
                name=name,
                width=float((row.get("diameter") or "0").replace(",", ".")),
            )
    missing = [name for name in TOOL_NAMES if name not in rows]
    if missing:
        raise ValueError(f"Faltan herramientas en {TOOL_CATALOG_PATH}: {', '.join(missing)}")
    return rows


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            "OPEN_POLY_LEFT_LINE_DU_R2",
            "Left",
            "Line",
            "Line",
            "Open polyline, Left compensation, Line Down/Up, radius multiplier 2.",
        ),
        Fixture(
            "OPEN_POLY_RIGHT_LINE_DU_R2",
            "Right",
            "Line",
            "Line",
            "Open polyline, Right compensation, Line Down/Up, radius multiplier 2.",
        ),
        Fixture(
            "OPEN_POLY_LEFT_ARC_DU_R2",
            "Left",
            "Arc",
            "Arc",
            "Open polyline, Left compensation, Arc Down/Up, radius multiplier 2.",
        ),
        Fixture(
            "OPEN_POLY_RIGHT_ARC_DU_R2",
            "Right",
            "Arc",
            "Arc",
            "Open polyline, Right compensation, Arc Down/Up, radius multiplier 2.",
        ),
    )


def _build_milling(tool: ToolInfo, fixture: Fixture, feature_name: str) -> object:
    return build_polyline_milling_spec(
        points=POLYLINE_POINTS,
        feature_name=feature_name,
        tool_id=tool.tool_id,
        tool_name=tool.name,
        tool_width=tool.width,
        security_plane=20.0,
        side_of_feature=fixture.side_of_feature,
        is_through=True,
        extra_depth=0.5,
        approach_enabled=True,
        approach_type=fixture.approach_type,
        approach_mode="Down",
        approach_radius_multiplier=2.0,
        retract_enabled=True,
        retract_type=fixture.retract_type,
        retract_mode="Up",
        retract_radius_multiplier=2.0,
        retract_overlap=0.0,
    )


def generate(output_dir: Path) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tools = _load_tools()
    rows: list[dict[str, str]] = []

    for tool_name in TOOL_NAMES:
        tool = tools[tool_name]
        for fixture in build_fixtures():
            name = f"Pieza_CompTool_{tool.name}_{fixture.code}"
            output_path = output_dir / f"{name}.pgmx"
            feature_name = name.removeprefix("Pieza_")
            row = {
                "name": name,
                "tool": tool.name,
                "tool_id": tool.tool_id,
                "tool_width": f"{tool.width:.3f}",
                "fixture": fixture.code,
                "side_of_feature": fixture.side_of_feature,
                "approach_type": fixture.approach_type,
                "retract_type": fixture.retract_type,
                "pgmx_path": str(output_path),
                "status": "failed",
                "sha256": "",
                "error": "",
                "purpose": fixture.purpose,
            }
            try:
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
                    ordered_machinings=(_build_milling(tool, fixture, feature_name),),
                )
                result = synthesize_request(request)
                row["status"] = "generated"
                row["sha256"] = result.sha256
                row["pgmx_path"] = str(result.output_path)
            except Exception as exc:  # noqa: BLE001 - manifest must record per-fixture generation failures.
                row["error"] = str(exc)
            rows.append(row)

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
                "side_of_feature",
                "approach_type",
                "retract_type",
                "pgmx_path",
                "status",
                "sha256",
                "error",
                "purpose",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate E00x compensated open-polyline mirror PGMX fixtures."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where .pgmx fixtures and manifest.csv will be written.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Return a non-zero exit code if any fixture cannot be generated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir)
    generated = [row for row in rows if row["status"] == "generated"]
    failed = [row for row in rows if row["status"] != "generated"]
    print(f"Generated {len(generated)} PGMX fixtures in {args.output_dir}")
    print(f"Failed {len(failed)} PGMX fixtures; see manifest.csv")
    for row in generated:
        print(f"{row['name']}  {row['sha256']}")
    for row in failed:
        print(f"FAILED {row['name']}: {row['error']}")
    return 1 if args.fail_on_error and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
