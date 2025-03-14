from collections import namedtuple
from pathlib import Path

import numpy as np
import pytest
from src.file_reader.ocr_parser import OCRParser

# Create a dummy ExtractionResult NamedTuple
DummyExtractionResult = namedtuple(
    "DummyExtractionResult", ["content", "mime_type", "metadata"]
)


# Define an async dummy function for extract_file
async def dummy_extract_file(path, **kwargs):
    return DummyExtractionResult("Test OCR text", "text/plain", {})


@pytest.mark.asyncio
async def test_ocr_parser(monkeypatch, tmp_path: Path):
    # Create a dummy image file
    dummy_image_path = tmp_path / "dummy.png"
    dummy_image_path.write_bytes(b"fake image data")

    # Simulate OpenCV functions
    import csv as cv2
    dummy_image = np.ones((10, 10, 3), dtype=np.uint8) * 255
    monkeypatch.setattr(cv2, "imread", lambda path: dummy_image)
    monkeypatch.setattr(cv2, "cvtColor", lambda img, code: img)

    # Patch extract_file in the ocr_parser module where it was imported
    import src.file_reader.ocr_parser as ocr_parser

    monkeypatch.setattr(ocr_parser, "extract_file", dummy_extract_file)

    parser = OCRParser()
    result = await parser.parse(dummy_image_path)
    assert "content" in result
    assert result["content"] == "Test OCR text"
