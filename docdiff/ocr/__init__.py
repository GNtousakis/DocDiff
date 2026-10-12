"""OCR engines."""
from __future__ import annotations

from docdiff.ocr.base import OcrEngine, OcrError, OcrLine, OcrResult, OcrWord
from docdiff.ocr.stub import StubOcrEngine

__all__ = ["OcrEngine", "OcrError", "OcrLine", "OcrResult", "OcrWord", "StubOcrEngine", "create_engine"]


def create_engine(force_stub: bool = False) -> OcrEngine:
    """Real Windows engine when available, otherwise the stub (development mode)."""
    if not force_stub:
        from docdiff.ocr import windows

        if windows.is_supported():
            try:
                return windows.WindowsOcrEngine()
            except OcrError:
                pass
    return StubOcrEngine(["table_v1", "table_v2"])
