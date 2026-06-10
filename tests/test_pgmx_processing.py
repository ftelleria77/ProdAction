from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from core.model import Piece
from pgmx.processing import MachiningOperation, PieceDrawingData, _ordered_snapshot_features, build_piece_svg
from pgmx.snapshot import PgmxObjectRefSnapshot, PgmxWorkingStepSnapshot, PgmxWorkplanSnapshot


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

    def test_snapshot_drawing_uses_first_workplan_with_machining_features(self) -> None:
        first_feature = SimpleNamespace(id="F1", operation_refs=())
        second_feature = SimpleNamespace(id="F2", operation_refs=())
        first_step = PgmxWorkingStepSnapshot(
            id="S1",
            object_type="ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep",
            runtime_type="a:MachiningWorkingStep",
            name="Primera fase",
            description="",
            is_enabled=True,
            priority=0,
            manufacturing_feature_ref=PgmxObjectRefSnapshot("F1", "Feature"),
            operation_ref=None,
            reference="",
            x=None,
            y=None,
            workplan_index=1,
            workplan_id="WP1",
            workplan_name="Fase Inicial",
        )
        second_step = PgmxWorkingStepSnapshot(
            id="S2",
            object_type="ScmGroup.XCam.MachiningDataModel.ProjectModule.MachiningWorkingStep",
            runtime_type="a:MachiningWorkingStep",
            name="Segunda fase",
            description="",
            is_enabled=True,
            priority=0,
            manufacturing_feature_ref=PgmxObjectRefSnapshot("F2", "Feature"),
            operation_ref=None,
            reference="",
            x=None,
            y=None,
            workplan_index=2,
            workplan_id="WP2",
            workplan_name="Fase Final",
        )
        snapshot = SimpleNamespace(
            feature_by_id={"F1": first_feature, "F2": second_feature},
            operation_by_id={},
            features=(first_feature, second_feature),
            working_steps=(first_step, second_step),
            workplans=(
                _workplan("WP1", "Fase Inicial", (first_step,)),
                _workplan("WP2", "Fase Final", (second_step,)),
            ),
        )

        ordered = _ordered_snapshot_features(snapshot)

        self.assertEqual([entry[0].id for entry in ordered], ["F1"])


def _workplan(
    workplan_id: str,
    name: str,
    steps: tuple[PgmxWorkingStepSnapshot, ...],
) -> PgmxWorkplanSnapshot:
    return PgmxWorkplanSnapshot(
        index=1,
        id=workplan_id,
        object_type="ScmGroup.XCam.MachiningDataModel.ProjectModule.MainWorkplan",
        name=name,
        description="",
        is_enabled=True,
        priority=0,
        setup_id="Setup",
        setup_object_type="ScmGroup.XCam.MachiningDataModel.Setup",
        origin_x=0.0,
        origin_y=0.0,
        origin_z=0.0,
        working_steps=steps,
    )


if __name__ == "__main__":
    unittest.main()
