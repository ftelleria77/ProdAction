import unittest

from core import nesting, nesting_guillotine_sections
from core.model import Piece
from core.nesting_model import (
    CUT_OPTIMIZATION_LONGITUDINAL,
    CUT_OPTIMIZATION_NONE,
    CUT_OPTIMIZATION_TRANSVERSAL,
    CutPiece,
    SectionCandidate,
    SectionSelection,
)


def _cut_piece(label: str, width: float, height: float, *, allow_rotate: bool = False) -> CutPiece:
    return CutPiece(
        piece=Piece(id=label, width=width, height=height, thickness=18),
        label=label,
        width=width,
        height=height,
        thickness=18,
        color="Blanco",
        allow_rotate=allow_rotate,
    )


class NestingGuillotineSectionsTests(unittest.TestCase):
    def test_nesting_keeps_guillotine_section_helper_compatibility_facade(self) -> None:
        self.assertIs(nesting._section_dimensions, nesting_guillotine_sections.section_dimensions)
        self.assertIs(nesting._section_build_score, nesting_guillotine_sections.section_build_score)
        self.assertIs(nesting._section_similarity_metrics, nesting_guillotine_sections.section_similarity_metrics)
        self.assertIs(nesting._build_section_candidate, nesting_guillotine_sections.build_section_candidate)
        self.assertIs(nesting._build_section_placements, nesting_guillotine_sections.build_section_placements)
        self.assertIs(nesting._build_main_cut_guides, nesting_guillotine_sections.build_main_cut_guides)

    def test_section_dimensions_follow_requested_optimization_axis(self) -> None:
        self.assertEqual(nesting_guillotine_sections.section_dimensions(100, 40, CUT_OPTIMIZATION_LONGITUDINAL), (100, 40))
        self.assertEqual(nesting_guillotine_sections.section_dimensions(100, 40, CUT_OPTIMIZATION_TRANSVERSAL), (40, 100))
        self.assertEqual(nesting_guillotine_sections.section_axes_for_mode(CUT_OPTIMIZATION_NONE), (0.0, 1.0))

    def test_build_section_candidate_packs_compatible_pieces_by_secondary_span(self) -> None:
        wide = _cut_piece("wide", 40, 20)
        narrow = _cut_piece("narrow", 40, 10)

        candidate = nesting_guillotine_sections.build_section_candidate(
            [wide, narrow],
            section_size=40,
            primary_remaining=100,
            secondary_capacity=40,
            piece_spacing=5,
            section_kerf=5,
            grain="",
            optimization_mode=CUT_OPTIMIZATION_LONGITUDINAL,
        )

        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate.occupied_primary, 45)
        self.assertEqual(candidate.used_secondary, 35)
        self.assertEqual(candidate.used_area, 1200)
        self.assertEqual([selection.cut_piece.label for selection in candidate.selections], ["wide", "narrow"])

    def test_build_section_placements_uses_primary_offset_and_spacing(self) -> None:
        first = _cut_piece("first", 40, 20)
        second = _cut_piece("second", 40, 10)
        candidate = SectionCandidate(
            section_size=40,
            occupied_primary=45,
            used_secondary=35,
            used_area=1200,
            selections=[
                SectionSelection(0, first, 40, 20, False, 40, 20, 800),
                SectionSelection(1, second, 40, 10, False, 40, 10, 400),
            ],
        )

        placements = nesting_guillotine_sections.build_section_placements(
            candidate,
            primary_offset=7,
            optimization_mode=CUT_OPTIMIZATION_LONGITUDINAL,
            piece_spacing=5,
        )

        self.assertEqual(
            [(placement.x, placement.y, placement.width, placement.height) for placement in placements],
            [(7, 0.0, 40, 20), (7, 25.0, 40, 10)],
        )

    def test_build_main_cut_guides_omits_board_edge_cut(self) -> None:
        sections = [
            SectionCandidate(section_size=40, occupied_primary=45, used_secondary=20, used_area=800),
            SectionCandidate(section_size=55, occupied_primary=55, used_secondary=20, used_area=1100),
        ]

        positions, orientation = nesting_guillotine_sections.build_main_cut_guides(
            sections,
            CUT_OPTIMIZATION_LONGITUDINAL,
            board_primary_capacity=100,
        )

        self.assertEqual(positions, [40.0])
        self.assertEqual(orientation, "vertical")


if __name__ == "__main__":
    unittest.main()
