"""Internal state model for the ISO state synthesis experiment."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Optional


class IsoStateSynthesisError(RuntimeError):
    """Base error raised by the state-based ISO synthesis experiment."""


@dataclass(frozen=True)
class IsoStateWarning:
    """Non-blocking issue found while building a state plan."""

    code: str
    message: str
    source: str = ""


@dataclass(frozen=True)
class EvidenceSource:
    """Where a state value or trace value came from."""

    kind: str
    path: str
    field: str = ""
    note: str = ""


@dataclass(frozen=True)
class StateValue:
    """One observed or inferred value in a named state layer."""

    layer: str
    key: str
    value: Any
    source: EvidenceSource
    confidence: str = "observed"
    note: str = ""
    required: bool = False

    @property
    def address(self) -> str:
        return f"{self.layer}.{self.key}"


@dataclass(frozen=True)
class StateVector:
    """Small immutable collection of state values."""

    values: tuple[StateValue, ...] = ()

    def as_map(self) -> dict[str, StateValue]:
        return {value.address: value for value in self.values}

    def by_layer(self, layer: str) -> tuple[StateValue, ...]:
        return tuple(value for value in self.values if value.layer == layer)

    def find(self, layer: str, key: str) -> Optional[StateValue]:
        for value in self.values:
            if value.layer == layer and value.key == key:
                return value
        return None

    def get(self, layer: str, key: str, default: Any = None) -> Any:
        value = self.find(layer, key)
        return value.value if value is not None else default

    def extend(self, *values: StateValue) -> "StateVector":
        return StateVector(self.values + tuple(values))

    def replace(self, *values: StateValue) -> "StateVector":
        replacements = {value.address: value for value in values}
        existing = {value.address for value in self.values}
        merged = [
            replacements.get(value.address, value)
            for value in self.values
        ]
        merged.extend(
            value
            for value in values
            if value.address not in existing
        )
        return StateVector(tuple(merged))


@dataclass(frozen=True)
class TracePoint:
    """One point in a toolpath, preserving local PGMX Z and optional ISO Z."""

    x: Optional[float]
    y: Optional[float]
    local_z: Optional[float]
    iso_z: Optional[float]
    source: EvidenceSource


@dataclass(frozen=True)
class TraceMove:
    """One trace segment or toolpath block observed in the PGMX."""

    name: str
    points: tuple[TracePoint, ...]
    feed: Optional[float] = None
    source: Optional[EvidenceSource] = None


@dataclass(frozen=True)
class StateStage:
    """One executable or explanatory stage in the state synthesis plan."""

    key: str
    family: str
    order_index: int
    target_state: StateVector
    trace: tuple[TraceMove, ...] = ()
    reset_state: StateVector = StateVector()
    xiso_statement: Optional[str] = None
    feature_id: str = ""
    operation_id: str = ""
    working_step_id: str = ""
    notes: tuple[str, ...] = ()
    warnings: tuple[IsoStateWarning, ...] = ()


@dataclass(frozen=True)
class StateChange:
    """A value needed by a stage compared against the active state."""

    layer: str
    key: str
    before: Any
    after: Any
    change_type: str
    source: EvidenceSource
    confidence: str = "observed"
    note: str = ""

    @property
    def address(self) -> str:
        return f"{self.layer}.{self.key}"


@dataclass(frozen=True)
class StageDifferential:
    """Differences required to execute one stage."""

    stage_key: str
    family: str
    order_index: int
    target_changes: tuple[StateChange, ...]
    forced_values: tuple[StateChange, ...] = ()
    reset_changes: tuple[StateChange, ...] = ()
    trace: tuple[TraceMove, ...] = ()
    notes: tuple[str, ...] = ()
    warnings: tuple[IsoStateWarning, ...] = ()

    @property
    def change_count(self) -> int:
        return (
            len(self.target_changes)
            + len(self.forced_values)
            + len(self.reset_changes)
        )


@dataclass(frozen=True)
class IsoStatePlan:
    """State-oriented view of a PGMX file before ISO emission exists."""

    source_path: Path
    project_name: str
    initial_state: StateVector
    stages: tuple[StateStage, ...]
    warnings: tuple[IsoStateWarning, ...] = ()

    def summary(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "project_name": self.project_name,
            "state_values": len(self.initial_state.values),
            "stages": len(self.stages),
            "warnings": len(self.warnings),
            "stage_keys": [stage.key for stage in self.stages],
        }


@dataclass(frozen=True)
class IsoStateEvaluation:
    """A state plan evaluated as stage-by-stage differentials."""

    source_path: Path
    project_name: str
    initial_state: StateVector
    differentials: tuple[StageDifferential, ...]
    final_state: StateVector
    warnings: tuple[IsoStateWarning, ...] = ()

    def summary(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "project_name": self.project_name,
            "initial_state_values": len(self.initial_state.values),
            "final_state_values": len(self.final_state.values),
            "stages": len(self.differentials),
            "changes": sum(item.change_count for item in self.differentials),
            "warnings": len(self.warnings),
            "stage_changes": {
                item.stage_key: item.change_count
                for item in self.differentials
            },
        }


def to_jsonable(value: Any) -> Any:
    """Convert nested dataclasses, tuples and paths to JSON-friendly objects."""

    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value
