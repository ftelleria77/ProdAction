"""PGMX inspection helpers for project detail."""

from pathlib import Path
from typing import Callable

from core.pgmx_processing import get_invalid_slot_machining_issues


def invalid_slot_cache_key(module_path: Path, source_value: str) -> tuple[str, str]:
    return str(module_path), str(source_value or "").strip()


def clear_invalid_slot_cache_entries(cache: dict, source_value: str | None = None) -> None:
    if source_value is None:
        cache.clear()
        return
    normalized_source = str(source_value or "").strip()
    keys_to_remove = [
        key for key in cache
        if len(key) > 1 and key[1] == normalized_source
    ]
    for key in keys_to_remove:
        cache.pop(key, None)


def get_cached_invalid_slot_issues(
    cache: dict,
    *,
    project,
    module_path: Path,
    piece_row: dict,
    build_piece: Callable[[dict], object],
):
    source_value = str(piece_row.get("source") or "").strip()
    if not source_value:
        return ()

    cache_key = invalid_slot_cache_key(module_path, source_value)
    if cache_key not in cache:
        try:
            cache[cache_key] = get_invalid_slot_machining_issues(
                project,
                build_piece(piece_row),
                module_path,
            )
        except Exception:
            cache[cache_key] = ()
    return cache.get(cache_key, ())


def invalid_slot_message(issues) -> str:
    if not issues:
        return ""
    first_issue = issues[0]
    feature_name = str(getattr(first_issue, "feature_name", None) or getattr(first_issue, "feature_id", None) or "ranura")
    return (
        f"Ranura no ejecutable: {feature_name}. "
        "Puede corregirse girando el PGMX 90 grados antihorario."
    )
