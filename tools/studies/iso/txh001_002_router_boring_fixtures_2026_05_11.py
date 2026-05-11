"""Generate PGMX fixtures for T-XH-001 and T-XH-002 head-switching study.

The batch extends the historical ``Pieza_*.pgmx`` sequence with isolated
fixtures for router -> boring head and boring head -> router transitions.
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
    index: int
    name: str
    transition_id: str
    order: str
    boring_family: str
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def expected_speed_case(self) -> str:
        if self.transition_id == "T-XH-001":
            return "router_18000_to_boring_head"
        return "boring_head_to_router_18000"


def _line_e004(fixture: Fixture) -> object:
    offset = (fixture.index - 1) * 8.0
    return build_line_milling_spec(
        line_x1=80.0 + offset,
        line_y1=70.0,
        line_x2=220.0 + offset,
        line_y2=70.0,
        line_feature_name=f"{fixture.transition_id}_{fixture.index:02d}_LINE_E004",
        line_tool_id="1903",
        line_tool_name="E004",
        line_tool_width=4.0,
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
        feature_name=f"{fixture.transition_id}_{fixture.index:02d}_TOP_D8",
        plane_name="Top",
        center_x=260.0,
        center_y=180.0,
        diameter=8.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _side_drill(fixture: Fixture) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=f"{fixture.transition_id}_{fixture.index:02d}_FRONT_D8",
        plane_name="Front",
        center_x=fixture.length * 0.5,
        center_y=fixture.depth / 2.0,
        diameter=8.0,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _top_slot(fixture: Fixture) -> SlotMillingSpec:
    return build_slot_milling_spec(
        feature_name=f"{fixture.transition_id}_{fixture.index:02d}_TOP_SLOT_082",
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


def _boring_work(fixture: Fixture) -> object:
    if fixture.boring_family == "top_drill":
        return _top_drill(fixture)
    if fixture.boring_family == "side_drill":
        return _side_drill(fixture)
    if fixture.boring_family == "slot_milling":
        return _top_slot(fixture)
    raise ValueError(f"Unsupported boring family: {fixture.boring_family}")


def build_fixtures() -> tuple[Fixture, ...]:
    specs = [
        ("T-XH-001", "router->top_drill", "top_drill"),
        ("T-XH-001", "router->side_drill", "side_drill"),
        ("T-XH-001", "router->slot_milling", "slot_milling"),
        ("T-XH-002", "top_drill->router", "top_drill"),
        ("T-XH-002", "side_drill->router", "side_drill"),
        ("T-XH-002", "slot_milling->router", "slot_milling"),
    ]
    return tuple(
        Fixture(
            index=index,
            name=f"Pieza_{158 + index:03d}",
            transition_id=transition_id,
            order=order,
            boring_family=boring_family,
        )
        for index, (transition_id, order, boring_family) in enumerate(specs, start=1)
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, object]:
    router = _line_e004(fixture)
    boring = _boring_work(fixture)
    if fixture.transition_id == "T-XH-001":
        return router, boring
    return boring, router


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
                "transition": fixture.order,
                "router_tool": "E004",
                "boring_family": fixture.boring_family,
                "boring_tool": _boring_tool_name(fixture.boring_family),
                "expected_speed_case": fixture.expected_speed_case,
                "sha256": result.sha256,
                "purpose": (
                    f"{fixture.transition_id}: isolate {fixture.order} "
                    f"with router E004 and {fixture.boring_family}."
                ),
            }
        )

    manifest_path = output_dir / "Pieza_159_164_TXH001_002_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition_id",
        "transition",
        "router_tool",
        "boring_family",
        "boring_tool",
        "expected_speed_case",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def _boring_tool_name(boring_family: str) -> str:
    if boring_family == "top_drill":
        return "Auto D8 top drill"
    if boring_family == "side_drill":
        return "Auto D8 Front side drill"
    if boring_family == "slot_milling":
        return "082"
    raise ValueError(f"Unsupported boring family: {boring_family}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T-XH-001/002 router-boring PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_159..164 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-XH-001/002 fixtures in {args.output_dir}")
    for row in rows:
        print(
            f"{row['name']} {row['transition_id']} {row['transition']} "
            f"{row['boring_family']} {row['expected_speed_case']} {row['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
