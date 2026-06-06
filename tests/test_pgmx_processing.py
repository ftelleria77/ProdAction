from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.model import Piece
from pgmx.processing import MachiningOperation, PieceDrawingData, build_piece_svg


class PgmxProcessingTests(unittest.TestCase):
    def test_side_projection_uses_operation_y_when_projected_y_is_missing(self) -> None:
        piece = Piece(id="P1", width=100, height=100, name="P1")
        drawing = PieceDrawingData(
            width=100,
            height=100,
            thickness=18,
            source_path=Path("P1.pgmx"),
            operations=[
                MachiningOperation(
                    op_type="drill",
                    x=20,
                    y=70,
                    diameter=8,
                    face="Left",
                    depth=20,
                    projected_x=None,
                    projected_y=None,
                )
            ],
            face_dimensions={"Top": (100, 100)},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "piece.svg"
            build_piece_svg(piece, drawing, output_path)
            svg = output_path.read_text(encoding="utf-8")

        self.assertIn(
            '<line x1="30.00" y1="100.00" x2="70.00" y2="100.00"',
            svg,
        )


if __name__ == "__main__":
    unittest.main()
