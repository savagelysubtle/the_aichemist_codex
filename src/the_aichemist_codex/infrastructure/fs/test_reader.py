"""Test script for file reader functionality."""

import asyncio
import logging
from pathlib import Path

from .file_reader import FileReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run file reader tests."""
    # Create a file reader
    reader = FileReader(max_workers=2, preview_length=200)

    # Get current script path
    current_file = Path(__file__)

    # Test reading this file
    logger.info(f"Testing file: {current_file}")

    # Get MIME type
    mime_type = reader.get_mime_type(current_file)
    logger.info(f"MIME type: {mime_type}")

    # Process file
    metadata = await reader.process_file(current_file)

    # Print metadata
    logger.info(f"File size: {metadata.size}")
    logger.info(f"Extension: {metadata.extension}")
    logger.info(f"Preview: {metadata.preview[:100]}...")

    if metadata.error:
        logger.error(f"Error: {metadata.error}")

    if metadata.parsed_data:
        logger.info(f"Line count: {metadata.parsed_data.get('line_count', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
