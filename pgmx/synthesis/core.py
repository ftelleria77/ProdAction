"""Compatibility facade for the modular PGMX synthesis package.

Production code should import the concrete modules under `pgmx.synthesis`.
This module keeps the historical `pgmx.synthesis.core` surface available for
legacy imports and tests.
"""

from __future__ import annotations

from .common.depth import *  # noqa: F401,F403
from .common.geometry import *  # noqa: F401,F403
from .common.hydration import *  # noqa: F401,F403
from .common.leads import *  # noqa: F401,F403
from .common.piece import *  # noqa: F401,F403
from .common.program import *  # noqa: F401,F403
from .common.reader import *  # noqa: F401,F403
from .common.strategy import *  # noqa: F401,F403
from .common.tools import *  # noqa: F401,F403
from .common.xml import *  # noqa: F401,F403
from .drilling.pattern import *  # noqa: F401,F403
from .drilling.single import *  # noqa: F401,F403
from .milling._common import *  # noqa: F401,F403
from .milling.circle import *  # noqa: F401,F403
from .milling.line import *  # noqa: F401,F403
from .milling.pocket import *  # noqa: F401,F403
from .milling.arc import *  # noqa: F401,F403
from .milling.polyline import *  # noqa: F401,F403
from .milling.channel import *  # noqa: F401,F403
from .milling.contour import *  # noqa: F401,F403

register_pgmx_namespaces()

__all__ = [
    "DEFAULT_BASELINE_DIR",
    "DEFAULT_BASELINE_XML_PATH",
    "SYNTHESIZER_VERSION",
    "PgmxState",
    "ApproachSpec",
    "RetractSpec",
    "MillingDepthSpec",
    "UnidirectionalMillingStrategySpec",
    "BidirectionalMillingStrategySpec",
    "HelicalMillingStrategySpec",
    "ContourParallelMillingStrategySpec",
    "GeometryPrimitiveSpec",
    "GeometryProfileSpec",
    "PocketBossRouteSeedSpec",
    "LineSpec",
    "ChannelSpec",
    "ArcSpec",
    "PolylineSpec",
    "PolylineSegment",
    "PolylineSpec",
    "CircleSpec",
    "ContourSpec",
    "PocketSpec",
    "DrillSpec",
    "DrillPatternSpec",
    "MachiningSpec",
    "MachineOperationSpec",
    "WorkplanSpec",
    "XnSpec",
    "XmsgSpec",
    "IsoSpec",
    "ParkSpec",
    "DrawingSpec",
    "ParametricVariableSpec",
    "PieceSpec",
    "PgmxSynthesisRequest",
    "PgmxSynthesisResult",
    "build_approach_spec",
    "build_retract_spec",
    "build_milling_depth_spec",
    "build_unidirectional_milling_strategy_spec",
    "build_bidirectional_milling_strategy_spec",
    "build_helical_milling_strategy_spec",
    "build_contour_parallel_milling_strategy_spec",
    "build_line_geometry_primitive",
    "build_arc_geometry_primitive",
    "build_point_geometry_profile",
    "build_line_geometry_profile",
    "build_circle_geometry_profile",
    "build_composite_geometry_profile",
    "build_compensated_toolpath_profile",
    "build_pocket_boss_route_seed_spec",
    "build_line_spec",
    "build_channel_spec",
    "build_arc_spec",
    "build_polyline_spec",
    "build_polyline_spec",
    "build_circle_spec",
    "build_contour_spec",
    "build_pocket_spec",
    "build_drill_spec",
    "build_drill_pattern_spec",
    "build_workplan_spec",
    "build_xn_spec",
    "build_xmsg_spec",
    "build_iso_spec",
    "build_park_spec",
    "build_drawing_spec",
    "build_parametric_variable_spec",
    "build_piece_spec",
    "read_pgmx_state",
    "read_pgmx_geometries",
    "build_synthesis_request",
    "_append_hydrated_machining_to_workplan",
    "_append_workplan_machinings",
    "synthesize_request",
    "synthesize_pgmx",
    "split_pgmx_pieces",
    "merge_pgmx_pieces",
]


from .cli import main  # noqa: E402
