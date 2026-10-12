"""Global hotkeys: RegisterHotKey + a Qt native event filter for WM_HOTKEY."""
from __future__ import annotations

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal

from docdiff.platform_win import IS_WINDOWS, WM_HOTKEY, HotkeyRegistry


class _Filter(QAbstractNativeEventFilter):
    def __init__(self, registry: HotkeyRegistry, callback):
        super().__init__()
        self._registry = registry
        self._callback = callback

    def nativeEventFilter(self, event_type, message):
        if IS_WINDOWS and bytes(event_type) == b"windows_generic_MSG":
            import ctypes
            from ctypes import wintypes

            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                name = self._registry.name_for(int(msg.wParam))
                if name:
                    self._callback(name)
                    return True, 0
        return False, 0


class HotkeyManager(QObject):
    """Registers the A/B hotkeys and emits ``triggered('A' | 'B')``."""

    triggered = Signal(str)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._registry = HotkeyRegistry()
        self._filter = _Filter(self._registry, self.triggered.emit)
        app.installNativeEventFilter(self._filter)

    def apply(self, hotkey_a: str, hotkey_b: str) -> dict[str, str]:
        """(Re)register both hotkeys. Returns {hotkey text: error code} for failures."""
        self._registry.unregister_all()
        errors = {}
        for name, text in (("A", hotkey_a), ("B", hotkey_b)):
            err = self._registry.register(name, text)
            if err:
                errors[text] = err
        return errors

    def shutdown(self) -> None:
        self._registry.unregister_all()
