"""Reusable ISO block and transition catalog.

The source of truth for these identifiers is
``memory/iso_parameters_state_memory.md``. This module makes that memory
addressable from code without changing the current candidate ISO text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .model import StageDifferential


ISO_PARAMETERS_MEMORY_PATH = "iso_state_synthesis/memory/iso_parameters_state_memory.md"

ROUTER_HEAD = "router"
BORING_HEAD = "boring_head"
MACHINE_HEAD = "machine"
NO_HEAD = "none"

ROUTER_FAMILIES = frozenset({"line_milling", "profile_milling"})
BORING_HEAD_FAMILIES = frozenset({"top_drill", "side_drill", "slot_milling"})


@dataclass(frozen=True)
class IsoBlockDefinition:
    """Reusable block documented as ``B-*`` in the ISO parameter memory."""

    block_id: str
    family: str
    head: str
    stage: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class IsoTransitionDefinition:
    """Reusable transition documented as ``T-*`` in the ISO parameter memory."""

    transition_id: str
    transition_type: str
    from_head: str
    to_head: str
    from_family: str
    to_family: str
    condition: str
    evidence: tuple[str, ...]


BLOCKS: dict[str, IsoBlockDefinition] = {
    "B-PG-001": IsoBlockDefinition("B-PG-001", "program", MACHINE_HEAD, "preamble", ("S001",)),
    "B-FR-001": IsoBlockDefinition("B-FR-001", "frame", NO_HEAD, "piece_frame", ("S002",)),
    "B-RH-001": IsoBlockDefinition("B-RH-001", "router", ROUTER_HEAD, "prepare", ("S006", "S019")),
    "B-RH-002": IsoBlockDefinition("B-RH-002", "router", ROUTER_HEAD, "trace", ("S007",)),
    "B-RH-003": IsoBlockDefinition("B-RH-003", "router", ROUTER_HEAD, "reset", ("S008", "S019")),
    "B-BH-001": IsoBlockDefinition("B-BH-001", "top_drill", BORING_HEAD, "prepare", ("S003",)),
    "B-BH-002": IsoBlockDefinition("B-BH-002", "top_drill", BORING_HEAD, "trace", ("S004",)),
    "B-BH-003": IsoBlockDefinition("B-BH-003", "top_drill", BORING_HEAD, "reset_complete", ("S005",)),
    "B-BH-004": IsoBlockDefinition("B-BH-004", "side_drill", BORING_HEAD, "prepare", ("S009",)),
    "B-BH-005": IsoBlockDefinition("B-BH-005", "side_drill", BORING_HEAD, "trace", ("S010",)),
    "B-BH-006": IsoBlockDefinition("B-BH-006", "slot_milling", BORING_HEAD, "prepare", ("S013", "S017")),
    "B-BH-007": IsoBlockDefinition("B-BH-007", "slot_milling", BORING_HEAD, "trace", ("S013",)),
    "B-PG-002": IsoBlockDefinition("B-PG-002", "program", MACHINE_HEAD, "close", ("S014",)),
}


TRANSITIONS: dict[str, IsoTransitionDefinition] = {
    "T-RH-001": IsoTransitionDefinition(
        "T-RH-001",
        "internal_router_incremental",
        ROUTER_HEAD,
        ROUTER_HEAD,
        "router",
        "router",
        "same_router_tool",
        ("S015",),
    ),
    "T-RH-002": IsoTransitionDefinition(
        "T-RH-002",
        "internal_router_physical_change",
        ROUTER_HEAD,
        ROUTER_HEAD,
        "router",
        "router",
        "different_router_tool",
        ("S019",),
    ),
    "T-BH-001": IsoTransitionDefinition(
        "T-BH-001",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "top_drill",
        "top_drill",
        "vertical_drill_continuity_or_tool_change",
        ("S020", "S021"),
    ),
    "T-BH-002": IsoTransitionDefinition(
        "T-BH-002",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "top_drill",
        "side_drill",
        "vertical_to_horizontal_drill",
        ("S022",),
    ),
    "T-BH-003": IsoTransitionDefinition(
        "T-BH-003",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "side_drill",
        "side_drill",
        "horizontal_drill_tool_face_or_axis_change",
        ("S011", "S023"),
    ),
    "T-BH-004": IsoTransitionDefinition(
        "T-BH-004",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "side_drill",
        "top_drill",
        "horizontal_to_vertical_drill",
        ("S012", "S024"),
    ),
    "T-BH-005": IsoTransitionDefinition(
        "T-BH-005",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "top_drill",
        "slot_milling",
        "vertical_drill_to_top_slot",
        ("S017",),
    ),
    "T-BH-006": IsoTransitionDefinition(
        "T-BH-006",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "slot_milling",
        "top_drill",
        "top_slot_to_vertical_drill",
        ("S018",),
    ),
    "T-BH-007": IsoTransitionDefinition(
        "T-BH-007",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "side_drill",
        "slot_milling",
        "horizontal_drill_to_top_slot",
        ("S025",),
    ),
    "T-BH-008": IsoTransitionDefinition(
        "T-BH-008",
        "internal_boring_head",
        BORING_HEAD,
        BORING_HEAD,
        "slot_milling",
        "side_drill",
        "top_slot_to_horizontal_drill",
        ("S026",),
    ),
    "T-XH-001": IsoTransitionDefinition(
        "T-XH-001",
        "switching_heads",
        ROUTER_HEAD,
        BORING_HEAD,
        "router",
        "boring_head",
        "router_tool_to_drill_or_saw",
        ("S027",),
    ),
    "T-XH-002": IsoTransitionDefinition(
        "T-XH-002",
        "switching_heads",
        BORING_HEAD,
        ROUTER_HEAD,
        "boring_head",
        "router",
        "drill_or_saw_to_router_tool",
        ("S028",),
    ),
}


_STAGE_BLOCK_IDS = {
    "machine_preamble": "B-PG-001",
    "program_close": "B-PG-002",
    "top_drill_trace": "B-BH-002",
    "side_drill_trace": "B-BH-005",
    "slot_milling_trace": "B-BH-007",
    "line_milling_trace": "B-RH-002",
    "profile_milling_trace": "B-RH-002",
}

_RULE_STATUS_TRANSITION_IDS = {
    "generalized_router_to_top_drill_sequence": "T-XH-001",
    "generalized_router_to_side_drill_transition": "T-XH-001",
    "router_inter_work_observed": "T-RH-002",
    "generalized_top_to_side_drill_sequence": "T-BH-002",
    "generalized_side_to_top_drill_sequence": "T-BH-004",
    "generalized_top_to_slot_milling_sequence": "T-BH-005",
    "generalized_slot_to_top_drill_sequence": "T-BH-006",
    "generalized_side_to_slot_milling_sequence": "T-BH-007",
    "generalized_slot_to_side_drill_sequence": "T-BH-008",
    "generalized_router_to_slot_milling_sequence": "T-XH-001",
    "generalized_boring_to_router_sequence": "T-XH-002",
}


def head_for_family(family: str) -> Optional[str]:
    """Return the physical head used by a work family."""

    if family in ROUTER_FAMILIES:
        return ROUTER_HEAD
    if family in BORING_HEAD_FAMILIES:
        return BORING_HEAD
    return None


def block_id_for_stage_key(stage_key: str) -> Optional[str]:
    """Map the current stage keys to the reusable block catalog."""

    return _STAGE_BLOCK_IDS.get(stage_key)


def transition_id_for_rule_status(rule_status: str) -> Optional[str]:
    """Bridge current emitter rule labels to the reusable transition catalog."""

    return _RULE_STATUS_TRANSITION_IDS.get(rule_status)


def select_transition_id(
    previous_family: str,
    previous_prepare: StageDifferential,
    next_family: str,
    next_prepare: StageDifferential,
) -> Optional[str]:
    """Select a documented transition id for two neighboring work groups."""

    previous_head = head_for_family(previous_family)
    next_head = head_for_family(next_family)
    if previous_head is None or next_head is None:
        return None

    if previous_head != next_head:
        if previous_head == ROUTER_HEAD and next_head == BORING_HEAD:
            return "T-XH-001"
        if previous_head == BORING_HEAD and next_head == ROUTER_HEAD:
            return "T-XH-002"
        return None

    if previous_head == ROUTER_HEAD:
        if _router_tool_number(previous_prepare) == _router_tool_number(next_prepare):
            return "T-RH-001"
        return "T-RH-002"

    if previous_family == "top_drill" and next_family == "top_drill":
        return "T-BH-001"
    if previous_family == "top_drill" and next_family == "side_drill":
        return "T-BH-002"
    if previous_family == "side_drill" and next_family == "side_drill":
        return "T-BH-003"
    if previous_family == "side_drill" and next_family == "top_drill":
        return "T-BH-004"
    if previous_family == "top_drill" and next_family == "slot_milling":
        return "T-BH-005"
    if previous_family == "slot_milling" and next_family == "top_drill":
        return "T-BH-006"
    if previous_family == "side_drill" and next_family == "slot_milling":
        return "T-BH-007"
    if previous_family == "slot_milling" and next_family == "side_drill":
        return "T-BH-008"
    return None


def _tool_name(differential: StageDifferential) -> Optional[str]:
    value = _change_after(differential, "herramienta", "tool_name")
    if value is None:
        return None
    return str(value)


def _router_tool_number(differential: StageDifferential) -> Optional[int]:
    value = _change_after(differential, "herramienta", "tool_number")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _change_after(differential: StageDifferential, layer: str, key: str) -> object:
    for changes in (differential.target_changes, differential.forced_values):
        for change in changes:
            if change.layer == layer and change.key == key:
                return change.after
    return None
