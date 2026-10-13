# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DocDiff: a Windows desktop app (PySide6) that captures two on-screen regions, OCRs them with the built-in Windows OCR (pywinrt), and shows a word/table-row diff. The UI is entirely Greek (all strings in `docdiff/strings.py`); documents may be Greek, English or mixed. It is developed on macOS/Linux using a stub OCR engine; the real engine only runs on Windows.

## Commands

```bash
pip install -r requirements-dev.txt
python -m docdiff                  # real OCR on Windows, stub OCR elsewhere
python -m docdiff --stub           # force stub OCR
python -m pytest                   # all tests (offscreen Qt is set in tests/conftest.py)
python -m pytest tests/test_diff.py::test_name   # single test
python -m docdiff --selftest out.txt   # real OCR on a generated image + headless UI check
python tools/build_exe.py          # Windows only: PyInstaller one-file windowed exe -> dist/DocDiff.exe
python tools/make_fixtures.py      # regenerate docdiff/fixtures/*.json used by the stub OCR
```

No linter is configured. Tests marked `windows_ocr` only run on Windows.

## Architecture

Data flow (text mode; image mode skips OCR and goes straight to `imagediff.compare_images`): `capture.py` (mss screenshots) / `ui/overlay.py` (region selection) -> `imaging.preprocess` -> `ocr/` engine -> `layout.reconstruct_text` -> user-editable text boxes -> `normalize` + `diffing` -> `ui/diff_view.py`. `pipeline.image_to_text` is the glue from image to text.

- **OCR abstraction** (`docdiff/ocr/`): `OcrEngine` interface returns word boxes + language; `WindowsOcrEngine` (winrt), `StubOcrEngine` (canned fixtures, picks by `synthetic.py`), non-Windows default. Layout is reconstructed from word boxes, not from OCR's own line output.
- **Layout** (`layout.py`): words -> rows -> columns/cells -> table rows rendered as `a | b | c`, or multi-column prose read column by column. Thresholds are heuristics tuned on synthetic fixtures.
- **Diff** (`diffing.py`, `normalize.py`): if both texts contain ` | ` table rows, lines are aligned and paired rows are diffed cell by cell; otherwise a flat word diff (`difflib.SequenceMatcher` on normalised keys). Normalisation strips Greek accents and folds final sigma, but display text is never altered.
- **Platform code** (`platform_win.py`): DPI v2 and `RegisterHotKey`, guarded to no-op off Windows. Hotkeys come via a Qt native event filter for `WM_HOTKEY`.
- **Overlay**: screenshots all monitors after hiding the main window, crop computed by ratio of screenshot pixels to widget size (DPI independent); Qt screens matched to mss monitors by geometry.
- **Image mode** (`imagediff.py`): second mode toggled in the header; skips OCR and compares the two captures as images (ORB+RANSAC alignment, content-masked SSIM, changed-region boxes/heat map). Pure numpy/opencv + PIL, no Qt; run on the same worker pool via `_ImageJob`. Both modes report a similarity % (`DiffStats.similarity` / `ImageDiffResult.similarity`).
- **Multiple regions**: a single FIFO OCR worker thread keeps appended captures in order.

## Gotchas

- Import Qt before any `winrt` module, otherwise an access violation on Windows (guarded in `docdiff/ocr/windows.py`).
- pywinrt uses snake_case names, e.g. `BitmapDecoder.get_software_bitmap_converted_async(format, alpha)`.
- CI (`.github/workflows/build.yml`) only has the `en-US` OCR language on windows-latest, so Greek OCR is never tested there; the frozen exe is verified with `DocDiff.exe --selftest` (real OCR + headless UI), not just built. Selftest must tolerate non-UTF8 consoles.
- Behavioural decisions, known limitations and the manual Windows test checklist are in `NOTES.md`; read it before changing layout/diff/overlay behaviour.
