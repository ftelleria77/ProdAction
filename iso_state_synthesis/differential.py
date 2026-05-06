"""State differential calculation for ISO state synthesis plans."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .model import (
    EvidenceSource,
    IsoStateEvaluation,
    IsoStatePlan,
    StageDifferential,
    StateChange,
    StateValue,
    StateVector,
)
from .pgmx_source import build_state_plan_from_pgmx

BORING_HEAD_SPEED_RULE_PATH = (
    "iso_state_synthesis/experiments/003_boring_head_speed_state.md"
)


def evaluate_pgmx_state_plan(path: Path) -> IsoStateEvaluation:
    """Build and evaluate a state plan for a `.pgmx` file."""

    return evaluate_state_plan(build_state_plan_from_pgmx(Path(path)))


def evaluate_state_plan(plan: IsoStatePlan) -> IsoStateEvaluation:
    """Calculate stage-by-stage differences from the active state."""

    current_state = plan.initial_state
    differentials: list[StageDifferential] = []
    warnings = list(plan.warnings)

    for stage in sorted(plan.stages, key=lambda item: item.order_index):
        target_changes, forced_values = _changes_for_values(
            current_state,
            stage.target_state.values,
            default_change_type="set",
            forced_change_type="force",
        )
        target_changes = target_changes + _boring_head_speed_activation_changes(
            current_state,
            stage.target_state,
        )
        current_state = current_state.replace(*stage.target_state.values)

        reset_changes, forced_resets = _changes_for_values(
            current_state,
            stage.reset_state.values,
            default_change_type="reset",
            forced_change_type="force_reset",
        )
        current_state = current_state.replace(*stage.reset_state.values)

        differentials.append(
            StageDifferential(
                stage_key=stage.key,
                family=stage.family,
                order_index=stage.order_index,
                target_changes=target_changes,
                forced_values=forced_values + forced_resets,
                reset_changes=reset_changes,
                trace=stage.trace,
                notes=stage.notes,
                warnings=stage.warnings,
            )
        )
        warnings.extend(stage.warnings)

    return IsoStateEvaluation(
        source_path=plan.source_path,
        project_name=plan.project_name,
        initial_state=plan.initial_state,
        differentials=tuple(differentials),
        final_state=current_state,
        warnings=tuple(warnings),
    )


def _boring_head_speed_activation_changes(
    current_state: StateVector,
    target_state: StateVector,
) -> tuple[StateChange, ...]:
    target_speed = target_state.find("maquina", "boring_head_speed")
    if target_speed is None:
        return ()

    active_speed = current_state.find("maquina", "boring_head_speed")
    before_speed = active_speed.value if active_speed is not None else None
    if active_speed is not None and _same_value(before_speed, target_speed.value):
        return ()

    active_etk = current_state.find("salida", "etk_17")
    before_etk = active_etk.value if active_etk is not None else None
    return (
        StateChange(
            layer="salida",
            key="etk_17",
            before=before_etk,
            after=257,
            change_type="emit",
            source=EvidenceSource(
                "observed_rule",
                BORING_HEAD_SPEED_RULE_PATH,
                "boring_head_speed_change",
            ),
            confidence="confirmed",
            note=(
                "Activacion de cambio de velocidad del BooringUnitHead: "
                f"{before_speed!r} -> {target_speed.value!r}."
            ),
        ),
    )


def _changes_for_values(
    current_state: StateVector,
    values: tuple[StateValue, ...],
    *,
    default_change_type: str,
    forced_change_type: str,
) -> tuple[tuple[StateChange, ...], tuple[StateChange, ...]]:
    changes: list[StateChange] = []
    forced: list[StateChange] = []
    for value in values:
        before = current_state.find(value.layer, value.key)
        before_value = before.value if before is not None else None
        if before is None or not _same_value(before_value, value.value):
            changes.append(_state_change(value, before_value, default_change_type))
        elif value.required:
            forced.append(_state_change(value, before_value, forced_change_type))
    return tuple(changes), tuple(forced)


def _state_change(
    value: StateValue,
    before: Any,
    change_type: str,
) -> StateChange:
    return StateChange(
        layer=value.layer,
        key=value.key,
        before=before,
        after=value.value,
        change_type=change_type,
        source=value.source,
        confidence=value.confidence,
        note=value.note,
    )


def _same_value(left: Any, right: Any) -> bool:
    if isinstance(left, float) or isinstance(right, float):
        try:
            return math.isclose(float(left), float(right), abs_tol=1e-6)
        except (TypeError, ValueError):
            return False
    return left == right
