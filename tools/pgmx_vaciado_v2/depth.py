from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VaciadoDepth:
    target_depth: float
    allow_multiple_passes: bool = False
    axial_cutting_depth: float = 0.0
    axial_finish_cutting_depth: float = 0.0

    def __post_init__(self) -> None:
        if self.target_depth <= 0.0:
            raise ValueError("target_depth must be positive.")
        if self.axial_cutting_depth < 0.0:
            raise ValueError("axial_cutting_depth must not be negative.")
        if self.axial_finish_cutting_depth < 0.0:
            raise ValueError("axial_finish_cutting_depth must not be negative.")
