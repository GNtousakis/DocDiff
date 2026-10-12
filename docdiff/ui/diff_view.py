"""Side-by-side diff display with synchronised scrolling, summary and legend."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QTextEdit, QVBoxLayout, QWidget

from docdiff import strings
from docdiff.diffing import ADDED, CHANGED, REMOVED, DiffResult, Segment
from docdiff.ui import theme


def _legend_chip(text: str, kind: str) -> QLabel:
    fmt = theme.format_for(kind)
    bg, fg = fmt.background().color().name(), fmt.foreground().color().name()
    deco = "underline" if fmt.fontUnderline() else "line-through" if fmt.fontStrikeOut() else "none"
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; text-decoration:{deco}; border-radius:6px; padding:3px 10px; font-weight:600;"
    )
    return lbl


def render_segments(edit: QTextEdit, segments: list[Segment]) -> None:
    edit.clear()
    cursor = QTextCursor(edit.document())
    for seg in segments:
        cursor.insertText(seg.text, theme.format_for(seg.kind))


class DiffView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.summary = QLabel("")
        self.summary.setObjectName("summary")
        self.left = QTextEdit()
        self.right = QTextEdit()
        for e in (self.left, self.right):
            e.setReadOnly(True)
            e.setLineWrapMode(QTextEdit.WidgetWidth)
        self._syncing = False
        self.left.verticalScrollBar().valueChanged.connect(lambda v: self._sync(self.left, self.right))
        self.right.verticalScrollBar().valueChanged.connect(lambda v: self._sync(self.right, self.left))

        legend = QHBoxLayout()
        legend.setSpacing(8)
        legend.addWidget(self.summary, 1)
        legend.addWidget(_legend_chip(strings.LEGEND_ADDED, ADDED))
        legend.addWidget(_legend_chip(strings.LEGEND_REMOVED, REMOVED))
        legend.addWidget(_legend_chip(strings.LEGEND_CHANGED, CHANGED))

        titles = QHBoxLayout()
        for t in (strings.RESULT_LEFT_TITLE, strings.RESULT_RIGHT_TITLE):
            lbl = QLabel(t)
            lbl.setObjectName("panelTitle")
            titles.addWidget(lbl, 1)
        cols = QHBoxLayout()
        cols.setSpacing(14)
        cols.addWidget(self.left, 1)
        cols.addWidget(self.right, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.addLayout(legend)
        lay.addLayout(titles)
        lay.addLayout(cols, 1)

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
        self.summary.setText(
            strings.SUMMARY_FMT.format(added=st.added, removed=st.removed, changed=st.changed)
            if st.total
            else strings.SUMMARY_IDENTICAL
        )
        render_segments(self.left, result.left)
        render_segments(self.right, result.right)
        self.left.verticalScrollBar().setValue(0)
        self.right.verticalScrollBar().setValue(0)
