"""Image -> structured text."""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from docdiff.imaging import preprocess
from docdiff.layout import reconstruct_text
from docdiff.ocr.base import OcrEngine


@dataclass
class OcrOutcome:
    text: str
    language: str | None = None
    language_fallback: bool = False


def image_to_text(engine: OcrEngine, image: Image.Image) -> OcrOutcome:
    max_dim = getattr(engine, "max_image_dimension", None)
    prepared = preprocess(image, max_dim) if max_dim else preprocess(image)
    result = engine.recognize(prepared)
    return OcrOutcome(reconstruct_text(result), result.language, result.language_fallback)
