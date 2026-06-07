"""Work grouping and transition planning for ISO emission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .catalog import select_transition_id
from .model import StageDifferential


_COMMON_STAGE_KEYS = {"program_header", "machine_preamble", "program_close"}
_WORK_STAGE_KEYS = {
    "top_drill": ("top_drill_prepare", "top_drill_trace", "top_drill_reset"),
    "side_drill": ("side_drill_prepare", "side_drill_trace", "side_drill_reset"),
    "slot_milling": ("slot_milling_prepare", "slot_milling_trace", "slot_milling_reset"),
    "line_milling": ("line_milling_prepare", "line_milling_trace", "line_milling_reset"),
    "profile_milling": ("profile_milling_prepare", "profile_milling_trace", "profile_milling_reset"),
}


@dataclass(frozen=True)
class _WorkGroup:
    """Prepared work group plus catalog transitions to neighboring groups."""

    family: str
    prepare: StageDifferential
    trace: StageDifferential
    reset: StageDifferential
    incoming_transition_id: Optional[str] = None
    outgoing_transition_id: Optional[str] = None


def _work_stage_groups(
    ordered_differentials: list[StageDifferential],
) -> tuple[_WorkGroup, ...]:
    work = [
        differential
        for differential in ordered_differentials
        if differential.stage_key not in _COMMON_STAGE_KEYS
    ]
    if not work or len(work) % 3:
        return ()

    raw_groups: list[tuple[str, StageDifferential, StageDifferential, StageDifferential]] = []
    for index in range(0, len(work), 3):
        stage_group = work[index : index + 3]
        stage_keys = tuple(differential.stage_key for differential in stage_group)
        for family, expected_keys in _WORK_STAGE_KEYS.items():
            if stage_keys == expected_keys:
                prepare, trace, reset = stage_group
                raw_groups.append((family, prepare, trace, reset))
                break
        else:
            return ()
    return _plan_work_groups(tuple(raw_groups))


def _plan_work_groups(
    groups: tuple[tuple[str, StageDifferential, StageDifferential, StageDifferential], ...],
) -> tuple[_WorkGroup, ...]:
    planned: list[_WorkGroup] = []
    for index, (family, prepare, trace, reset) in enumerate(groups):
        previous = groups[index - 1] if index > 0 else None
        next_group = groups[index + 1] if index < len(groups) - 1 else None
        incoming_transition_id = (
            select_transition_id(previous[0], previous[1], family, prepare)
            if previous is not None
            else None
        )
        outgoing_transition_id = (
            select_transition_id(family, prepare, next_group[0], next_group[1])
            if next_group is not None
            else None
        )
        planned.append(
            _WorkGroup(
                family=family,
                prepare=prepare,
                trace=trace,
                reset=reset,
                incoming_transition_id=incoming_transition_id,
                outgoing_transition_id=outgoing_transition_id,
            )
        )
    return tuple(planned)
