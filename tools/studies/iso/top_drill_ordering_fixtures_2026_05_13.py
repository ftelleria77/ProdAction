"""Generate and analyze top-drill ordering fixtures.

This batch isolates how Maestro orders mixed top-drill holes that use tools
``005``, ``002`` and ``001``.  The PGMX source order is intentionally different
from the suspected Maestro order so the resulting ISO can reveal whether the
postprocessor sorts by geometry, source order, previous router context, or a
combination of those factors.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso_state_synthesis.pgmx_source import (  # noqa: E402
    _ordered_resolved_working_steps,
    _resolved_step_family,
)
from tools.pgmx_snapshot import (  # noqa: E402
    PgmxResolvedWorkingStepSnapshot,
    read_pgmx_snapshot,
)
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
MANIFEST_NAME = "Pieza_209_214_TBH001_top_order_manifest.csv"
ANALYSIS_NAME = "Pieza_209_214_TBH001_top_order_analysis.csv"

TOOL_BY_DIAMETER = {
    5.0: "005",
    8.0: "001",
    15.0: "002",
}


@dataclass(frozen=True)
class Hole:
    label: str
    x: float
    y: float
    diameter: float

    @property
    def tool(self) -> str:
        return TOOL_BY_DIAMETER[self.diameter]

    @property
    def encoded(self) -> str:
        return f"{self.label}:{self.tool}@{self.x:g},{self.y:g}"


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    context: str
    hole_labels: tuple[str, ...]
    length: float = 820.0
    width: float = 620.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def source_order_case(self) -> str:
        if self.hole_labels == SUSPECTED_SERPENTINE_ORDER:
            return "suspected_serpentine"
        if self.hole_labels == tuple(reversed(SUSPECTED_SERPENTINE_ORDER)):
            return "reverse_serpentine"
        return "scrambled"


HOLES: dict[str, Hole] = {
    "A": Hole("A", 33.0, 32.0, 15.0),
    "B": Hole("B", 250.5, 60.0, 5.0),
    "C": Hole("C", 450.5, 60.0, 5.0),
    "D": Hole("D", 450.5, 532.0, 5.0),
    "E": Hole("E", 250.5, 532.0, 5.0),
    "F": Hole("F", 33.0, 553.0, 15.0),
    "G": Hole("G", 741.0, 53.0, 8.0),
    "H": Hole("H", 773.0, 53.0, 8.0),
    "I": Hole("I", 773.0, 562.0, 8.0),
    "J": Hole("J", 741.0, 562.0, 8.0),
}

SUSPECTED_SERPENTINE_ORDER = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")
SCRAMBLED_ORDER = ("H", "A", "E", "C", "G", "F", "B", "J", "D", "I")


def _top_drill(fixture: Fixture, hole: Hole, ordinal: int) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=(
            f"TBH001_ORDER_{fixture.name}_{ordinal:02d}_"
            f"{hole.label}_{hole.tool}_X{_coord_token(hole.x)}_Y{_coord_token(hole.y)}"
        ),
        plane_name="Top",
        center_x=hole.x,
        center_y=hole.y,
        diameter=hole.diameter,
        target_depth=10.0,
        tool_resolution="Auto",
    )


def _coord_token(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def _top_drills(fixture: Fixture) -> tuple[DrillingSpec, ...]:
    return tuple(
        _top_drill(fixture, HOLES[label], ordinal)
        for ordinal, label in enumerate(fixture.hole_labels, start=1)
    )


def _line_ltr(fixture: Fixture) -> object:
    return build_line_milling_spec(
        line_x1=60.0,
        line_y1=24.0,
        line_x2=760.0,
        line_y2=24.0,
        line_feature_name=f"TBH001_ORDER_{fixture.name}_PREV_LINE_LTR_E001",
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


def _line_rtl(fixture: Fixture) -> object:
    return build_line_milling_spec(
        line_x1=760.0,
        line_y1=24.0,
        line_x2=60.0,
        line_y2=24.0,
        line_feature_name=f"TBH001_ORDER_{fixture.name}_PREV_LINE_RTL_E001",
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


def _profile(fixture: Fixture, *, winding: str) -> object:
    return build_squaring_milling_spec(
        winding=winding,
        feature_name=f"TBH001_ORDER_{fixture.name}_PREV_PROFILE_{winding}_E001",
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


def build_fixtures() -> tuple[Fixture, ...]:
    return (
        Fixture(
            name="Pieza_209",
            purpose="Top-only mixed 005/002/001 holes; PGMX source order is scrambled.",
            context="top_only",
            hole_labels=SCRAMBLED_ORDER,
        ),
        Fixture(
            name="Pieza_210",
            purpose="Top-only control with the same holes but reversed suspected order.",
            context="top_only",
            hole_labels=tuple(reversed(SUSPECTED_SERPENTINE_ORDER)),
        ),
        Fixture(
            name="Pieza_211",
            purpose="Line E001 left-to-right before the same scrambled top-drill block.",
            context="line_ltr_before_top",
            hole_labels=SCRAMBLED_ORDER,
        ),
        Fixture(
            name="Pieza_212",
            purpose="Line E001 right-to-left before the same scrambled top-drill block.",
            context="line_rtl_before_top",
            hole_labels=SCRAMBLED_ORDER,
        ),
        Fixture(
            name="Pieza_213",
            purpose="Clockwise E001 profile with Arc+Quote before the same scrambled top-drill block.",
            context="profile_clockwise_before_top",
            hole_labels=SCRAMBLED_ORDER,
        ),
        Fixture(
            name="Pieza_214",
            purpose="Counterclockwise E001 profile with Arc+Quote before the same scrambled top-drill block.",
            context="profile_counterclockwise_before_top",
            hole_labels=SCRAMBLED_ORDER,
        ),
    )


def _ordered_machinings(fixture: Fixture) -> tuple[object, ...]:
    top_drills = _top_drills(fixture)
    if fixture.context == "top_only":
        return top_drills
    if fixture.context == "line_ltr_before_top":
        return (_line_ltr(fixture), *top_drills)
    if fixture.context == "line_rtl_before_top":
        return (_line_rtl(fixture), *top_drills)
    if fixture.context == "profile_clockwise_before_top":
        return (_profile(fixture, winding="Clockwise"), *top_drills)
    if fixture.context == "profile_counterclockwise_before_top":
        return (_profile(fixture, winding="CounterClockwise"), *top_drills)
    raise ValueError(f"Unsupported fixture context: {fixture.context}")


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
                "id": f"P-TBH001-ORDER-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "context": fixture.context,
                "source_order_case": fixture.source_order_case,
                "source_order": _format_order(HOLES[label] for label in fixture.hole_labels),
                "suspected_maestro_order": _format_order(HOLES[label] for label in SUSPECTED_SERPENTINE_ORDER),
                "sha256": result.sha256,
                "purpose": fixture.purpose,
            }
        )

    manifest_path = output_dir / MANIFEST_NAME
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "context",
        "source_order_case",
        "source_order",
        "suspected_maestro_order",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def analyze_manifest(manifest_path: Path, output_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as manifest_file:
        rows = list(csv.DictReader(manifest_file))

    analysis_rows: list[dict[str, str]] = []
    for row in rows:
        pgmx_path = Path(row["pgmx_path"])
        iso_path = Path(row["expected_iso_path"])
        source_order = _top_order_from_pgmx(pgmx_path, candidate=False)
        candidate_order = _top_order_from_pgmx(pgmx_path, candidate=True)
        maestro_order = _top_order_from_iso(iso_path) if iso_path.exists() else []
        analysis_rows.append(
            {
                "name": row["name"],
                "context": row["context"],
                "iso_status": "available" if iso_path.exists() else "pending_iso",
                "source_order": _format_order(source_order),
                "candidate_order": _format_order(candidate_order),
                "maestro_order": _format_order(maestro_order),
                "maestro_matches_source": _bool_text(maestro_order == source_order) if maestro_order else "",
                "maestro_matches_candidate": _bool_text(maestro_order == candidate_order) if maestro_order else "",
                "maestro_matches_suspected": (
                    _bool_text(_format_order(maestro_order) == row["suspected_maestro_order"])
                    if maestro_order
                    else ""
                ),
                "pgmx_path": row["pgmx_path"],
                "expected_iso_path": row["expected_iso_path"],
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "context",
        "iso_status",
        "source_order",
        "candidate_order",
        "maestro_order",
        "maestro_matches_source",
        "maestro_matches_candidate",
        "maestro_matches_suspected",
        "pgmx_path",
        "expected_iso_path",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as analysis_file:
        writer = csv.DictWriter(analysis_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_rows)
    return analysis_rows


def _top_order_from_pgmx(path: Path, *, candidate: bool) -> list[Hole]:
    snapshot = read_pgmx_snapshot(path)
    steps: Iterable[PgmxResolvedWorkingStepSnapshot]
    if candidate:
        steps = _ordered_resolved_working_steps(snapshot)
    else:
        steps = snapshot.resolved_working_steps
    return [_hole_from_step(step) for step in steps if _resolved_step_family(step) == "top_drill"]


def _hole_from_step(step: PgmxResolvedWorkingStepSnapshot) -> Hole:
    if step.geometry is None or step.geometry.point is None:
        raise ValueError(f"Top-drill step without point geometry: {step.step.id}")
    x, y, _ = step.geometry.point
    tool = step.operation.tool_key.name if step.operation is not None and step.operation.tool_key is not None else ""
    label = _label_for(float(x), float(y), tool)
    return Hole(label, round(float(x), 6), round(float(y), 6), _diameter_for_tool(tool))


def _diameter_for_tool(tool: str) -> float:
    for diameter, expected_tool in TOOL_BY_DIAMETER.items():
        if expected_tool == tool:
            return diameter
    raise ValueError(f"Unsupported top-drill tool: {tool}")


def _top_order_from_iso(path: Path) -> list[Hole]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    order: list[Hole] = []
    current_tool = ""
    last_g0_xy: tuple[float, float] | None = None

    for raw_line in lines:
        line = raw_line.strip()
        tool_match = re.fullmatch(r"\?%ETK\[6\]=(\d+)", line)
        if tool_match:
            current_tool = f"{int(tool_match.group(1)):03d}"
            continue

        if line.startswith("G0 "):
            xy = _extract_xy(line)
            if xy is not None:
                last_g0_xy = xy
            continue

        if line == "?%ETK[7]=3" and last_g0_xy is not None and current_tool in {"001", "002", "005"}:
            x, y = last_g0_xy
            label = _label_for(x, y, current_tool)
            order.append(Hole(label, x, y, _diameter_for_tool(current_tool)))

    return order


def _extract_xy(line: str) -> tuple[float, float] | None:
    x_match = re.search(r"\bX(-?\d+(?:\.\d+)?)", line)
    y_match = re.search(r"\bY(-?\d+(?:\.\d+)?)", line)
    if not x_match or not y_match:
        return None
    return (round(float(x_match.group(1)), 6), round(float(y_match.group(1)), 6))


def _label_for(x: float, y: float, tool: str) -> str:
    for hole in HOLES.values():
        if round(hole.x, 6) == round(x, 6) and round(hole.y, 6) == round(y, 6) and hole.tool == tool:
            return hole.label
    return f"?{tool}@{x:g},{y:g}"


def _format_order(holes: Iterable[Hole]) -> str:
    return " -> ".join(hole.encoded for hole in holes)


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and analyze mixed top-drill ordering fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_209..214 fixtures.")
    parser.add_argument("--analyze", action="store_true", help="Analyze Maestro ISO order after generation.")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze an existing manifest.")
    parser.add_argument("--manifest", type=Path, help="Manifest CSV to analyze.")
    parser.add_argument("--analysis-output", type=Path, help="CSV path for the ordering analysis report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest or args.output_dir / MANIFEST_NAME
    analysis_output = args.analysis_output or manifest_path.with_name(ANALYSIS_NAME)

    if args.analyze_only:
        analysis_rows = analyze_manifest(manifest_path, analysis_output)
        _print_analysis_summary(analysis_rows, analysis_output)
        return 0

    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} mixed top-drill ordering fixtures in {args.output_dir}")
    for row in rows:
        print(f"{row['name']} {row['context']} {row['source_order_case']} {row['sha256']}")

    if args.analyze:
        analysis_rows = analyze_manifest(manifest_path, analysis_output)
        _print_analysis_summary(analysis_rows, analysis_output)
    return 0


def _print_analysis_summary(rows: Sequence[dict[str, str]], output_path: Path) -> None:
    available = sum(1 for row in rows if row["iso_status"] == "available")
    print(f"Analyzed {len(rows)} fixtures ({available} Maestro ISO available).")
    print(f"Analysis CSV: {output_path}")
    for row in rows:
        print(
            f"{row['name']} {row['iso_status']} "
            f"candidate={row['candidate_order']} maestro={row['maestro_order']}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
