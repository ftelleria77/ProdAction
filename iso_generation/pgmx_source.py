"""PGMX reader/adaptation layer for future ISO translation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools import synthesize_pgmx as sp
from tools.pgmx_adapters import PgmxAdaptationResult, adapt_pgmx_path
from tools.pgmx_snapshot import PgmxSnapshot

from .model import IsoGenerationWarning, to_jsonable


SPECIAL_TOOL_POLICY: dict[str, str] = {
    "E002": (
        "Sierra Horizontal: blocked for automatic PGMX trace generation until "
        "that family has safe rules. Existing Maestro-defined traces may be "
        "translated when their ISO contract is generalized."
    ),
    "E005": (
        "Fresa 45 grados: automatic PGMX generation is allowed only for "
        "en_juego division with the established separation/depth rule. Existing "
        "Maestro-defined traces may be translated with a warning."
    ),
    "E006": (
        "Fresa 0 grados / rectificado: blocked for automatic PGMX trace "
        "generation until shallow surface/rectification rules are studied. "
        "Existing Maestro-defined traces may be translated with a warning."
    ),
}

TOOL_ID_TO_ROUTER_NAME: dict[str, str] = {
    "1901": "E002",
    "1904": "E005",
    "1905": "E006",
}


@dataclass(frozen=True)
class PgmxIsoSource:
    """Snapshot and adaptation result used as source for ISO work."""

    path: Path
    snapshot: PgmxSnapshot
    adaptation: PgmxAdaptationResult
    warnings: tuple[IsoGenerationWarning, ...]

    @property
    def state(self) -> sp.PgmxState:
        return self.snapshot.state

    @property
    def adapted_count(self) -> int:
        return len(self.adaptation.adapted_entries)

    @property
    def unsupported_count(self) -> int:
        return len(self.adaptation.unsupported_entries)

    @property
    def ignored_count(self) -> int:
        return len(self.adaptation.ignored_entries)

    def summary(self) -> dict[str, Any]:
        """Return a compact JSON-friendly summary."""

        counts = {
            "entries": len(self.adaptation.entries),
            "adapted": self.adapted_count,
            "unsupported": self.unsupported_count,
            "ignored": self.ignored_count,
            "line_millings": len(self.adaptation.line_millings),
            "slot_millings": len(self.adaptation.slot_millings),
            "polyline_millings": len(self.adaptation.polyline_millings),
            "circle_millings": len(self.adaptation.circle_millings),
            "squaring_millings": len(self.adaptation.squaring_millings),
            "drillings": len(self.adaptation.drillings),
            "drilling_patterns": len(self.adaptation.drilling_patterns),
        }
        return {
            "source_path": str(self.path),
            "project_name": self.snapshot.project_name,
            "piece": to_jsonable(self.state),
            "counts": counts,
            "warnings": to_jsonable(self.warnings),
        }


def load_pgmx_iso_source(path: Path) -> PgmxIsoSource:
    """Read a `.pgmx`, adapt it through existing PGMX APIs, and collect policy warnings."""

    path = Path(path)
    adaptation = adapt_pgmx_path(path)
    return PgmxIsoSource(
        path=path,
        snapshot=adaptation.snapshot,
        adaptation=adaptation,
        warnings=_collect_policy_warnings(adaptation),
    )


def _collect_policy_warnings(result: PgmxAdaptationResult) -> tuple[IsoGenerationWarning, ...]:
    warnings: list[IsoGenerationWarning] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in result.entries:
        source = entry.working_step_name or entry.feature_name or entry.feature_id
        for tool_name in _entry_tool_names(result, entry):
            message = SPECIAL_TOOL_POLICY.get(tool_name)
            if message is None:
                continue
            key = (entry.feature_id, entry.operation_id or "", tool_name)
            if key in seen:
                continue
            seen.add(key)
            warnings.append(
                IsoGenerationWarning(
                    code=f"special_tool_{tool_name.lower()}",
                    message=message,
                    source=source,
                )
            )
    return tuple(warnings)


def _entry_tool_names(
    result: PgmxAdaptationResult,
    entry: Any,
) -> tuple[str, ...]:
    labels: list[str] = []
    spec = getattr(entry, "spec", None)
    if spec is not None:
        labels.extend(
            [
                str(getattr(spec, "tool_name", "") or ""),
                str(getattr(spec, "tool_id", "") or ""),
            ]
        )
    operation_id = getattr(entry, "operation_id", None)
    if operation_id:
        operation = result.snapshot.operation_by_id.get(operation_id)
        if operation is not None and operation.tool_key is not None:
            labels.extend([operation.tool_key.name, operation.tool_key.id])

    normalized: list[str] = []
    for label in labels:
        tool_name = _normalize_tool_label(label)
        if tool_name and tool_name not in normalized:
            normalized.append(tool_name)
    return tuple(normalized)


def _normalize_tool_label(value: str) -> str:
    value = value.strip().upper()
    if not value:
        return ""
    if value in TOOL_ID_TO_ROUTER_NAME:
        return TOOL_ID_TO_ROUTER_NAME[value]
    if value.startswith("E") and value[1:].isdigit():
        return f"E{int(value[1:]):03d}"
    return value
