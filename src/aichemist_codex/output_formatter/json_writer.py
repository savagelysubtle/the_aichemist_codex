"""Handles JSON output for structured code summaries."""

import logging
from pathlib import Path

from aichemist_codex.utils import AsyncFileIO

logger = logging.getLogger(__name__)


async def save_as_json_async(output_file: Path, data: dict):
    """Saves extracted code summary as a structured JSON file asynchronously."""
    success = await AsyncFileIO.write_json(output_file, data)
    if success:
        logger.info(f"JSON summary saved: {output_file}")
    else:
        logger.error(f"Error writing JSON output to {output_file}")
    return success


def save_as_json(output_file: Path, data: dict):
    """Saves extracted code summary as a structured JSON file."""
    import asyncio

    return asyncio.run(save_as_json_async(output_file, data))
