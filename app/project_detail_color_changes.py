"""Scoped color-change application for project-detail inspection."""

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Callable, Iterable, MutableSequence

from core.model import ModuleData

from app.project_detail_colors import (
    apply_color_to_matching_pieces,
    apply_color_to_matching_rows,
    apply_color_to_piece_row,
    module_locale_key,
)


@dataclass(frozen=True)
class ColorChangeScopeResult:
    applied: bool
    changed_count: int = 0


def is_same_module(left: ModuleData, right: ModuleData) -> bool:
    return (left.relative_path or left.path) == (right.relative_path or right.path)


def apply_scoped_color_change(
    *,
    project_modules: Iterable[ModuleData],
    selected_module: ModuleData,
    current_rows: MutableSequence[dict],
    current_color: str,
    new_color: str | None,
    scope: str,
    target_row_index: int | None,
    force_no_grain: bool,
    project_root: str | Path,
    module_config_path: Callable[[ModuleData], Path],
    persist_current_module: Callable[[], None],
    generated_at: str | None = None,
) -> ColorChangeScopeResult:
    changed_count = 0

    if scope == "piece":
        if target_row_index is None or target_row_index < 0 or target_row_index >= len(current_rows):
            return ColorChangeScopeResult(applied=False)
        apply_color_to_piece_row(
            current_rows[target_row_index],
            new_color,
            force_no_grain=force_no_grain,
        )
        persist_current_module()
        return ColorChangeScopeResult(applied=True, changed_count=1)

    if scope == "module":
        changed_count += apply_color_to_matching_rows(
            current_rows,
            current_color,
            new_color,
            force_no_grain=force_no_grain,
        )
        persist_current_module()
        return ColorChangeScopeResult(applied=True, changed_count=changed_count)

    changed_count += apply_color_to_matching_rows(
        current_rows,
        current_color,
        new_color,
        force_no_grain=force_no_grain,
    )
    persist_current_module()

    current_locale_key = module_locale_key(selected_module, project_root)
    if not current_locale_key:
        return ColorChangeScopeResult(applied=True, changed_count=changed_count)

    config_generated_at = generated_at or datetime.now().isoformat(sep=" ", timespec="seconds")
    for module in project_modules:
        if is_same_module(module, selected_module):
            continue
        if module_locale_key(module, project_root) != current_locale_key:
            continue

        changed_count += apply_color_to_matching_pieces(
            getattr(module, "pieces", []),
            current_color,
            new_color,
            force_no_grain=force_no_grain,
        )

        other_config_path = module_config_path(module)
        if not other_config_path.exists():
            continue
        try:
            other_config = json.loads(other_config_path.read_text(encoding="utf-8"))
            changed_rows = apply_color_to_matching_rows(
                other_config.get("pieces", []),
                current_color,
                new_color,
                force_no_grain=force_no_grain,
            )
            if changed_rows:
                changed_count += changed_rows
                other_config["generated_at"] = config_generated_at
                other_config_path.write_text(
                    json.dumps(other_config, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
        except Exception:
            pass

    return ColorChangeScopeResult(applied=True, changed_count=changed_count)
