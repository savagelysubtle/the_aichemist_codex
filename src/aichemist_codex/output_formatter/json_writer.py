"""Handles JSON output for structured code summaries."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_as_json(output_file: Path, data: dict):
    """Saves extracted code summary as a structured JSON file."""
    try:
        output_file.write_text(json.dumps(data, indent=4), encoding="utf-8")
        logger.info(f"JSON summary saved: {output_file}")

    except Exception as e:
        logger.error(f"Error writing JSON output to {output_file}: {e}")
