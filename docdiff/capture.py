"""Screen capture with mss."""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class Monitor:
    left: int
    top: int
    width: int
    height: int


class CaptureError(RuntimeError):
    pass


def grab_monitors() -> list[tuple[Monitor, Image.Image]]:
    """Screenshot of every physical monitor (mss physical pixels)."""
    try:
        import mss

        with mss.mss() as sct:
            out = []
            for m in sct.monitors[1:]:
                shot = sct.grab(m)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                out.append((Monitor(m["left"], m["top"], m["width"], m["height"]), img))
            if not out:
                raise CaptureError("no monitors")
            return out
    except CaptureError:
        raise
    except Exception as exc:  # mss raises ScreenShotError and platform specific errors
        raise CaptureError(str(exc)) from exc


def match_monitor(monitors: list[Monitor], x: float, y: float, w: float, h: float) -> int:
    """Index of the monitor whose geometry is closest to the given (expected physical) rectangle."""
    def dist(m: Monitor) -> float:
        return abs(m.left - x) + abs(m.top - y) + abs(m.width - w) + abs(m.height - h)

    return min(range(len(monitors)), key=lambda i: dist(monitors[i]))


def crop_selection(image: Image.Image, sel: tuple[float, float, float, float], widget_size: tuple[float, float]) -> Image.Image:
    """Crop ``image`` (physical pixels) using ``sel`` (x, y, w, h) given in widget (logical) coordinates."""
    sx = image.width / widget_size[0]
    sy = image.height / widget_size[1]
    x, y, w, h = sel
    box = (round(x * sx), round(y * sy), round((x + w) * sx), round((y + h) * sy))
    box = (max(0, box[0]), max(0, box[1]), min(image.width, box[2]), min(image.height, box[3]))
    if box[2] - box[0] < 1 or box[3] - box[1] < 1:
        raise CaptureError("empty selection")
    return image.crop(box)
