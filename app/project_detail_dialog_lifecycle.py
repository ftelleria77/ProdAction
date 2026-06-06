"""Lifecycle helpers for project detail dialogs."""

from typing import Callable

from PySide6.QtWidgets import QMessageBox


def confirm_save_before_close(
    parent,
    has_unsaved_changes: Callable[[], bool],
    save_settings: Callable[..., None],
) -> bool:
    if not has_unsaved_changes():
        return True

    answer = QMessageBox.question(
        parent,
        "Cambios sin guardar",
        "Hay cambios sin guardar en la configuración del módulo. ¿Desea guardarlos antes de cerrar?",
        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
        QMessageBox.Yes,
    )

    if answer == QMessageBox.Yes:
        save_settings(show_feedback=False)
        return True
    return answer == QMessageBox.No


def close_dialog_if_confirmed(dialog, can_close: Callable[[], bool]) -> None:
    if can_close():
        dialog.accept()


def install_reject_confirmation(dialog, can_close: Callable[[], bool]) -> None:
    original_reject = dialog.reject

    def reject_with_confirmation():
        if can_close():
            original_reject()

    dialog.reject = reject_with_confirmation
