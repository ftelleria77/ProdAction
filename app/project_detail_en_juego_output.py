"""Output helpers for creating En-Juego PGMX files from the project detail UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from core.en_juego_synthesis import create_en_juego_pgmx


def en_juego_output_path_for_config(output_path, module_path) -> str:
    generated_output_path = Path(output_path)
    module_path = Path(module_path)
    try:
        return str(
            generated_output_path.resolve().relative_to(module_path.resolve())
        ).replace("\\", "/")
    except Exception:
        return str(generated_output_path)


def en_juego_creation_details(result: Any) -> list[str]:
    details = [
        f"Archivo generado: {result.output_path}",
        (
            "Tablero sintetizado: "
            f"{result.board_width:.2f} x {result.board_height:.2f} x "
            f"{result.board_thickness:.2f} mm"
        ),
        f"Piezas ubicadas: {result.instance_count}",
        f"Contornos generados: {result.contour_count}",
    ]
    if result.fallback_contour_count:
        details.append(
            "Contornos por rectángulo de respaldo: "
            f"{result.fallback_contour_count}"
        )
    return details


def create_en_juego_pgmx_from_dialog(
    *,
    parent_dialog,
    project,
    module_name: str,
    module_path,
    piece_rows: list[dict],
    config_data: dict,
    en_juego_settings: dict,
    sync_settings_from_controls,
    save_composition_layout,
    sync_en_juego_observations,
    persist_module_config,
    refresh_pieces_table,
) -> None:
    sync_settings_from_controls()
    if en_juego_settings.get("cut_mode") != "nesting":
        QMessageBox.information(
            parent_dialog,
            "Crear En-Juego",
            "La generación del En-Juego automático solo está disponible con 'Corte Nesting'.",
        )
        return

    module_path = Path(module_path)
    default_name = f"{module_name}_EnJuego.pgmx"
    default_path = module_path / default_name
    output_file, _ = QFileDialog.getSaveFileName(
        parent_dialog,
        "Crear En-Juego",
        str(default_path),
        "Programas PGMX (*.pgmx);;Todos los archivos (*.*)",
    )
    if not output_file:
        return

    sync_settings_from_controls()
    save_composition_layout()
    config_data["en_juego_settings"] = dict(en_juego_settings)
    persist_module_config()

    try:
        result = create_en_juego_pgmx(
            project=project,
            module_name=module_name,
            module_path=module_path,
            piece_rows=piece_rows,
            saved_layout=config_data.get("en_juego_layout", {}),
            settings=config_data.get("en_juego_settings", {}),
            output_path=Path(output_file),
        )
    except Exception as exc:
        QMessageBox.critical(
            parent_dialog,
            "Crear En-Juego",
            f"No se pudo generar el archivo En-Juego.\n\n{exc}",
        )
        return

    config_data["en_juego_output_path"] = en_juego_output_path_for_config(
        result.output_path,
        module_path,
    )

    sync_en_juego_observations()
    persist_module_config()
    refresh_pieces_table()

    QMessageBox.information(
        parent_dialog,
        "Crear En-Juego",
        "\n".join(en_juego_creation_details(result)),
    )
