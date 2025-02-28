"""Handles JSON output for structured code summaries."""

import json
import logging
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)


class PathEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


async def save_as_json_async(data, output_file: Path):
    """Saves data as JSON asynchronously, converting Path objects to strings."""
    try:
        json_data = json.dumps(data, cls=PathEncoder, indent=4)
        async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
            await f.write(json_data)
        logger.info(f"File tree saved to {output_file}")
    except Exception as e:
        logger.error(f"Error writing JSON to {output_file}: {e}")


def save_as_json(output_file: Path, data: dict):
    """Saves extracted code summary as a structured JSON file."""
    import asyncio

    return asyncio.run(save_as_json_async(data, output_file))
