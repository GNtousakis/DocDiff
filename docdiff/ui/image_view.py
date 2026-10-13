"""Scaled image display used for the captured region and for the image-diff overlay."""
from __future__ import annotations

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from docdiff import strings
from docdiff.ui.overlay import pil_to_qimage


class ImageView(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("imageView")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._pix: QPixmap | None = None
        self.clear_image()

    def set_image(self, image: Image.Image) -> None:
        self._pix = QPixmap.fromImage(pil_to_qimage(image))
        self.setText("")
        self._refresh()

    def clear_image(self, placeholder: str = strings.IMAGE_PLACEHOLDER) -> None:
        self._pix = None
        self.setPixmap(QPixmap())
        self.setText(placeholder)

    def has_image(self) -> bool:
        return self._pix is not None

    def _refresh(self) -> None:
        if self._pix is not None:
            self.setPixmap(self._pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()
