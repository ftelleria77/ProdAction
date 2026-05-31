"""Vaciado V2 experimental model.

This package is intentionally independent from
`tools.pgmx_vaciado.trace_engine`. The old engine remains an oracle during the
rebuild, but V2 should model geometry, strategy, depth, and trace decisions as
separate concerns.
"""

from .depth import VaciadoDepth
from .adapters import from_pocket_milling_spec
from .geometry import BBox, PolylineContour, VaciadoGeometry
from .primitives import TracePrimitive2D, TracePrimitiveSequence2D
from .strategy import VaciadoStrategy
from .trace import OffsetFamily, RectangularNoIslandTracePlan, plan_rectangular_no_islands

__all__ = [
    "BBox",
    "OffsetFamily",
    "PolylineContour",
    "RectangularNoIslandTracePlan",
    "TracePrimitive2D",
    "TracePrimitiveSequence2D",
    "VaciadoDepth",
    "VaciadoGeometry",
    "VaciadoStrategy",
    "from_pocket_milling_spec",
    "plan_rectangular_no_islands",
]
