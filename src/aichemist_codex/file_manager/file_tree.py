"""Generates and manages project file trees."""

import asyncio
import json
import logging
from pathlib import Path

from aichemist_codex.utils.patterns import pattern_matcher

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
                rel_path = str(entry.relative_to(directory))

                if pattern_matcher.should_ignore(rel_path):
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


def generate_file_tree(directory: Path, output_file: Path):
    """Generates and saves the file tree as JSON."""
    generator = FileTreeGenerator()
    file_tree = asyncio.run(generator.generate(directory))
    output_file.write_text(json.dumps(file_tree, indent=4), encoding="utf-8")
    logger.info(f"File tree saved to {output_file}")
