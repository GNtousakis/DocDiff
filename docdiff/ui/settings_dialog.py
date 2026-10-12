from __future__ import annotations

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QKeySequenceEdit, QLabel, QMessageBox, QVBoxLayout,
)

from docdiff import strings
from docdiff.platform_win import HotkeyError, parse_hotkey
from docdiff.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(strings.SETTINGS_TITLE)
        self.setMinimumWidth(460)
        self.edit_a = self._hotkey_edit(settings.hotkey_a)
        self.edit_b = self._hotkey_edit(settings.hotkey_b)
        self.chk_case = QCheckBox(strings.SETTINGS_IGNORE_CASE)
        self.chk_case.setChecked(settings.ignore_case)
        self.chk_punct = QCheckBox(strings.SETTINGS_IGNORE_PUNCT)
        self.chk_punct.setChecked(settings.ignore_punctuation)
        hint = QLabel(strings.SETTINGS_HOTKEY_HINT)
        hint.setObjectName("status")
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.addRow(strings.SETTINGS_HOTKEY_A, self.edit_a)
        form.addRow(strings.SETTINGS_HOTKEY_B, self.edit_b)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(strings.SETTINGS_OK)
        buttons.button(QDialogButtonBox.Cancel).setText(strings.SETTINGS_CANCEL)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)
        lay.addLayout(form)
        lay.addWidget(hint)
        lay.addWidget(self.chk_case)
        lay.addWidget(self.chk_punct)
        lay.addWidget(buttons)
        self.result_settings: AppSettings | None = None

    @staticmethod
    def _hotkey_edit(text: str) -> QKeySequenceEdit:
        edit = QKeySequenceEdit(QKeySequence(text))
        edit.setMaximumSequenceLength(1)
        edit.setMinimumHeight(34)
        return edit

    def _accept(self) -> None:
        a = self.edit_a.keySequence().toString(QKeySequence.PortableText)
        b = self.edit_b.keySequence().toString(QKeySequence.PortableText)
        for text in (a, b):
            try:
                parse_hotkey(text)
            except HotkeyError:
                QMessageBox.warning(self, strings.MSG_TITLE_WARNING, strings.ERR_HOTKEY_INVALID.format(hotkey=text or "—"))
                return
        if a.upper() == b.upper():
            QMessageBox.warning(self, strings.MSG_TITLE_WARNING, strings.ERR_HOTKEY_SAME)
            return
        self.result_settings = AppSettings(a, b, self.chk_case.isChecked(), self.chk_punct.isChecked())
        self.accept()
