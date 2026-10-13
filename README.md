# DocDiff

Windows desktop app that compares the text of two on-screen regions. Open two documents in a browser
(PDF, or a Word document in a web viewer), select a rectangle of each, and DocDiff reads the text with the
built-in Windows OCR and shows the differences side by side. The UI is entirely in Greek; documents may be
Greek, English or mixed. Tables and multi-column layouts are reconstructed from OCR word boxes so that table
rows are compared as rows.

## Download the .exe

Every push runs the GitHub Actions workflow `build` (`.github/workflows/build.yml`). Open the repository's
**Actions** tab, pick the latest green run and download the artifact **DocDiff-windows-exe** (a zip containing
`DocDiff.exe`). It is a single file with no installer or setup; just double-click it.

## Run in development

```bash
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m docdiff            # real OCR on Windows, stub OCR elsewhere
python -m docdiff --stub     # force the stub OCR engine
python -m pytest             # unit tests (the Windows OCR smoke test only runs on Windows)
python -m docdiff --selftest out.txt   # OCR on a generated image + headless UI check
python tools/build_exe.py    # Windows only: builds dist/DocDiff.exe
```

On Linux/macOS the app starts in *stub mode*: OCR returns canned fixtures from `docdiff/fixtures`, global
hotkeys are disabled and DPI code is skipped. Linux needs `libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3`
for Qt (use `QT_QPA_PLATFORM=offscreen` for headless runs).

## Layout

| Path | Purpose |
| --- | --- |
| `docdiff/ocr/` | `OcrEngine` interface, `WindowsOcrEngine` (pywinrt), `StubOcrEngine`, synthetic fixtures |
| `docdiff/layout.py` | words -> rows, columns, table rows (`a \| b \| c`), paragraph merging |
| `docdiff/normalize.py`, `docdiff/diffing.py` | Greek-aware normalisation, word diff, row-by-row table diff |
| `docdiff/capture.py`, `docdiff/imaging.py` | mss capture, preprocessing |
| `docdiff/platform_win.py` | per-monitor DPI v2, RegisterHotKey helpers (guarded off Windows) |
| `docdiff/ui/` | PySide6 window, overlay, panels, diff view, settings |
| `docdiff/strings.py` | all Greek UI strings |

## How the GitHub Actions build works

The `windows` job (windows-latest): installs dependencies, runs the full pytest suite (including a smoke test that renders Greek and English text with Pillow and OCRs it with
the real Windows engine; the hosted runner only has English OCR, so Greek is skipped with a logged warning and English is checked), runs
`python -m docdiff --selftest`, builds the one-file windowed exe with PyInstaller (`tools/build_exe.py`, which
collects the `winrt` packages), then runs `DocDiff.exe --selftest` to prove the winrt projections and Qt are bundled
correctly, and uploads `DocDiff.exe`. A `linux-stub` job runs the tests in stub mode.

## Install the Greek OCR language on Windows

1. Open **Settings > Time & language > Language & region**.
2. Click **Add a language**, choose **Ελληνικά (Greek)**, and keep the **Optical character recognition** (and
   *Basic typing*) features ticked.
3. Wait for the download to finish, then restart DocDiff.

Without it the app shows a Greek message and falls back to the OCR languages of your Windows profile. Admins can
also run, in an elevated PowerShell: `Add-WindowsCapability -Online -Name "Language.OCR~~~el-GR~0.0.1.0"`.

## Usage

1. Press **Λήψη περιοχής** (or Ctrl+Alt+A / Ctrl+Alt+B) for document A or B and drag a rectangle; Esc cancels.
2. Use **Προσθήκη περιοχής** to append more regions (e.g. while scrolling). Remove any with its thumbnail button.
3. Fix OCR mistakes in the text boxes, then press **Σύγκριση**.
