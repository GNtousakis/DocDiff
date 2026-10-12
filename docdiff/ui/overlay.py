"""Full-screen selection overlay (one translucent window per monitor, over a frozen screenshot)."""
from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QObject, QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from docdiff import strings
from docdiff.capture import CaptureError, Monitor, crop_selection, grab_monitors, match_monitor

MIN_SELECTION = 6


def pil_to_qimage(img: Image.Image) -> QImage:
    rgb = img.convert("RGB")
    return QImage(rgb.tobytes("raw", "RGB"), rgb.width, rgb.height, 3 * rgb.width, QImage.Format_RGB888).copy()


class SelectionOverlay(QWidget):
    selected = Signal(object, tuple, tuple)  # screenshot (PIL), (x, y, w, h), (widget w, h)
    cancelled = Signal()

    def __init__(self, screen, shot: Image.Image):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self._shot = shot
        self._pixmap = QPixmap.fromImage(pil_to_qimage(shot))
        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self.setScreen(screen)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def selection_rect(self) -> QRect | None:
        if self._origin is None or self._current is None:
            return None
        return QRect(self._origin, self._current).normalized().intersected(self.rect())

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        target = QRectF(self.rect())
        p.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))
        sel = self.selection_rect()
        if sel is not None and sel.width() > 0 and sel.height() > 0:
            sx = self._pixmap.width() / self.width()
            sy = self._pixmap.height() / self.height()
            src = QRectF(sel.x() * sx, sel.y() * sy, sel.width() * sx, sel.height() * sy)
            p.drawPixmap(QRectF(sel), self._pixmap, src)
            p.setPen(QPen(QColor("#1f6feb"), 2))
            p.drawRect(sel)
        self._paint_hint(p)

    def _paint_hint(self, p: QPainter) -> None:
        font = QFont("Segoe UI", 13)
        p.setFont(font)
        fm = p.fontMetrics()
        w = fm.horizontalAdvance(strings.OVERLAY_HINT) + 40
        box = QRect((self.width() - w) // 2, 24, w, fm.height() + 20)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 24, 31, 220))
        p.drawRoundedRect(box, 10, 10)
        p.setPen(QColor("white"))
        p.drawText(box, Qt.AlignCenter, strings.OVERLAY_HINT)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.RightButton:
            self.cancelled.emit()
            return
        self._origin = self._current = e.position().toPoint()
        self.update()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._origin is not None:
            self._current = e.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        if e.button() != Qt.LeftButton or self._origin is None:
            return
        self._current = e.position().toPoint()
        sel = self.selection_rect()
        self._origin = self._current = None
        if sel is None or sel.width() < MIN_SELECTION or sel.height() < MIN_SELECTION:
            self.update()
            return
        self.selected.emit(self._shot, (sel.x(), sel.y(), sel.width(), sel.height()), (self.width(), self.height()))

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key_Escape:
            self.cancelled.emit()


class CaptureController(QObject):
    """Shows overlays on every monitor and reports the chosen region as a PIL image."""

    captured = Signal(object)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._overlays: list[SelectionOverlay] = []

    @property
    def active(self) -> bool:
        return bool(self._overlays)

    def start(self) -> None:
        if self.active:
            return
        try:
            shots = grab_monitors()
        except CaptureError as exc:
            self.failed.emit(str(exc))
            return
        monitors = [m for m, _ in shots]
        screens = QGuiApplication.screens()
        for screen in screens:
            g, dpr = screen.geometry(), screen.devicePixelRatio()
            idx = match_monitor(monitors, g.x(), g.y(), g.width() * dpr, g.height() * dpr)
            ov = SelectionOverlay(screen, shots[idx][1])
            ov.selected.connect(self._on_selected)
            ov.cancelled.connect(self._on_cancelled)
            self._overlays.append(ov)
        for ov in self._overlays:
            ov.show()
        # Keyboard focus (Esc) goes to the overlay under the cursor.
        target = next((o for o in self._overlays if o.geometry().contains(self._cursor_pos())), self._overlays[0])
        target.raise_()
        target.activateWindow()
        target.setFocus()

    @staticmethod
    def _cursor_pos():
        from PySide6.QtGui import QCursor

        return QCursor.pos()

    def _close_all(self) -> None:
        for ov in self._overlays:
            ov.close()
        self._overlays.clear()

    def _on_selected(self, shot, sel, size) -> None:
        self._close_all()
        try:
            self.captured.emit(crop_selection(shot, sel, size))
        except CaptureError as exc:
            self.failed.emit(str(exc))

    def _on_cancelled(self) -> None:
        self._close_all()
        self.cancelled.emit()
