from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QRunnable, QObject, QThreadPool, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from docdiff import strings
from docdiff.diffing import diff_texts
from docdiff.ocr.base import OcrEngine
from docdiff.pipeline import image_to_text
from docdiff.platform_win import IS_WINDOWS
from docdiff.settings import AppSettings, SettingsStore
from docdiff.ui.diff_view import DiffView
from docdiff.ui.hotkeys import HotkeyManager
from docdiff.ui.overlay import CaptureController
from docdiff.ui.panel import Panel
from docdiff.ui import theme
from docdiff.ui.settings_dialog import SettingsDialog

HIDE_DELAY_MS = 300  # let the window finish disappearing before the screenshot


class _OcrSignals(QObject):
    done = Signal(str, int, str, bool)  # side, region id, text, language_fallback
    failed = Signal(str, int, str)


class _OcrJob(QRunnable):
    def __init__(self, engine: OcrEngine, side: str, rid: int, image: Image.Image, signals: _OcrSignals):
        super().__init__()
        self.engine, self.side, self.rid, self.image, self.signals = engine, side, rid, image, signals

    def run(self) -> None:
        try:
            out = image_to_text(self.engine, self.image)
        except Exception as exc:  # shown to the user, never crash the worker
            self.signals.failed.emit(self.side, self.rid, str(exc) or type(exc).__name__)
        else:
            self.signals.done.emit(self.side, self.rid, out.text, out.language_fallback)


