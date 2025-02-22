import json
import logging

logger = logging.getLogger(__name__)


def load_file_moves(json_file: str) -> dict:
    """Loads file move instructions from a JSON file."""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file: {json_file}. Error: {e}")
        return {}
