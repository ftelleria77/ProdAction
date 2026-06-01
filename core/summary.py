"""Summary exports and compatibility facades."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.model import Project, normalize_piece_grain_direction
from core.production_sheet import export_production_sheet, export_production_sheet_pdf


def _safe_int(value, default=1) -> int:
    try:
        parsed = int(float(value))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _effective_piece_quantity(piece_quantity, module_quantity) -> int:
    return _safe_int(piece_quantity, default=1) * _safe_int(module_quantity, default=1)


def export_summary(project: Project, output_csv: Path):
    """Export a per-piece CSV summary."""

    modules_sorted = sorted(project.modules, key=lambda module: module.is_manual)

    rows = []
    for module in modules_sorted:
        module_quantity = _safe_int(getattr(module, "quantity", None), default=1)
        for piece in module.pieces:
            if piece.thickness == 0 or piece.thickness is None:
                continue
            rows.append({
                "module": module.name,
                "piece_id": piece.id,
                "piece_name": piece.name or piece.id,
                "quantity": _effective_piece_quantity(piece.quantity, module_quantity),
                "height": piece.height,
                "width": piece.width,
                "thickness": piece.thickness,
                "color": piece.color,
                "grain_direction": normalize_piece_grain_direction(piece.grain_direction),
                "source": piece.cnc_source,
            })

    columns = [
        "module",
        "piece_id",
        "piece_name",
        "quantity",
        "height",
        "width",
        "thickness",
        "color",
        "grain_direction",
        "source",
    ]
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(output_csv, index=False, encoding="utf-8", sep=";")
    return df


__all__ = [
    "export_summary",
    "export_production_sheet",
    "export_production_sheet_pdf",
]