class MainWindow(QMainWindow):
    def __init__(self, engine: OcrEngine, store: SettingsStore, hotkeys: HotkeyManager | None = None, show_dialogs: bool = True):
        super().__init__()
        self.engine = engine
        self.store = store
        self.settings: AppSettings = store.load()
        theme.set_theme(str(store.q.value("theme", theme.current())))
        self.show_dialogs = show_dialogs
        self.setWindowTitle(strings.WINDOW_TITLE)
        self.resize(1200, 760)
        geometry = store.load_geometry()
        if geometry:
            self.restoreGeometry(geometry)

        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)  # FIFO: appended captures keep their order
        self._signals = _OcrSignals(self)
        self._signals.done.connect(self._on_ocr_done)
        self._signals.failed.connect(self._on_ocr_failed)

        self.capture = CaptureController(self)
        self.capture.captured.connect(self._on_captured)
        self.capture.cancelled.connect(self._on_cancelled)
        self.capture.failed.connect(self._on_capture_failed)
        self._pending_capture: tuple[str, bool] | None = None
        self._capture_busy = False
        self.last_result = None

        self.panels = {"A": Panel("A", strings.PANEL_A_TITLE), "B": Panel("B", strings.PANEL_B_TITLE)}
        for p in self.panels.values():
            p.capture_requested.connect(self.start_capture)
            p.text_changed.connect(self._update_compare_enabled)

        self.btn_compare = QPushButton(strings.BTN_COMPARE)
        self.btn_compare.setObjectName("primary")
        self.btn_compare.setEnabled(False)
        self.btn_compare.clicked.connect(self.compare)
        self.btn_settings = QPushButton(strings.BTN_SETTINGS)
        self.btn_settings.clicked.connect(self.open_settings)

        self.banner = QLabel("")
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        self.banner_box = QFrame()
        self.banner_box.setObjectName("bannerBox")
        tag = QLabel(strings.DEMO_TAG.upper())
        tag.setObjectName("bannerTag")
        bl = QHBoxLayout(self.banner_box)
        bl.setContentsMargins(10, 6, 10, 6)
        bl.addWidget(tag, 0, Qt.AlignTop)
        bl.addWidget(self.banner, 1)
        self.banner_box.setVisible(False)

        self.btn_theme = QPushButton()
        self.btn_theme.clicked.connect(self.toggle_theme)
        self._refresh_theme_button()
        brand = QLabel(strings.APP_NAME)
        brand.setObjectName("brand")
        sub = QLabel(strings.APP_SUBTITLE)
        sub.setObjectName("brandSub")
        nav = QFrame()
        nav.setObjectName("nav")
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(20, 8, 20, 8)
        nl.addWidget(brand)
        nl.addWidget(sub, 1)
        nl.addWidget(self.btn_theme)
        nl.addWidget(self.btn_settings)

        self.diff_view = DiffView(self.panels["A"].diff, self.panels["B"].diff)
        self.btn_back = QPushButton(strings.BTN_EDIT)
        self.btn_back.clicked.connect(self.back_to_edit)
        self.hint = QLabel(strings.HINT_ADD_TEXT)
        self.hint.setObjectName("railHint")
        self.hint.setWordWrap(True)
        self.hint.setAlignment(Qt.AlignCenter)
        self.diff_view.setVisible(False)
        self.btn_back.setVisible(False)
        rail = QWidget()
        rail.setFixedWidth(168)
        middle = QVBoxLayout(rail)
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(14)
        middle.addStretch(1)
        middle.addWidget(self.btn_compare)
        middle.addWidget(self.hint)
        middle.addWidget(self.diff_view)
        middle.addWidget(self.btn_back)
        middle.addStretch(1)
        row = QHBoxLayout()
        row.setSpacing(27)
        row.addWidget(self.panels["A"], 1)
        row.addWidget(rail)
        row.addWidget(self.panels["B"], 1)
        page = QWidget()
        edit_lay = QVBoxLayout(page)
        edit_lay.setContentsMargins(0, 0, 0, 0)
        edit_lay.addWidget(self.banner_box)
        edit_lay.addLayout(row, 1)
        self.stack = page
        self.in_result = False

        central = QWidget()
        central.setObjectName("central")
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(nav)
        body = QVBoxLayout()
        body.setContentsMargins(20, 27, 20, 20)
        body.addWidget(self.stack)
        outer.addLayout(body, 1)
        self.setCentralWidget(central)

        self.hotkeys = hotkeys
        if hotkeys is not None:
            hotkeys.triggered.connect(lambda side: self.start_capture(side, False))
            self.apply_hotkeys()
        self._show_engine_notices()

    # --- theme ------------------------------------------------------
    def _refresh_theme_button(self) -> None:
        self.btn_theme.setText(strings.THEME_TO_LIGHT if theme.current() == "dark" else strings.THEME_TO_DARK)

    def toggle_theme(self) -> None:
        theme.set_theme("light" if theme.current() == "dark" else "dark")
        self.store.q.setValue("theme", theme.current())
        QApplication.instance().setStyleSheet(theme.build_stylesheet())
        self._refresh_theme_button()
        if self.last_result is not None:
            self.diff_view.show_result(self.last_result)

    # --- notices ----------------------------------------------------
    def show_banner(self, message: str) -> None:
        self.banner.setText(message if not self.banner_box.isVisible() else self.banner.text() + "\n\n" + message)
        self.banner_box.setVisible(True)

    def _notify(self, message: str, error: bool = False) -> None:
        if self.show_dialogs:
            box = QMessageBox.critical if error else QMessageBox.warning
            box(self, strings.MSG_TITLE_ERROR if error else strings.MSG_TITLE_WARNING, message)

    def _show_engine_notices(self) -> None:
        if not self.engine.is_real:
            self.show_banner(strings.INFO_STUB_MODE if IS_WINDOWS is False else strings.ERR_OCR_UNAVAILABLE)
        elif self.engine.language_fallback:
            self._language_missing_notice()

    def _language_missing_notice(self) -> None:
        if self.banner.text().find(strings.ERR_OCR_LANG_MISSING) < 0:
            self.show_banner(strings.ERR_OCR_LANG_MISSING)
            QTimer.singleShot(0, lambda: self._notify(strings.ERR_OCR_LANG_MISSING))

    # --- hotkeys ----------------------------------------------------
    def apply_hotkeys(self) -> None:
        if self.hotkeys is None:
            return
        errors = self.hotkeys.apply(self.settings.hotkey_a, self.settings.hotkey_b)
        for text, code in errors.items():
            if code == "in_use":
                msg = strings.ERR_HOTKEY_IN_USE.format(hotkey=text)
            elif code == "unsupported":
                msg = strings.ERR_HOTKEYS_UNSUPPORTED
                if msg in self.banner.text():
                    continue
            else:
                msg = strings.ERR_HOTKEY_INVALID.format(hotkey=text)
            self.show_banner(msg)

    # --- capture ----------------------------------------------------
    def start_capture(self, side: str, append: bool) -> None:
        if self._capture_busy:
            return
        self._capture_busy = True
        self._pending_capture = (side, append)
        self.hide()
        QTimer.singleShot(HIDE_DELAY_MS, self.capture.start)

    def _restore_window(self) -> None:
        self._capture_busy = False
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_cancelled(self) -> None:
        side, _ = self._pending_capture or ("A", False)
        self._restore_window()
        self.panels[side].set_status(strings.ERR_CAPTURE_CANCELLED, "warn")

    def _on_capture_failed(self, detail: str) -> None:
        side, _ = self._pending_capture or ("A", False)
        self._restore_window()
        self.panels[side].set_status(strings.ERR_CAPTURE_FAILED.format(detail=detail), "error")

    def _on_captured(self, image: Image.Image) -> None:
        side, append = self._pending_capture or ("A", False)
        self._restore_window()
        self.submit_image(side, image, replace=not append)

    def submit_image(self, side: str, image: Image.Image, replace: bool = True) -> int:
        """Register a captured image on a panel and queue OCR for it."""
        panel = self.panels[side]
        rid = panel.begin_region(image, replace)
        self.pool.start(_OcrJob(self.engine, side, rid, image, self._signals))
        return rid

    def _on_ocr_done(self, side: str, rid: int, text: str, fallback: bool) -> None:
        self.panels[side].finish_region(rid, text)
        if fallback:
            self._language_missing_notice()

    def _on_ocr_failed(self, side: str, rid: int, detail: str) -> None:
        self.panels[side].fail_region(rid, strings.ERR_OCR_FAILED.format(detail=detail))

    def wait_for_ocr(self, timeout_ms: int = 30000) -> bool:
        """Block until queued OCR jobs finish (used by tests / self-test)."""
        from PySide6.QtWidgets import QApplication

        ok = self.pool.waitForDone(timeout_ms)
        QApplication.processEvents()
        return ok

    # --- compare / settings -------------------------------------------
    def _update_compare_enabled(self) -> None:
        ok = all(p.has_text() for p in self.panels.values())
        self.btn_compare.setEnabled(ok)
        self.hint.setVisible(not ok and not self.in_result)

    def compare(self) -> None:
        a, b = self.panels["A"].text(), self.panels["B"].text()
        if not (a.strip() and b.strip()):
            self.panels["A"].set_status(strings.ERR_COMPARE_EMPTY, "warn")
            return
        self.last_result = diff_texts(a, b, self.settings.compare_options)
        self.diff_view.show_result(self.last_result)
        self._set_result_mode(True)

    def _set_result_mode(self, on: bool) -> None:
        self.in_result = on
        for p in self.panels.values():
            p.set_result_mode(on)
        self.btn_compare.setVisible(not on)
        self.hint.setVisible(not on and not self.btn_compare.isEnabled())
        self.diff_view.setVisible(on)
        self.btn_back.setVisible(on)

    def back_to_edit(self) -> None:
        self._set_result_mode(False)

    def open_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() and dlg.result_settings:
            self.settings = dlg.result_settings
            self.store.save(self.settings)
            self.apply_hotkeys()

    def closeEvent(self, event) -> None:
        self.store.save_geometry(self.saveGeometry())
        if self.hotkeys is not None:
            self.hotkeys.shutdown()
        super().closeEvent(event)
