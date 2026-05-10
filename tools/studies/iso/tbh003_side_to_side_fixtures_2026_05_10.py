"""Generate PGMX fixtures for T-BH-003 side-drill to side-drill study.

The generated files extend the historical ``Pieza_*.pgmx`` sequence with one
fixture for each directed side-face variant. They are meant to be postprocessed
manually in Maestro/CNC before the ISO transition rules are closed.
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
    build_synthesis_request,
    synthesize_request,
)


DEFAULT_OUTPUT_DIR = Path(r"S:\Maestro\Projects\ProdAction\ISO")
EXPECTED_ISO_DIR = Path(r"P:\USBMIX\ProdAction\ISO")

FACES = ("Front", "Right", "Back", "Left")
FACE_LABELS = {
    "Front": "anterior/delantera/frontal",
    "Right": "lateral derecha",
    "Back": "posterior/trasera",
    "Left": "lateral izquierda",
}


@dataclass(frozen=True)
class Fixture:
    index: int
    name: str
    from_face: str
    to_face: str
    length: float = 420.0
    width: float = 280.0
    depth: float = 18.0
    origin_x: float = 5.0
    origin_y: float = 5.0
    origin_z: float = 25.0
    execution_fields: str = "HG"

    @property
    def transition(self) -> str:
        return f"{self.from_face}->{self.to_face}"

    @property
    def variant_kind(self) -> str:
        return "same_face" if self.from_face == self.to_face else "cross_face"


def _face_span(fixture: Fixture, face: str) -> float:
    if face in {"Front", "Back"}:
        return fixture.length
    if face in {"Right", "Left"}:
        return fixture.width
    raise ValueError(f"Unsupported side face: {face}")


def _face_position(fixture: Fixture, face: str, fraction: float) -> float:
    return round(_face_span(fixture, face) * fraction, 3)


def _side_drill(fixture: Fixture, face: str, ordinal: int) -> DrillingSpec:
    fraction = 0.35 if ordinal == 1 else 0.65
    return build_drilling_spec(
        feature_name=f"TBH003_{fixture.index:02d}_{ordinal}_{face.upper()}_D8",
        plane_name=face,
        center_x=_face_position(fixture, face, fraction),
        center_y=fixture.depth / 2.0,
        diameter=8.0,
        target_depth=28.0,
        tool_resolution="Auto",
    )


def build_fixtures() -> tuple[Fixture, ...]:
    variants: list[tuple[str, str]] = []
    variants.extend((face, face) for face in FACES)
    variants.extend(
        (from_face, to_face)
        for from_face in FACES
        for to_face in FACES
        if from_face != to_face
    )
    return tuple(
        Fixture(index=index, name=f"Pieza_{102 + index:03d}", from_face=from_face, to_face=to_face)
        for index, (from_face, to_face) in enumerate(variants, start=1)
    )


def generate(output_dir: Path, *, force: bool = False) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for fixture in build_fixtures():
        output_path = output_dir / f"{fixture.name}.pgmx"
        if output_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing fixture: {output_path}")

        drillings = (
            _side_drill(fixture, fixture.from_face, 1),
            _side_drill(fixture, fixture.to_face, 2),
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
            ordered_machinings=drillings,
        )
        result = synthesize_request(request)
        expected_iso_path = EXPECTED_ISO_DIR / f"{fixture.name.lower()}.iso"
        rows.append(
            {
                "id": f"P-TBH003-{fixture.index:03d}",
                "name": fixture.name,
                "pgmx_path": str(result.output_path),
                "expected_iso_path": str(expected_iso_path),
                "transition": fixture.transition,
                "from_face": fixture.from_face,
                "to_face": fixture.to_face,
                "from_face_label": FACE_LABELS[fixture.from_face],
                "to_face_label": FACE_LABELS[fixture.to_face],
                "variant_kind": fixture.variant_kind,
                "drillings": str(len(drillings)),
                "diameter": "8",
                "target_depth": "28",
                "sha256": result.sha256,
                "purpose": (
                    f"T-BH-003: isolate side drill transition {fixture.transition} "
                    "with two consecutive D8 horizontal drillings."
                ),
            }
        )

    manifest_path = output_dir / "Pieza_103_118_TBH003_manifest.csv"
    fieldnames = [
        "id",
        "name",
        "pgmx_path",
        "expected_iso_path",
        "transition",
        "from_face",
        "to_face",
        "from_face_label",
        "to_face_label",
        "variant_kind",
        "drillings",
        "diameter",
        "target_depth",
        "sha256",
        "purpose",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T-BH-003 side-to-side PGMX fixtures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="Overwrite existing Pieza_103..118 fixtures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = generate(args.output_dir, force=args.force)
    print(f"Generated {len(rows)} T-BH-003 fixtures in {args.output_dir}")
    for row in rows:
        print(f"{row['name']} {row['transition']} {row['variant_kind']} {row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
