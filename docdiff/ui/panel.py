"""One side (A or B): capture buttons, region thumbnails and the editable OCR text."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from PIL import Image
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from docdiff import strings
from docdiff.regions import append_text, remove_region_text
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
        self.btn_capture = QPushButton(strings.BTN_CAPTURE)
        self.btn_add = QPushButton(strings.BTN_ADD_REGION)
        self.btn_clear = QPushButton(strings.BTN_CLEAR)
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
        self.no_regions.setObjectName("status")

        self.edit = QPlainTextEdit()
        self.edit.setPlaceholderText(strings.TEXT_PLACEHOLDER)
        self.edit.textChanged.connect(self.text_changed)
        self.status = QLabel("")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(self.btn_capture, 1)
        buttons.addWidget(self.btn_add, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(self.title, 1)
        header.addWidget(self.btn_clear)
        lay.addLayout(header)
        lay.addLayout(buttons)
        lay.addWidget(self.no_regions)
        lay.addWidget(self.thumbs_scroll)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.status)
        self._refresh_thumbs_visibility()

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
        self.thumbs_scroll.setVisible(has)
        self.no_regions.setVisible(not has)

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
