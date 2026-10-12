"""Windows-only helpers (DPI awareness, global hotkeys), guarded for other platforms."""
from __future__ import annotations

import sys

IS_WINDOWS = sys.platform == "win32"

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
WM_HOTKEY = 0x0312
_DPI_PER_MONITOR_AWARE_V2 = -4

_MODIFIERS = {"CTRL": MOD_CONTROL, "CONTROL": MOD_CONTROL, "ALT": MOD_ALT, "SHIFT": MOD_SHIFT, "WIN": MOD_WIN, "META": MOD_WIN}


def enable_per_monitor_dpi_v2() -> bool:
    """Per-monitor DPI awareness v2; must run before any window is created."""
    if not IS_WINDOWS:
        return False
    import ctypes

    try:
        return bool(ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(_DPI_PER_MONITOR_AWARE_V2)))
    except (AttributeError, OSError):
        pass
    try:  # Windows 8.1 fallback: per-monitor v1
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return True
    except (AttributeError, OSError):
        return False


class HotkeyError(ValueError):
    pass


def parse_hotkey(text: str) -> tuple[int, int]:
    """'Ctrl+Alt+A' -> (modifiers, virtual-key code). Raises HotkeyError if unusable."""
    parts = [p.strip() for p in text.split("+") if p.strip()]
    if len(parts) < 2:
        raise HotkeyError(text)
    mods = 0
    for p in parts[:-1]:
        m = _MODIFIERS.get(p.upper())
        if m is None:
            raise HotkeyError(text)
        mods |= m
    key = parts[-1].upper()
    if len(key) == 1 and ("A" <= key <= "Z" or "0" <= key <= "9"):
        vk = ord(key)
    elif key.startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x70 + int(key[1:]) - 1
    else:
        raise HotkeyError(text)
    return mods, vk


def hotkey_available() -> bool:
    return IS_WINDOWS


class HotkeyRegistry:
    """Registers/unregisters thread-level hotkeys with RegisterHotKey (no hooks)."""

    def __init__(self) -> None:
        self._ids: dict[int, str] = {}
        self._next = 0xB000

    def register(self, name: str, text: str) -> str | None:
        """Register ``text`` for ``name``. Returns None on success or an error code
        ('invalid', 'in_use', 'unsupported')."""
        try:
            mods, vk = parse_hotkey(text)
        except HotkeyError:
            return "invalid"
        if not IS_WINDOWS:
            return "unsupported"
        import ctypes

        hid = self._next
        self._next += 1
        if not ctypes.windll.user32.RegisterHotKey(None, hid, mods | MOD_NOREPEAT, vk):
            # Almost always ERROR_HOTKEY_ALREADY_REGISTERED (1409); report any failure as "in use".
            return "in_use"
        self._ids[hid] = name
        return None

    def unregister_all(self) -> None:
        if IS_WINDOWS:
            import ctypes

            for hid in self._ids:
                ctypes.windll.user32.UnregisterHotKey(None, hid)
        self._ids.clear()

    def name_for(self, hotkey_id: int) -> str | None:
        return self._ids.get(hotkey_id)
