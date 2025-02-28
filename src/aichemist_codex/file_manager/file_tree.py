"""Generates and manages project file trees."""

import asyncio
import logging
from pathlib import Path

from aichemist_codex.utils.async_io import AsyncFileIO
from aichemist_codex.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)
MAX_DEPTH = 10  # Prevent infinite recursion


class FileTreeGenerator:
    """Recursively generates a project file tree."""

    async def generate(self, directory: Path, depth=0) -> dict:
        """Scans the directory and generates a structured file tree."""
        if depth > MAX_DEPTH:
            return {"error": "max_depth_exceeded"}

        tree = {}
        try:
            for entry in sorted(directory.iterdir(), key=lambda e: e.name.lower()):
                if SafeFileHandler.should_ignore(entry):
                    logger.info(f"Skipping ignored path: {entry}")
                    continue

                if entry.is_dir():
                    tree[entry.name] = await self.generate(entry, depth + 1)
                else:
                    tree[entry.name] = {"size": entry.stat().st_size, "type": "file"}
        except PermissionError:
            logger.error(f"Permission denied: {directory}")
            tree["error"] = "permission_denied"
        except Exception as e:
            logger.error(f"Error scanning {directory}: {e}")
            tree["error"] = str(e)
        return tree


async def generate_file_tree(directory: Path, output_file: Path):
    generator = FileTreeGenerator()
    file_tree = await generator.generate(directory)
    success = await AsyncFileIO.write_json(output_file, file_tree)
    if success:
        logger.info(f"File tree saved to {output_file}")
    else:
        logger.error(f"Failed to save file tree to {output_file}")
