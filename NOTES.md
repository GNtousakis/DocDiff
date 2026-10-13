# Notes

## Decisions

- **Diff engine**: `difflib.SequenceMatcher` on normalised word keys (no extra dependency). Counts are per *difference block*:
  an inserted run is one addition, a deleted run one deletion, a replaced run one change. A whole added/removed table row counts as one.
- **Normalisation**: NFC, accents/diacritics stripped (NFD minus combining marks), final sigma ς -> σ always, case-folding if "ignore case", punctuation removed if
  "ignore punctuation" (except `.`/`,` between digits so `1,20` != `12,0`). Display text is never altered. A lone `|` is never compared.
- **Tables**: if both texts contain table rows (` | `), lines are aligned (exact match, then similarity DP inside changed blocks) and paired rows are
  diffed cell by cell (when cell counts match). Otherwise a flat word diff is used, so reflowed paragraphs never show differences.
- **Layout heuristics** (`docdiff/layout.py`): rows from vertical clustering; cells/columns split by a gap > 1.5x median word height; consecutive
  rows sharing gutters form a block; a block with a median >= 8 words per cell is treated as multi-column prose (read column by column), otherwise as a table.
  Paragraphs merge unless there is a larger vertical gap, a short previous line, indentation or list marker; hyphenated line ends are re-joined.
- **OCR language**: Greek engine preferred (also reads Latin text, so mixed text uses one pass); fallback = user profile languages + Greek banner/dialog.
- **Overlay**: screenshots of all monitors are taken after the main window is hidden (300 ms), shown dimmed in one frameless window per monitor, and the
  crop is computed from the ratio screenshot pixels / widget size, so it is DPI independent. Qt screens are matched to mss monitors by geometry.
- **Hotkeys**: `RegisterHotKey` (thread queue) with a Qt native event filter for `WM_HOTKEY`; no hooks. Settings use `QKeySequenceEdit`.
- **Multiple regions**: one OCR worker thread (FIFO) keeps appended captures in order. Removing a region deletes its original text from the box; if the
  user already edited that text a Greek warning asks them to delete it manually.
- **Similarity %**: text mode = `2 * matched words / (words A + words B)` (`DiffStats.similarity`; table cells are counted word by word). Image mode =
  mean SSIM over the *content area* only (dilated ink of A or B, theme independent), so white page background does not inflate the score. Shown as
  `100%` only when nothing differs, otherwise rounded down (never `100.0%` for a non-identical pair).
- **Image mode** (`docdiff/imagediff.py`, no Qt): ORB features + RANSAC `estimateAffinePartial2D` (shift/scale/small rotation, not a homography - captures
  are flat and a homography can warp wrongly on repetitive text/tables) aligns B onto A; rejected when too few inliers, scale outside 0.25-4x or rotation > 10 deg,
  then B is simply stretched to A's size and a warning is shown. Then blur -> SSIM -> threshold -> morphology -> boxes + red heat overlay. Both images are
  capped at 2400 px. Sensitivity (Settings) selects threshold/min-area presets.
- **Image mode UI**: mode toggle in the header (persisted as `mode`); one image per side (capture replaces, no "add region", no OCR). Text and image contents
  of a panel are independent and both survive a mode switch. The comparison runs on the same single worker pool.
- **CI**: the frozen exe is verified with `DocDiff.exe --selftest` (real OCR + headless UI), not only built.

## CI findings

- The windows-latest runner only has the `en-US` OCR language; `Add-WindowsCapability Language.OCR~~~el-GR` ran ~10 min without installing it, so the step was
  removed. **Greek OCR is therefore never exercised in CI** - verify it manually on a machine with Greek OCR installed.
- Qt must be imported before any `winrt` module (otherwise an access violation on Windows); guarded in `docdiff/ocr/windows.py`.
- pywinrt method names: `BitmapDecoder.get_software_bitmap_converted_async(format, alpha)`.

## Known limitations

- Wrapped table cells (cell text on two physical lines) become extra rows with empty cells; a trailing row with a single filled cell is read as a paragraph.
- Overlapping scroll captures are not de-duplicated; appended text is just joined.
- Scroll sync is proportional, not line-aligned.
- Mixed Greek/English uses the Greek engine only; Latin text is read by it but accuracy may differ from the English engine.
- Thresholds in `layout.py` are tuned on synthetic fixtures; real documents may need adjustment.
- Hotkey conflict is reported at startup / after changing settings; hotkeys do not work while an elevated window has focus.

- Image mode: very different zoom/perspective (photos of paper), or crops with almost no texture (blank areas), fall back to a plain resize; a different
  font rendering / ClearType colour fringes can lower the score slightly even for the same text.

## Please test manually on Windows first

1. Overlay on multi-monitor setups (different resolutions, monitor left of / above the primary): the selected rectangle must match the captured pixels.
2. DPI scaling 125%, 150%, and mixed-DPI monitors.
3. Global hotkeys while the app is minimised/hidden, and the "already in use" message (try a combination used by another app).
4. OCR quality on real Greek PDFs/Word web viewers, with and without the Greek OCR language installed.
5. Table/multi-column reconstruction on real documents.
6. SmartScreen: the unsigned exe may show a warning on first start.
7. Image mode: capture the same page twice with a slightly different selection (shift/zoom) -> ~100%, no boxes; edit one word -> one box around it;
   toggle heat map and dark theme; check the frozen exe's `--selftest` reports `image: OK`.
