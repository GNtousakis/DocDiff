"""Persistent settings (QSettings)."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from docdiff.normalize import CompareOptions

DEFAULT_HOTKEY_A = "Ctrl+Alt+A"
DEFAULT_HOTKEY_B = "Ctrl+Alt+B"


def _bool(v, default: bool) -> bool:
    if v is None:
        return default
    return v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes")


@dataclass
class AppSettings:
    hotkey_a: str = DEFAULT_HOTKEY_A
    hotkey_b: str = DEFAULT_HOTKEY_B
    ignore_case: bool = True
    ignore_punctuation: bool = True

    @property
    def compare_options(self) -> CompareOptions:
        return CompareOptions(self.ignore_case, self.ignore_punctuation)


class SettingsStore:
    """Thin wrapper over QSettings; pass ``qsettings`` to use a custom backend (tests)."""

    def __init__(self, qsettings: QSettings | None = None):
        self.q = qsettings or QSettings("DocDiff", "DocDiff")

    def load(self) -> AppSettings:
        q = self.q
        return AppSettings(
            hotkey_a=str(q.value("hotkey_a", DEFAULT_HOTKEY_A)),
            hotkey_b=str(q.value("hotkey_b", DEFAULT_HOTKEY_B)),
            ignore_case=_bool(q.value("ignore_case"), True),
            ignore_punctuation=_bool(q.value("ignore_punctuation"), True),
        )

    def save(self, s: AppSettings) -> None:
        q = self.q
        q.setValue("hotkey_a", s.hotkey_a)
        q.setValue("hotkey_b", s.hotkey_b)
        q.setValue("ignore_case", s.ignore_case)
        q.setValue("ignore_punctuation", s.ignore_punctuation)
        q.sync()

    def load_geometry(self):
        return self.q.value("window_geometry")

    def save_geometry(self, data) -> None:
        self.q.setValue("window_geometry", data)
        self.q.sync()
