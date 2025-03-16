from collections import namedtuple
from pathlib import Path

import numpy as np
import pytest

from backend.src.file_reader.ocr_parser import OCRParser

# Create a dummy ExtractionResult NamedTuple
DummyExtractionResult = namedtuple(
    "DummyExtractionResult", ["content", "mime_type", "metadata"]
)


# Define an async dummy function for extract_file
async def dummy_extract_file(
    path: Path, **kwargs: dict[str, str]
) -> DummyExtractionResult:
    return DummyExtractionResult("Test OCR text", "text/plain", {})


@pytest.mark.asyncio
async def test_ocr_parser(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Create a dummy image file
    dummy_image_path = tmp_path / "dummy.png"
    dummy_image_path.write_bytes(b"fake image data")

    # Simulate OpenCV functions with a mock instead of importing
    from unittest.mock import MagicMock

    cv2 = MagicMock()

    dummy_image = np.ones((10, 10, 3), dtype=np.uint8) * 255
    monkeypatch.setattr(cv2, "imread", lambda path: dummy_image)
    monkeypatch.setattr(cv2, "cvtColor", lambda img, code: img)

    # Patch extract_file in the ocr_parser module where it was imported
    import backend.src.file_reader.ocr_parser as ocr_parser

    monkeypatch.setattr(ocr_parser, "extract_file", dummy_extract_file)

    parser = OCRParser()
    result = await parser.parse(dummy_image_path)
    assert "content" in result  # noqa: S101
    assert result["content"] == "Test OCR text"  # noqa: S101
