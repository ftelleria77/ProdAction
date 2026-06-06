from __future__ import annotations

import unittest
from pathlib import Path

from core.en_juego_synthesis import (
    EnJuegoPgmxResult,
    _ResolvedInstance,
    _layout_transform,
    _parse_quantity,
    _safe_bool,
    _safe_float,
    _validate_division_gap,
    _validate_no_piece_overlaps,
)
from core.en_juego_transform import EnJuegoTransform


def _instance(
    key: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> _ResolvedInstance:
    return _ResolvedInstance(
        instance_key=key,
        piece_id=key,
        copy_index=1,
        title_text=key,
        piece_row={},
        source_path=Path(f"{key}.pgmx"),
        snapshot=None,  # type: ignore[arg-type]
        transform=EnJuegoTransform(x, y),
        footprint_x=x,
        footprint_y=y,
        footprint_width=width,
        footprint_height=height,
    )


class EnJuegoSynthesisTests(unittest.TestCase):
    def test_safe_helpers_accept_common_saved_values(self) -> None:
        self.assertEqual(_safe_float("18,5"), 18.5)
        self.assertTrue(_safe_bool("si"))
        self.assertTrue(_safe_bool("sí"))
        self.assertFalse(_safe_bool("off", default=True))
        self.assertEqual(_parse_quantity({"quantity": "2,0"}), 2)
        self.assertEqual(_parse_quantity({"quantity": "-1"}), 1)

    def test_layout_transform_reads_saved_layout_v2_values(self) -> None:
        transform = _layout_transform({"x_mm": "10,5", "y_mm": "20", "rotation": "90"})

        self.assertIsNotNone(transform)
        assert transform is not None
        self.assertEqual(transform.origin_x_mm, 10.5)
        self.assertEqual(transform.origin_y_mm, 20.0)
        self.assertEqual(transform.rotation_deg, 90.0)

    def test_validate_no_piece_overlaps_allows_touching_and_rejects_overlap(self) -> None:
        _validate_no_piece_overlaps(
            (
                _instance("A", x=0, y=0, width=100, height=50),
                _instance("B", x=100, y=0, width=100, height=50),
            )
        )

        with self.assertRaises(ValueError) as context:
            _validate_no_piece_overlaps(
                (
                    _instance("A", x=0, y=0, width=100, height=50),
                    _instance("B", x=99, y=0, width=100, height=50),
                )
            )

        self.assertIn("solapes entre piezas", str(context.exception))

    def test_validate_division_gap_requires_tool_width(self) -> None:
        _validate_division_gap(10, 10, "division")

        with self.assertRaises(ValueError) as context:
            _validate_division_gap(9.8, 10, "division")

        self.assertIn("herramienta 10 mm", str(context.exception))

    def test_result_contract_is_stable(self) -> None:
        result = EnJuegoPgmxResult(
            output_path=Path("out.pgmx"),
            piece_name="Modulo_EnJuego",
            board_width=100,
            board_height=50,
            board_thickness=18,
            instance_count=2,
            contour_count=1,
            fallback_contour_count=0,
        )

        self.assertEqual(result.piece_name, "Modulo_EnJuego")
        self.assertEqual(result.instance_count, 2)


if __name__ == "__main__":
    unittest.main()
