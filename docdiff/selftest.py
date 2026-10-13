"""Self-test: real OCR on a generated Greek/English image, then a headless UI start.

Used by CI against both the source tree and the frozen .exe (``DocDiff.exe --selftest out.txt``).
Exit code 0 = OK. Greek OCR missing is only a warning (English is checked instead).
"""
from __future__ import annotations

import os
import tempfile
import sys
import traceback

from PIL import Image, ImageDraw, ImageFont

from docdiff.normalize import normalize_word

ENGLISH_LINES = ["Quarterly report invoice total", "Payment delivery agreement"]
GREEK_LINES = ["Καλημέρα κόσμε σύμβαση παράδοση", "Πληρωμή εταιρεία προϊόντα"]
_FONTS = [
    "arial.ttf", "segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
    "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for name in _FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise RuntimeError("no TrueType font with Greek support found")


def render_lines(lines: list[str], size: int = 40) -> Image.Image:
    font = load_font(size)
    img = Image.new("RGB", (1100, 40 + len(lines) * int(size * 1.8)), "white")
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((30, 20 + i * int(size * 1.8)), line, fill="black", font=font)
    return img


def keywords_found(text: str, lines: list[str], minimum: int = 3) -> tuple[bool, list[str], list[str]]:
    wanted = [normalize_word(w) for ln in lines for w in ln.split()]
    got = {normalize_word(w) for w in text.split()}
    found = [w for w in wanted if w in got]
    missing = [w for w in wanted if w not in got]
    return len(found) >= minimum, found, missing


def check_ocr(log) -> bool:
    from docdiff.ocr import windows
    from docdiff.pipeline import image_to_text

    if not windows.is_supported():
        log("SKIP: Windows OCR not available on this platform")
        return True
    engine = windows.WindowsOcrEngine()
    log(f"OCR language: {engine.language_tag} (greek fallback: {engine.language_fallback})")
    try:
        log(f"Installed OCR languages: {windows.available_language_tags()}")
    except Exception as exc:  # informational only
        log(f"could not list OCR languages: {exc}")
    ok = True
    raw = engine.recognize(render_lines(ENGLISH_LINES))
    if not raw.words:
        log("FAIL: no word boxes returned")
        return False
    out = image_to_text(engine, render_lines(ENGLISH_LINES))
    good, found, missing = keywords_found(out.text, ENGLISH_LINES)
    log(f"English text: {out.text!r} found={found} missing={missing}")
    ok &= good
    if engine.language_fallback or not (engine.language_tag or "").lower().startswith("el"):
        log("WARNING: Greek OCR language is not installed; Greek check skipped")
    else:
        out = image_to_text(engine, render_lines(GREEK_LINES))
        good, found, missing = keywords_found(out.text, GREEK_LINES)
        log(f"Greek text: {out.text!r} found={found} missing={missing}")
        ok &= good
    return bool(ok)


def check_ui(log) -> bool:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    from docdiff.ocr import StubOcrEngine
    from docdiff.settings import SettingsStore
    from docdiff.ui import theme
    from docdiff.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setStyleSheet(theme.STYLESHEET)
    store = SettingsStore(QSettings(os.path.join(tempfile.gettempdir(), "docdiff-selftest.ini"), QSettings.IniFormat))
    win = MainWindow(StubOcrEngine(["table_v1", "table_v2"]), store, hotkeys=None, show_dialogs=False)
    win.show()
    win.submit_image("A", Image.new("RGB", (300, 100), "white"))
    win.submit_image("B", Image.new("RGB", (300, 100), "white"))
    win.wait_for_ocr()
    win.compare()
    stats = win.last_result.stats
    log(f"UI compare summary: added={stats.added} removed={stats.removed} changed={stats.changed}")
    win.close()
    win.deleteLater()
    app.processEvents()
    return stats.changed == 2 and stats.added == 0 and stats.removed == 0


def check_image(log) -> bool:
    """Image diff end to end (verifies numpy/opencv are bundled and ORB alignment works)."""
    from docdiff.imagediff import compare_images

    def page(lines: list[str]) -> Image.Image:
        img = Image.new("RGB", (900, 300), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default(size=32)  # no system font needed
        for i, line in enumerate(lines):
            draw.text((30, 20 + i * 60), line, fill="black", font=font)
        return img

    lines = ENGLISH_LINES + ["Customer reference number 88231"]
    a = page(lines)
    b = page(lines[:2] + ["Customer reference number 99999"])
    same = compare_images(a, a.copy())
    changed = compare_images(a, b)
    log(f"Image diff: identical={same.similarity:.1f}% changed={changed.similarity:.1f}% "
        f"boxes={len(changed.boxes)} aligned={changed.aligned}")
    return same.similarity > 99 and not same.boxes and changed.similarity < same.similarity and bool(changed.boxes)


def run_selftest(out_path: str | None = None) -> int:
    import faulthandler

    import PySide6.QtWidgets  # noqa: F401  (must load before winrt, see ocr/windows.py)

    out = open(out_path, "w", encoding="utf-8", buffering=1) if out_path else None
    if out:
        faulthandler.enable(out)

    def log(msg: str) -> None:
        if out:
            out.write(msg + "\n")
            out.flush()
        if sys.stdout:
            try:
                print(msg, flush=True)
            except UnicodeEncodeError:  # legacy Windows console code page
                print(msg.encode("ascii", "backslashreplace").decode(), flush=True)

    ok = True
    for name, fn in (("ocr", check_ocr), ("ui", check_ui), ("image", check_image)):
        try:
            if name == "ocr":  # same threading model as the app: OCR on a worker thread
                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor(1) as ex:
                    res = ex.submit(fn, log).result()
            else:
                res = fn(log)
        except Exception:
            log(f"EXCEPTION in {name}:\n{traceback.format_exc()}")
            res = False
        log(f"{name}: {'OK' if res else 'FAILED'}")
        ok &= bool(res)
    if out:
        out.close()
    return 0 if ok else 1
