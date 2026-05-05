"""Minimal modal-state planner for ISO transition emission.

This module is intentionally small: it starts with operation-level modal
contracts and the transitions already validated from an 082 top slot to
drilling. More transitions can move here as their observed Maestro behavior is
proven.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


LineFormatter = Callable[[float], str]
SafeZEmitter = Callable[[], str]


@dataclass(frozen=True)
class ModalState:
    """Observed machine state left by the previous emitted block."""

    plane_context: str = "Top"
    operation_family: Optional[str] = None
    active_etk1: Optional[int] = None
    active_etk7: Optional[int] = None
    active_etk8: Optional[int] = None
    compensation: str = "G40"
    mlv_mode: int = 2
    safe_z_known: bool = False
    length_comp_active: bool = False
    radius_comp_active: bool = False


@dataclass(frozen=True)
class OperationRequirement:
    """Modal requirements before the next operation can start."""

    plane_context: str
    active_etk8: Optional[int] = None
    compensation: str = "G40"
    mlv_mode: int = 2
    safe_z_required: bool = True
    operation_reentry_required: bool = True
    reset_etk1: bool = False


@dataclass(frozen=True)
class OperationPlan:
    """Operation-level modal contract independent of complete sequence shape."""

    family: str
    plane_context: str
    requirement: OperationRequirement
    leaves_profile_active: bool = False
    leaves_drilling_active: bool = False


@dataclass(frozen=True)
class TransitionPlan:
    """Concrete transition lines plus the modal state after applying them."""

    lines: tuple[str, ...]
    state_after: ModalState
    actions: tuple[str, ...] = field(default_factory=tuple)


def operation_reentry_lines(
    *,
    origin_z: float,
    format_mm: LineFormatter,
) -> tuple[str, ...]:
    return (
        "MLV=1",
        f"SHF[Z]={format_mm(origin_z)}+%ETK[114]/1000",
        "MLV=2",
        "G17",
    )


def plan_transition(
    current: ModalState,
    required: OperationRequirement,
    *,
    origin_z: float,
    format_mm: LineFormatter,
    safe_z_line: SafeZEmitter,
) -> TransitionPlan:
    """Emit the minimal observed modal diff for currently supported cases."""

    lines: list[str] = []
    actions: list[str] = []

    if required.active_etk8 is not None and current.active_etk8 != required.active_etk8:
        lines.append(f"?%ETK[8]={required.active_etk8}")
        actions.append("set_etk8")

    if required.compensation == "G40" and current.compensation != "G40":
        lines.append("G40")
        actions.append("cancel_compensation")
    elif required.compensation == "G40":
        # Maestro emits this defensively on the validated slot -> side transition.
        lines.append("G40")
        actions.append("confirm_g40")

    if required.safe_z_required:
        lines.extend(("MLV=0", safe_z_line(), "MLV=2"))
        actions.append("safe_z")

    if required.reset_etk1 and current.active_etk1 not in {None, 0}:
        lines.append("?%ETK[1]=0")
        actions.append("reset_etk1")

    if required.operation_reentry_required:
        lines.extend(
            operation_reentry_lines(
                origin_z=origin_z,
                format_mm=format_mm,
            )
        )
        actions.append("operation_reentry")

    return TransitionPlan(
        lines=tuple(lines),
        state_after=ModalState(
            plane_context=required.plane_context,
            operation_family=current.operation_family,
            active_etk1=0 if required.reset_etk1 else current.active_etk1,
            active_etk7=current.active_etk7,
            active_etk8=required.active_etk8,
            compensation=required.compensation,
            mlv_mode=required.mlv_mode,
            safe_z_known=required.safe_z_required,
            length_comp_active=False,
            radius_comp_active=False,
        ),
        actions=tuple(actions),
    )
