"""Diff result helpers: segment rendering, synchronised scrolling and the summary column in the middle rail."""
from __future__ import annotations

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from docdiff import strings
from docdiff.diffing import ADDED, CHANGED, REMOVED, DiffResult, Segment
from docdiff.ui import theme


def render_segments(edit: QTextEdit, segments: list[Segment]) -> None:
    edit.clear()
    cursor = QTextCursor(edit.document())
    for seg in segments:
        cursor.insertText(seg.text, theme.format_for(seg.kind))


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
        self.summary.setText("" if st.total else strings.SUMMARY_IDENTICAL)
        render_segments(self.left, result.left)
        render_segments(self.right, result.right)
        self.left.verticalScrollBar().setValue(0)
        self.right.verticalScrollBar().setValue(0)
