"""Diff result helpers: segment rendering, synchronised scrolling and the summary column in the middle rail."""
from __future__ import annotations

import math

from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from docdiff import strings
from docdiff.diffing import ADDED, CHANGED, REMOVED, DiffResult, Segment
from docdiff.imagediff import ImageDiffResult
from docdiff.ui import theme


def render_segments(edit: QTextEdit, segments: list[Segment]) -> None:
    edit.clear()
    cursor = QTextCursor(edit.document())
    for seg in segments:
        cursor.insertText(seg.text, theme.format_for(seg.kind))


def format_similarity(value: float, perfect: bool) -> str:
    """'100%' only when nothing differs; otherwise round down so near-misses never read as 100."""
    if perfect:
        return strings.SIMILARITY_FMT.format(pct="100")
    v = min(math.floor(max(value, 0.0) * 10) / 10, 99.9)
    return strings.SIMILARITY_FMT.format(pct=f"{v:.1f}")


def _similarity_block() -> tuple[QWidget, QLabel]:
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    caption = QLabel(strings.SIMILARITY_CAPTION.upper())
    caption.setObjectName("similarityCaption")
    value = QLabel("")
    value.setObjectName("similarity")
    lay.addWidget(caption)
    lay.addWidget(value)
    return box, value


def _count_row(label: str, swatch: str | None = None) -> tuple[QFrame, QLabel]:
    row = QFrame()
    row.setObjectName("summaryRow")
    name = QLabel(label)
    name.setObjectName("summaryName")
    num = QLabel("0")
    num.setObjectName("summaryNum")
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 7)
    lay.setSpacing(6)
    if swatch:
        sw = QLabel()
        sw.setObjectName(swatch)
        sw.setFixedSize(10, 10)
        lay.addWidget(sw)
    lay.addWidget(name, 1)
    lay.addWidget(num)
    return row, num


class ImageSummary(QWidget):
    """Middle-rail summary for image mode: similarity %, number of changed regions, heat-map switch."""

    heat_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        block, self.value = _similarity_block()
        self.regions_row, self.regions = _count_row(strings.LEGEND_REGIONS, "swatch_changed")
        self.note = QLabel("")
        self.note.setObjectName("summaryNote")
        self.note.setWordWrap(True)
        self.chk_heat = QCheckBox(strings.CHK_HEAT)
        self.chk_heat.setChecked(True)
        self.chk_heat.toggled.connect(self.heat_toggled)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)
        lay.addWidget(block)
        lay.addWidget(self.regions_row)
        lay.addWidget(self.chk_heat)
        lay.addWidget(self.note)

    def heat_enabled(self) -> bool:
        return self.chk_heat.isChecked()

    def show_result(self, result: ImageDiffResult) -> None:
        identical = not result.boxes and result.similarity >= 99.95
        self.value.setText(format_similarity(result.similarity, identical))
        self.regions.setText(str(result.regions))
        note = {"resized": strings.WARN_IMAGE_RESIZED, "aspect": strings.WARN_IMAGE_ASPECT}.get(result.warning or "", "")
        if not note and identical:
            note = strings.SUMMARY_IMAGES_IDENTICAL
        self.note.setText(note)


class DiffView(QWidget):
    """Summary rows (deletions / additions / changes) plus scroll sync between the two diff boxes."""

    def __init__(self, left: QTextEdit, right: QTextEdit, parent=None):
        super().__init__(parent)
        self.left, self.right = left, right
        self._syncing = False
        left.verticalScrollBar().valueChanged.connect(lambda v: self._sync(left, right))
        right.verticalScrollBar().valueChanged.connect(lambda v: self._sync(right, left))

        self.summary = QLabel("")  # "texts are identical" message
        self.summary.setObjectName("summaryNote")
        self.summary.setWordWrap(True)
        self.counts: dict[str, QLabel] = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(7)
        block, self.similarity = _similarity_block()
        lay.addWidget(block)
        for kind, label in ((REMOVED, strings.LEGEND_REMOVED_ROW), (ADDED, strings.LEGEND_ADDED_ROW), (CHANGED, strings.LEGEND_CHANGED_ROW)):
            lay.addWidget(self._row(kind, label))
        lay.addWidget(self.summary)

    def _row(self, kind: str, label: str) -> QFrame:
        row = QFrame()
        row.setObjectName("summaryRow")
        swatch = QLabel()
        swatch.setObjectName(f"swatch_{kind}")
        swatch.setFixedSize(10, 10)
        name = QLabel(label)
        name.setObjectName("summaryName")
        num = QLabel("0")
        num.setObjectName("summaryNum")
        self.counts[kind] = num
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 7)
        lay.setSpacing(6)
        lay.addWidget(swatch)
        lay.addWidget(name, 1)
        lay.addWidget(num)
        return row

    def _sync(self, src: QTextEdit, dst: QTextEdit) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            s, d = src.verticalScrollBar(), dst.verticalScrollBar()
            span = s.maximum() - s.minimum()
            frac = (s.value() - s.minimum()) / span if span > 0 else 0.0
            d.setValue(d.minimum() + round(frac * (d.maximum() - d.minimum())))
        finally:
            self._syncing = False

    def show_result(self, result: DiffResult) -> None:
        st = result.stats
        self.counts[ADDED].setText(str(st.added))
        self.counts[REMOVED].setText(str(st.removed))
        self.counts[CHANGED].setText(str(st.changed))
        self.similarity.setText(format_similarity(st.similarity, st.total == 0))
        self.summary.setText("" if st.total else strings.SUMMARY_IDENTICAL)
        render_segments(self.left, result.left)
        render_segments(self.right, result.right)
        self.left.verticalScrollBar().setValue(0)
        self.right.verticalScrollBar().setValue(0)
