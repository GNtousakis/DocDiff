"""One side (A or B): capture buttons, region thumbnails and the editable OCR text."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from PIL import Image
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QStackedWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from docdiff import strings
from docdiff.regions import append_text, remove_region_text
from docdiff.ui import theme
from docdiff.ui.overlay import pil_to_qimage

THUMB_SIZE = (96, 64)


@dataclass
class Region:
    rid: int
    text: str | None = None  # None while OCR is pending
    widget: QWidget | None = field(default=None, repr=False)
    label: QLabel | None = field(default=None, repr=False)


class Panel(QFrame):
    capture_requested = Signal(str, bool)  # side, append
    text_changed = Signal()

    _ids = count(1)

    def __init__(self, side: str, title: str, parent=None):
        super().__init__(parent)
        self.side = side
        self.setObjectName("panel")
        self.regions: list[Region] = []

        self.title = QLabel(title)
        self.title.setObjectName("panelTitle")
        self.kicker = QLabel(strings.PANEL_A_KICKER if side == "A" else strings.PANEL_B_KICKER)
        self.kicker.setObjectName("panelKicker")
        self.letter = QLabel(title.strip()[-1:])
        self.letter.setObjectName("letter")
        self.letter.setAlignment(Qt.AlignCenter)
        self.letter.setFixedSize(34, 34)
        self.btn_capture = QPushButton(strings.BTN_CAPTURE)
        self.btn_add = QPushButton(strings.BTN_ADD_REGION)
        self.btn_clear = QPushButton(strings.BTN_CLEAR)
        self.btn_clear.setObjectName("ghost")
        self.btn_capture.clicked.connect(lambda: self.capture_requested.emit(self.side, False))
        self.btn_add.clicked.connect(lambda: self.capture_requested.emit(self.side, True))
        self.btn_clear.clicked.connect(self.clear)

        self.thumbs_layout = QHBoxLayout()
        self.thumbs_layout.setContentsMargins(0, 0, 0, 0)
        self.thumbs_layout.setSpacing(8)
        self.thumbs_layout.addStretch(1)
        holder = QWidget()
        holder.setLayout(self.thumbs_layout)
        self.thumbs_scroll = QScrollArea()
        self.thumbs_scroll.setWidget(holder)
        self.thumbs_scroll.setWidgetResizable(True)
        self.thumbs_scroll.setFrameShape(QFrame.NoFrame)
        self.thumbs_scroll.setFixedHeight(THUMB_SIZE[1] + 62)
        self.no_regions = QLabel(f"{strings.REGIONS_LABEL} {strings.NO_REGIONS}")
        self.no_regions.setObjectName("regions")

        self.edit = QPlainTextEdit()
        self.edit.setPlaceholderText(strings.TEXT_PLACEHOLDER)
        self.edit.textChanged.connect(self.text_changed)
        self.edit.textChanged.connect(self._update_counts)
        self.words = QLabel("")
        self.words.setObjectName("count")
        self.chars = QLabel("")
        self.chars.setObjectName("count")
        self.status = QLabel("")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)

        self.diff = QTextEdit()
        self.diff.setReadOnly(True)
        self.diff.setObjectName("diff")
        self.body = QStackedWidget()
        self.body.addWidget(self.edit)
        self.body.addWidget(self.diff)
        self.actions = QWidget()
        buttons = QHBoxLayout(self.actions)
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(10)
        buttons.addWidget(self.btn_capture, 1)
        buttons.addWidget(self.btn_add, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 26, 26, 26)  # 6px margin for the corner marks + 20px padding
        lay.setSpacing(14)
        header = QHBoxLayout()
        header.setSpacing(10)
        header.addWidget(self.letter)
        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(self.kicker)
        names.addWidget(self.title)
        header.addLayout(names, 1)
        header.addWidget(self.btn_clear)
        lay.addLayout(header)
        lay.addWidget(self.actions)
        lay.addWidget(self.no_regions)
        lay.addWidget(self.thumbs_scroll)
        lay.addWidget(self.body, 1)
        counts = QHBoxLayout()
        counts.addWidget(self.words)
        counts.addStretch(1)
        counts.addWidget(self.chars)
        lay.addLayout(counts)
        lay.addWidget(self.status)
        self._update_counts()
        self._refresh_thumbs_visibility()

    def paintEvent(self, event) -> None:
        """Hairline frame with blueprint registration marks centred on the corners."""
        p = QPainter(self)
        col = QColor(theme.palette()["divider"])
        p.setPen(QPen(col, 1))
        m = 6
        r = self.rect().adjusted(m, m, -m - 1, -m - 1)
        p.drawRect(r)
        mark = QColor(theme.palette()["text"])
        mark.setAlpha(140)
        p.setPen(QPen(mark, 1))
        for x, y in ((r.left(), r.top()), (r.right(), r.top()), (r.left(), r.bottom()), (r.right(), r.bottom())):
            p.drawLine(x - 5, y, x + 5, y)
            p.drawLine(x, y - 5, x, y + 5)
        p.end()

    def set_result_mode(self, on: bool) -> None:
        self.body.setCurrentIndex(1 if on else 0)
        self.actions.setVisible(not on)
        self.btn_clear.setVisible(not on)
        self.thumbs_scroll.setVisible(not on and bool(self.regions))
        self.no_regions.setVisible(not on and not self.regions)

    def _update_counts(self) -> None:
        text = self.text()
        n = len(text.split())
        self.words.setText((strings.WORDS_ONE if n == 1 else strings.WORDS_MANY).format(n=n))
        self.chars.setText(strings.CHARS_FMT.format(n=len(text)))

    # --- public API -------------------------------------------------
    def text(self) -> str:
        return self.edit.toPlainText()

    def has_text(self) -> bool:
        return bool(self.text().strip())

    def set_status(self, message: str, level: str = "info") -> None:
        self.status.setText(message)
        self.status.setProperty("level", level)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def begin_region(self, image: Image.Image, replace: bool) -> int:
        """Add a thumbnail for a new capture (text pending). ``replace`` drops previous regions and text."""
        if replace:
            self.clear()
        rid = next(self._ids)
        region = Region(rid)
        region.widget, region.label = self._make_thumb(rid, image)
        self.regions.append(region)
        self.thumbs_layout.insertWidget(self.thumbs_layout.count() - 1, region.widget)
        self._refresh_thumbs_visibility()
        self.set_status(strings.INFO_READING)
        return rid

    def finish_region(self, rid: int, text: str) -> None:
        region = self._find(rid)
        if region is None:  # removed while OCR was running
            return
        region.text = text
        if region.label:
            region.label.setText("")
        if not text.strip():
            self.set_status(strings.ERR_NO_TEXT, "warn")
            return
        self.edit.setPlainText(append_text(self.text(), text))
        self.set_status(strings.INFO_DONE)

    def fail_region(self, rid: int, message: str) -> None:
        region = self._find(rid)
        if region is not None:
            self._drop_widget(region)
            self.regions.remove(region)
            self._refresh_thumbs_visibility()
        self.set_status(message, "error")

    def clear(self) -> None:
        for r in self.regions:
            self._drop_widget(r)
        self.regions.clear()
        self.edit.clear()
        self.set_status("")
        self._refresh_thumbs_visibility()

    def remove_region(self, rid: int) -> None:
        region = self._find(rid)
        if region is None:
            return
        self._drop_widget(region)
        self.regions.remove(region)
        self._refresh_thumbs_visibility()
        if region.text:
            new, ok = remove_region_text(self.text(), region.text)
            if ok:
                self.edit.setPlainText(new)
                self.set_status("")
            else:
                self.set_status(strings.ERR_REMOVE_EDITED, "warn")

    # --- internals --------------------------------------------------
    def _find(self, rid: int) -> Region | None:
        return next((r for r in self.regions if r.rid == rid), None)

    def _drop_widget(self, region: Region) -> None:
        if region.widget is not None:
            region.widget.setParent(None)
            region.widget.deleteLater()
            region.widget = None

    def _refresh_thumbs_visibility(self) -> None:
        has = bool(self.regions)
        in_result = self.body.currentIndex() == 1
        self.thumbs_scroll.setVisible(has and not in_result)
        self.no_regions.setVisible(not has and not in_result)

    def _make_thumb(self, rid: int, image: Image.Image):
        frame = QFrame()
        frame.setObjectName("thumb")
        pic = QLabel()
        thumb = image.copy()
        thumb.thumbnail((THUMB_SIZE[0] * 2, THUMB_SIZE[1] * 2))
        pix = QPixmap.fromImage(pil_to_qimage(thumb)).scaled(*THUMB_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pic.setPixmap(pix)
        pic.setAlignment(Qt.AlignCenter)
        pic.setFixedSize(*THUMB_SIZE)
        pending = QLabel(strings.REGION_PENDING)
        pending.setObjectName("status")
        pending.setAlignment(Qt.AlignCenter)
        remove = QPushButton(strings.BTN_REMOVE)
        remove.setObjectName("small")
        remove.clicked.connect(lambda: self.remove_region(rid))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addWidget(pic)
        lay.addWidget(pending)
        lay.addWidget(remove)
        return frame, pending
