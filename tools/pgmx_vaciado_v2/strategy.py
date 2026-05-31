from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VaciadoStrategy:
    tool_width: float
    overlap: float = 0.5
    allowance_side: float = 0.0
    rotation_direction: str = "CounterClockwise"
    inside_to_outside: bool = True
    stroke_connection_strategy: str = "LiftShiftPlunge"
    is_helic_strategy: bool = False

    def __post_init__(self) -> None:
        if self.tool_width <= 0.0:
            raise ValueError("tool_width must be positive.")
        if not 0.0 <= self.overlap < 1.0:
            raise ValueError("overlap must be in the range [0, 1).")
        if self.effective_offset < -1e-9:
            raise ValueError("tool radius + allowance_side must not be negative.")
        if self.rotation_direction not in {"Clockwise", "CounterClockwise"}:
            raise ValueError("rotation_direction must be Clockwise or CounterClockwise.")
        if self.stroke_connection_strategy not in {"LiftShiftPlunge", "Straghtline"}:
            raise ValueError("unsupported stroke_connection_strategy.")

    @property
    def tool_radius(self) -> float:
        return self.tool_width / 2.0

    @property
    def effective_offset(self) -> float:
        return self.tool_radius + self.allowance_side

    @property
    def radial_step(self) -> float:
        return self.tool_width * (1.0 - self.overlap)
