from __future__ import annotations

import unittest
from unittest import mock

from PySide6.QtWidgets import QMessageBox

from app.project_detail_dialog_lifecycle import (
    close_dialog_if_confirmed,
    confirm_save_before_close,
    install_reject_confirmation,
)


class FakeDialog:
    def __init__(self) -> None:
        self.accept_count = 0
        self.reject_count = 0

    def accept(self) -> None:
        self.accept_count += 1

    def reject(self) -> None:
        self.reject_count += 1


class ProjectDetailDialogLifecycleTests(unittest.TestCase):
    def test_confirm_save_before_close_returns_true_without_unsaved_changes(self) -> None:
        save_calls = []

        with mock.patch("app.project_detail_dialog_lifecycle.QMessageBox.question") as question:
            result = confirm_save_before_close(
                None,
                lambda: False,
                lambda **kwargs: save_calls.append(kwargs),
            )

        self.assertTrue(result)
        self.assertEqual(save_calls, [])
        question.assert_not_called()

    def test_confirm_save_before_close_saves_when_user_accepts(self) -> None:
        save_calls = []

        with mock.patch(
            "app.project_detail_dialog_lifecycle.QMessageBox.question",
            return_value=QMessageBox.Yes,
        ):
            result = confirm_save_before_close(
                None,
                lambda: True,
                lambda **kwargs: save_calls.append(kwargs),
            )

        self.assertTrue(result)
        self.assertEqual(save_calls, [{"show_feedback": False}])

    def test_confirm_save_before_close_allows_discard_and_blocks_cancel(self) -> None:
        with mock.patch(
            "app.project_detail_dialog_lifecycle.QMessageBox.question",
            return_value=QMessageBox.No,
        ):
            self.assertTrue(confirm_save_before_close(None, lambda: True, lambda **_: None))

        with mock.patch(
            "app.project_detail_dialog_lifecycle.QMessageBox.question",
            return_value=QMessageBox.Cancel,
        ):
            self.assertFalse(confirm_save_before_close(None, lambda: True, lambda **_: None))

    def test_close_dialog_if_confirmed_accepts_only_when_allowed(self) -> None:
        dialog = FakeDialog()

        close_dialog_if_confirmed(dialog, lambda: False)
        close_dialog_if_confirmed(dialog, lambda: True)

        self.assertEqual(dialog.accept_count, 1)

    def test_install_reject_confirmation_preserves_original_reject(self) -> None:
        dialog = FakeDialog()
        install_reject_confirmation(dialog, lambda: False)
        dialog.reject()
        self.assertEqual(dialog.reject_count, 0)

        allowed_dialog = FakeDialog()
        install_reject_confirmation(allowed_dialog, lambda: True)
        allowed_dialog.reject()
        self.assertEqual(allowed_dialog.reject_count, 1)


if __name__ == "__main__":
    unittest.main()
