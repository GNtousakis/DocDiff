"""Application entry point."""
from __future__ import annotations

import sys

from docdiff.platform_win import enable_per_monitor_dpi_v2


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        from docdiff.selftest import run_selftest

        out = argv[argv.index("--selftest") + 1] if len(argv) > argv.index("--selftest") + 1 else None
        return run_selftest(out)

    enable_per_monitor_dpi_v2()  # before any window exists
    from PySide6.QtWidgets import QApplication

    from docdiff.ocr import create_engine
    from docdiff.settings import SettingsStore
    from docdiff.ui import theme
    from docdiff.ui.hotkeys import HotkeyManager
    from docdiff.ui.main_window import MainWindow

    app = QApplication([sys.argv[0]])
    app.setApplicationName("DocDiff")
    app.setOrganizationName("DocDiff")
    app.setFont(theme.app_font())
    app.setStyleSheet(theme.STYLESHEET)
    engine = create_engine(force_stub="--stub" in argv)
    window = MainWindow(engine, SettingsStore(), HotkeyManager(app))
    window.show()
    return app.exec()
