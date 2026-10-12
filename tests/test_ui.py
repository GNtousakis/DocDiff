import pytest
from PIL import Image
from PySide6.QtCore import QCoreApplication, QEvent, QSettings
from PySide6.QtWidgets import QApplication

from docdiff import strings
from docdiff.ocr import StubOcrEngine
from docdiff.ocr.base import OcrError, OcrEngine
from docdiff.settings import AppSettings, SettingsStore
from docdiff.ui.main_window import MainWindow
from docdiff.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    for w in _windows:
        w.pool.waitForDone(5000)
        w.close()
        w.deleteLater()
    _windows.clear()
    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


@pytest.fixture
def store(tmp_path):
    return SettingsStore(QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat))


_windows = []


def make_window(qapp, store, engine=None):
    w = MainWindow(engine or StubOcrEngine(["table_v1", "table_v2"]), store, hotkeys=None, show_dialogs=False)
    _windows.append(w)
    return w


IMG = Image.new("RGB", (200, 80), "white")


def test_compare_disabled_until_both_sides_have_text(qapp, store):
    w = make_window(qapp, store)
    assert not w.btn_compare.isEnabled()
    w.submit_image("A", IMG)
    w.wait_for_ocr()
    assert w.panels["A"].has_text() and not w.btn_compare.isEnabled()
    w.submit_image("B", IMG)
    w.wait_for_ocr()
    assert w.btn_compare.isEnabled()


def test_compare_shows_summary_and_highlights(qapp, store):
    w = make_window(qapp, store)
    w.submit_image("A", IMG)
    w.submit_image("B", IMG)
    w.wait_for_ocr()
    w.compare()
    assert w.stack.currentIndex() == 1
    assert "2" in w.diff_view.summary.text()
    assert w.last_result.stats.changed == 2


def test_edit_text_before_compare(qapp, store):
    w = make_window(qapp, store)
    w.submit_image("A", IMG)
    w.submit_image("B", IMG)
    w.wait_for_ocr()
    w.panels["B"].edit.setPlainText(w.panels["A"].text())
    w.compare()
    assert w.last_result.stats.total == 0
    assert w.diff_view.summary.text() == strings.SUMMARY_IDENTICAL


def test_append_and_remove_regions(qapp, store):
    w = make_window(qapp, store, StubOcrEngine(["greek", "english"]))
    p = w.panels["A"]
    w.submit_image("A", IMG, replace=True)
    w.wait_for_ocr()
    first = p.text()
    w.submit_image("A", IMG, replace=False)
    w.wait_for_ocr()
    assert len(p.regions) == 2
    assert p.text().startswith(first) and "The company" in p.text()
    p.remove_region(p.regions[1].rid)
    assert p.text() == first and len(p.regions) == 1
    w.submit_image("A", IMG, replace=True)  # replace drops old regions
    w.wait_for_ocr()
    assert len(p.regions) == 1


def test_remove_edited_region_warns(qapp, store):
    w = make_window(qapp, store)
    p = w.panels["A"]
    w.submit_image("A", IMG)
    w.wait_for_ocr()
    p.edit.setPlainText("totally different")
    p.remove_region(p.regions[0].rid)
    assert p.status.text() == strings.ERR_REMOVE_EDITED and p.text() == "totally different"


def test_no_text_message(qapp, store):
    from docdiff.ocr.base import OcrResult

    w = make_window(qapp, store, StubOcrEngine(OcrResult()))
    w.submit_image("A", IMG)
    w.wait_for_ocr()
    assert w.panels["A"].status.text() == strings.ERR_NO_TEXT


def test_ocr_failure_message(qapp, store):
    class Boom(OcrEngine):
        def recognize(self, image):
            raise OcrError("kaboom")

    w = make_window(qapp, store, Boom())
    w.submit_image("A", IMG)
    w.wait_for_ocr()
    assert "kaboom" in w.panels["A"].status.text() and not w.panels["A"].regions


def test_stub_mode_banner_shown(qapp, store):
    w = make_window(qapp, store)
    w.show()
    assert w.banner.isVisible()


def test_language_fallback_banner(qapp, store):
    class Fallback(StubOcrEngine):
        is_real = True
        language_fallback = True

    w = make_window(qapp, store, Fallback("greek"))
    assert strings.ERR_OCR_LANG_MISSING in w.banner.text()
    assert "Add a language" in strings.ERR_OCR_LANG_MISSING


def test_settings_roundtrip(qapp, store):
    assert store.load() == AppSettings()
    s = AppSettings("Ctrl+Shift+X", "Ctrl+Shift+Y", False, False)
    store.save(s)
    assert store.load() == s


def test_settings_dialog_validation(qapp, store):
    dlg = SettingsDialog(AppSettings(), None)
    assert dlg.edit_a.keySequence().toString() == "Ctrl+Alt+A"
    assert dlg.chk_case.isChecked() and dlg.chk_punct.isChecked()


def test_options_applied_in_compare(qapp, store):
    store.save(AppSettings(ignore_case=False))
    w = make_window(qapp, store)
    assert not w.settings.compare_options.ignore_case


def test_geometry_remembered(qapp, store):
    w = make_window(qapp, store)
    w.show()
    w.resize(760, 520)
    size = (w.width(), w.height())  # the platform may enforce a larger minimum
    w.close()
    w2 = make_window(qapp, store)
    w2.show()
    assert (w2.width(), w2.height()) == size
