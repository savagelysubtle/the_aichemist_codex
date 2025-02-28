import logging
from pathlib import Path
from typing import Any, Dict

from kreuzberg import extract_file

logger = logging.getLogger(__name__)


class OCRParser:
    """Parser for performing OCR on image files using kreuzberg.
    This parser extracts text from image files.
    """

    async def parse(self, file_path: Path) -> Dict[str, Any]:
        """Perform OCR on the image file.

        Args:
            file_path (Path): The path to the image file.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted text under 'content'.

        Raises:
            Exception: If the image cannot be read or OCR fails.
        """
        try:
            from aichemist_codex.utils import AsyncFileIO

            # Read the image file as binary data.
            binary_data = await AsyncFileIO.read_binary(file_path)
            result = await extract_file(binary_data)
            return {"content": result.content}
        except Exception as e:
            logger.error(f"OCR parsing failed for {file_path}: {e}", exc_info=True)
            raise

    def get_preview(self, parsed_data: Dict[str, Any], max_length: int = 1000) -> str:
        """Generate a preview of the OCR extracted text."""
        text = parsed_data.get("content", "")
        return text[:max_length] + "..." if len(text) > max_length else text
