"""Fixtures for B-BH-002: top-drill ordering — 4-hole exception and direction continuation.

Two open questions drive this batch:

Q1 — 4-hole mixed-depth exception (TabiqueF6):
  ``_top_drill_auto_block_has_single_tool_mixed_depth`` fires for Haeublein's
  TabiqueF6 because the 4 holes have two different target_depth values (10 and 15).
  This routes the block to start_at_max_x_min_y, giving order D→C→A→B, but Maestro
  starts at A (origin-nearest).  Fixtures Pieza_216 (mixed depth) and Pieza_217
  (same depth) share identical XY positions to isolate the depth variable.

Q2 — direction continuation vs. X-ascending tiebreaker (Lat_Der mod 11):
  Nearest-neighbor with X-ascending tiebreaker picks the lower-X option when two
  remaining holes are equidistant.  Maestro picks the option that continues the
  direction of travel (increasing X in all observed cases).  Pieza_215 creates a
  controlled equidistant scenario where the difference between the two rules is one
  hole.  Pieza_218 strips it to the minimal 3-hole form.

Fixture map
-----------
Pieza_215  5 holes, D=5, same depth. Right-going sequence then equidistant split.
           Current code order : A→B→C→E→D   (X tiebreaker picks E at same dist as D)
           Hyp. Maestro order : A→B→C→D→E   (direction continuation: D is rightward)

Pieza_216  4 holes, D=5, MIXED depth (10 and 15). TabiqueF6 geometry.
           Exception fires  : D(507,32)→C(507,68)→A(237.5,60)→B(237.5,373)
           Hyp. origin-start: A(237.5,60)→D(507,32)→C(507,68)→B(237.5,373)

Pieza_217  Same XY as Pieza_216 but SAME depth=12 (control, no exception).
           Expected Maestro  : A(237.5,60)→D(507,32)→C(507,68)→B(237.5,373)
           Deviation reveals whether mixed depth alone changes Maestro behavior.

Pieza_218  3 holes, D=5, same depth. Minimal equidistant-from-start test.
           Current code order : A→B→C   (X tiebreaker picks B.x=50 < C.x=200)
           Hyp. Maestro order : A→C→B   (C is in the direction of origin→A travel)
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso_state_synthesis.pgmx_source import (  # noqa: E402
    _ordered_resolved_working_steps,
    _resolved_step_family,
)
from pgmx.snapshot import (  # noqa: E402
    PgmxResolvedWorkingStepSnapshot,
    read_pgmx_snapshot,
)
from pgmx.synthesis import (  # noqa: E402
    DrillingSpec,
    build_drilling_spec,
    build_synthesis_request,
    synthesize_request,
)

DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")
EXPECTED_ISO_DIR = Path(r"P:\USBMIX\ProdAction\ISO")
MANIFEST_NAME = "Pieza_215_218_BBH002_top_order_manifest.csv"
ANALYSIS_NAME = "Pieza_215_218_BBH002_top_order_analysis.csv"


@dataclass(frozen=True)
class Hole:
    label: str
    x: float
    y: float
    diameter: float
    target_depth: float

    @property
    def encoded(self) -> str:
        return f"{self.label}@({self.x:g},{self.y:g})d{self.target_depth:g}"


@dataclass(frozen=True)
class Fixture:
    name: str
    purpose: str
    question: str
    holes: tuple[Hole, ...]
    source_order_labels: tuple[str, ...]
    expected_candidate_order: tuple[str, ...]
    expected_maestro_order: tuple[str, ...]
    length: float = 820.0
    width: float = 620.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"


def _hole_map(holes: Iterable[Hole]) -> dict[str, Hole]:
    return {h.label: h for h in holes}


# ---------------------------------------------------------------------------
# Pieza_215 — direction continuation: 5 holes, equidistant split at C
# A(50,50) → B(200,50) → C(350,50), then D(500,50) and E(350,200) equidistant
# dist C→D = 150, dist C→E = sqrt(0+150²) = 150
# X-tiebreaker: C→E (E.x=350 < D.x=500)   hyp Maestro: C→D (continuing rightward)
# ---------------------------------------------------------------------------
_P215_HOLES: tuple[Hole, ...] = (
    Hole("A", 50.0, 50.0, 5.0, 12.0),
    Hole("B", 200.0, 50.0, 5.0, 12.0),
    Hole("C", 350.0, 50.0, 5.0, 12.0),
    Hole("D", 500.0, 50.0, 5.0, 12.0),
    Hole("E", 350.0, 200.0, 5.0, 12.0),
)

# ---------------------------------------------------------------------------
# Pieza_216 — TabiqueF6 geometry, MIXED depth (exception fires)
# D=5, depth 10 for A,B and depth 15 for C,D
# Exception→ max X/min Y start = D(507,32)
# Origin-start hypothesis = A(237.5,60)
# ---------------------------------------------------------------------------
_P216_HOLES: tuple[Hole, ...] = (
    Hole("A", 237.5, 60.0, 5.0, 10.0),
    Hole("B", 237.5, 373.0, 5.0, 10.0),
    Hole("C", 507.0, 68.0, 5.0, 15.0),
    Hole("D", 507.0, 32.0, 5.0, 15.0),
)

# ---------------------------------------------------------------------------
# Pieza_217 — same XY as Pieza_216 but same depth=12 (no exception fires)
# Control: isolates whether mixed depth changes Maestro behavior
# Both current-code and hypothesis expect origin-start: A(237.5,60)
# ---------------------------------------------------------------------------
_P217_HOLES: tuple[Hole, ...] = (
    Hole("A", 237.5, 60.0, 5.0, 12.0),
    Hole("B", 237.5, 373.0, 5.0, 12.0),
    Hole("C", 507.0, 68.0, 5.0, 12.0),
    Hole("D", 507.0, 32.0, 5.0, 12.0),
)

# ---------------------------------------------------------------------------
# Pieza_218 — minimal 3-hole equidistant test
# A(50,5) nearest to origin; B(50,155) and C(200,5) equidistant from A at dist=150
# X-tiebreaker: A→B (B.x=50 < C.x=200)   hyp: A→C (C is in origin→A direction)
# ---------------------------------------------------------------------------
_P218_HOLES: tuple[Hole, ...] = (
    Hole("A", 50.0, 5.0, 5.0, 12.0),
    Hole("B", 50.0, 155.0, 5.0, 12.0),
    Hole("C", 200.0, 5.0, 5.0, 12.0),
)


def _origin_nearest_neighbor_order(holes: tuple[Hole, ...]) -> tuple[str, ...]:
    """Nearest-neighbor traversal starting at the hole closest to (0,0)."""
    remaining = list(holes)
    start = min(remaining, key=lambda h: math.hypot(h.x, h.y))
    remaining.remove(start)
    ordered = [start]
    while remaining:
        prev = ordered[-1]
        nxt = min(remaining, key=lambda h: (math.hypot(h.x - prev.x, h.y - prev.y), h.x, h.y))
        remaining.remove(nxt)
        ordered.append(nxt)
    return tuple(h.label for h in ordered)


def _max_x_min_y_nearest_neighbor_order(holes: tuple[Hole, ...]) -> tuple[str, ...]:
    """Nearest-neighbor starting at max-X / min-Y hole."""
    remaining = list(holes)
    start = min(remaining, key=lambda h: (-h.x, h.y))
    remaining.remove(start)
    ordered = [start]
    while remaining:
        prev = ordered[-1]
        nxt = min(remaining, key=lambda h: (math.hypot(h.x - prev.x, h.y - prev.y), h.x, h.y))
        remaining.remove(nxt)
        ordered.append(nxt)
    return tuple(h.label for h in ordered)


def build_fixtures() -> tuple[Fixture, ...]:
    origin_p216 = _origin_nearest_neighbor_order(_P216_HOLES)
    exception_p216 = _max_x_min_y_nearest_neighbor_order(_P216_HOLES)
    origin_p218 = _origin_nearest_neighbor_order(_P218_HOLES)

    return (
        Fixture(
            name="Pieza_215",
            purpose=(
                "5 holes D=5 same depth; right-going A→B→C, then equidistant D(500,50) and E(350,200). "
                "X-tiebreaker picks E; direction-continuation picks D."
            ),
            question="Q2-direction-continuation",
            holes=_P215_HOLES,
            source_order_labels=("E", "C", "A", "D", "B"),
            expected_candidate_order=("A", "B", "C", "E", "D"),
            expected_maestro_order=("A", "B", "C", "D", "E"),
        ),
        Fixture(
            name="Pieza_216",
            purpose=(
                "4 holes D=5 mixed depth 10/15 — TabiqueF6 geometry clone. "
                "4-hole exception fires → max-X/min-Y start D(507,32). "
                "Hypothesis: Maestro uses origin-start A(237.5,60)."
            ),
            question="Q1-four-hole-exception",
            holes=_P216_HOLES,
            source_order_labels=("C", "A", "D", "B"),
            expected_candidate_order=list(exception_p216),
            expected_maestro_order=list(origin_p216),
            length=704.0,
            width=413.0,
        ),
        Fixture(
            name="Pieza_217",
            purpose=(
                "4 holes D=5 same depth=12 — same XY as Pieza_216 (TabiqueF6), no exception. "
                "Control: verifies origin-start for same-depth 4-hole block."
            ),
            question="Q1-four-hole-control",
            holes=_P217_HOLES,
            source_order_labels=("C", "A", "D", "B"),
            expected_candidate_order=list(origin_p216),
            expected_maestro_order=list(origin_p216),
            length=704.0,
            width=413.0,
        ),
        Fixture(
            name="Pieza_218",
            purpose=(
                "3 holes D=5 same depth. A(50,5) is nearest origin; B(50,155) and C(200,5) "
                "are equidistant from A. X-tiebreaker→A→B→C; direction-continuation→A→C→B."
            ),
            question="Q2-direction-continuation-minimal",
            holes=_P218_HOLES,
            source_order_labels=("B", "C", "A"),
            expected_candidate_order=list(origin_p218),
            expected_maestro_order=("A", "C", "B"),
        ),
    )


def _top_drill_spec(fixture: Fixture, hole: Hole, ordinal: int) -> DrillingSpec:
    return build_drilling_spec(
        feature_name=(
            f"BBH002_ORDER_{fixture.name}_{ordinal:02d}_{hole.label}"
            f"_X{_coord_token(hole.x)}_Y{_coord_token(hole.y)}"
        ),
        plane_name="Top",
        center_x=hole.x,
        center_y=hole.y,
        diameter=hole.diameter,
        target_depth=hole.target_depth,
        tool_resolution="Auto",
    )


def _coord_token(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def generate(output_dir: Path, *, force: bool = False) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
        if output_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing fixture: {output_path}")

        hole_map = _hole_map(fixture.holes)
        ordered_holes = [hole_map[label] for label in fixture.source_order_labels]
        specs = tuple(
            _top_drill_spec(fixture, hole, ordinal)
            for ordinal, hole in enumerate(ordered_holes, start=1)
        )
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
            ordered_machinings=specs,
        )
        result = synthesize_request(request)
        expected_iso_path = EXPECTED_ISO_DIR / f"{fixture.name.lower()}.iso"
        rows.append(
            {
                "id": f"P-BBH002-ORDER-{fixture.name[-3:]}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "question": fixture.question,
                "source_order": _format_labels(fixture.source_order_labels),
                "expected_candidate_order": _format_labels(fixture.expected_candidate_order),
                "expected_maestro_order": _format_labels(fixture.expected_maestro_order),
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
        "question",
        "source_order",
        "expected_candidate_order",
        "expected_maestro_order",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def analyze_manifest(manifest_path: Path, output_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    analysis_rows: list[dict[str, str]] = []
    for row in rows:
        pgmx_path = Path(row["pgmx_path"])
        iso_path = Path(row["expected_iso_path"])
        candidate_order = _top_order_from_pgmx(pgmx_path, candidate=True)
        maestro_order = _top_order_from_iso(iso_path) if iso_path.exists() else []
        source_order = _top_order_from_pgmx(pgmx_path, candidate=False)
        analysis_rows.append(
            {
                "name": row["name"],
                "question": row["question"],
                "iso_status": "available" if iso_path.exists() else "pending_iso",
                "source_order": _format_labels(h.label for h in source_order),
                "candidate_order": _format_labels(h.label for h in candidate_order),
                "maestro_order": _format_labels(h.label for h in maestro_order),
                "candidate_matches_expected": _bool_text(
                    _format_labels(h.label for h in candidate_order)
                    == row["expected_candidate_order"]
                ),
                "maestro_matches_expected": (
                    _bool_text(
                        _format_labels(h.label for h in maestro_order)
                        == row["expected_maestro_order"]
                    )
                    if maestro_order
                    else ""
                ),
                "maestro_matches_candidate": (
                    _bool_text(maestro_order == candidate_order) if maestro_order else ""
                ),
                "pgmx_path": row["pgmx_path"],
                "expected_iso_path": row["expected_iso_path"],
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "question",
        "iso_status",
        "source_order",
        "candidate_order",
        "maestro_order",
        "candidate_matches_expected",
        "maestro_matches_expected",
        "maestro_matches_candidate",
        "pgmx_path",
        "expected_iso_path",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_rows)
    return analysis_rows


def _top_order_from_pgmx(path: Path, *, candidate: bool) -> list[Hole]:
    snapshot = read_pgmx_snapshot(path)
    if candidate:
        steps = _ordered_resolved_working_steps(snapshot)
    else:
        steps = snapshot.resolved_working_steps
    return [_hole_from_step(step) for step in steps if _resolved_step_family(step) == "top_drill"]


def _hole_from_step(step: PgmxResolvedWorkingStepSnapshot) -> Hole:
    if step.geometry is None or step.geometry.point is None:
        raise ValueError(f"Top-drill step without point geometry: {step.step.id}")
    x, y, _ = step.geometry.point
    feature_name = step.feature.name if step.feature else ""
    label = _label_from_feature_name(feature_name)
    diameter = 5.0
    if step.feature and step.feature.diameter is not None:
        diameter = float(step.feature.diameter)
    return Hole(label, round(float(x), 6), round(float(y), 6), diameter, 0.0)


def _label_from_feature_name(name: str) -> str:
    """Extract single-letter label from BBH002_ORDER_PiezaXXX_NN_LABEL_... names."""
    import re
    m = re.search(r"BBH002_ORDER_Pieza_\d{3}_\d{2}_([A-Z])_", name)
    if m:
        return m.group(1)
    return f"?({name})"


def _top_order_from_iso(path: Path) -> list[Hole]:
    """Extract hole visit order from Maestro ISO output."""
    import re
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    order: list[Hole] = []
    last_g0_xy: tuple[float, float] | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("G0 "):
            m_x = re.search(r"\bX(-?\d+(?:\.\d+)?)", line)
            m_y = re.search(r"\bY(-?\d+(?:\.\d+)?)", line)
            if m_x and m_y:
                last_g0_xy = (round(float(m_x.group(1)), 6), round(float(m_y.group(1)), 6))
            continue
        if line == "?%ETK[7]=3" and last_g0_xy is not None:
            x, y = last_g0_xy
            order.append(Hole(f"({x:g},{y:g})", x, y, 5.0, 0.0))
            last_g0_xy = None

    return order


def _format_labels(labels: Iterable[str]) -> str:
    return " → ".join(labels)


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate BBH002 top-drill ordering fixtures (Pieza_215..218)."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing fixtures.")
    parser.add_argument("--analyze", action="store_true", help="Analyze after generation.")
    parser.add_argument("--analyze-only", action="store_true", help="Analyze only (no generate).")
    parser.add_argument("--manifest", type=Path, help="Manifest CSV for analysis.")
    parser.add_argument("--analysis-output", type=Path, help="CSV path for analysis report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest or args.output_dir / MANIFEST_NAME
    analysis_output = args.analysis_output or manifest_path.with_name(ANALYSIS_NAME)

    if args.analyze_only:
        rows = analyze_manifest(manifest_path, analysis_output)
        _print_summary(rows, analysis_output)
        return 0

    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} BBH002 top-drill fixtures in {args.output_dir}")
    for row in rows:
        print(f"  {row['name']}  {row['question']}  sha256={row['sha256']}")

    if args.analyze:
        arows = analyze_manifest(manifest_path, analysis_output)
        _print_summary(arows, analysis_output)
    return 0


def _print_summary(rows: Sequence[dict[str, str]], output_path: Path) -> None:
    available = sum(1 for r in rows if r["iso_status"] == "available")
    print(f"Analyzed {len(rows)} fixtures ({available} Maestro ISO available). {output_path}")
    for row in rows:
        print(
            f"  {row['name']} [{row['question']}] "
            f"candidate={row['candidate_order']}  maestro={row['maestro_order']}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
