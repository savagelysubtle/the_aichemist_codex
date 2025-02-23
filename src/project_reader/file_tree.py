import argparse
import asyncio
import json
import logging
from pathlib import Path

from config.config_manager import CodexConfig
from project_reader.logging_config import setup_logging
from project_reader.patterns import PatternMatcher

setup_logging()
config = CodexConfig()

MAX_DEPTH = 10


class FileTreeGenerator:
    def __init__(self):
        self.pattern_matcher = PatternMatcher()

    async def generate(self, directory: Path, depth=0) -> dict:
        """Recursively generates a file tree, applying ignore patterns."""
        if depth > MAX_DEPTH:
            return {"error": "max_depth_exceeded"}

        tree = {}
        try:
            for entry in sorted(directory.iterdir(), key=lambda e: e.name.lower()):
                rel_path = str(entry.relative_to(directory))

                if self.pattern_matcher.should_ignore(rel_path):
                    continue

                if entry.is_symlink() and not self._is_safe_symlink(entry, directory):
                    continue

                if entry.is_dir():
                    tree[entry.name] = await self.generate(entry, depth + 1)
                else:
                    tree[entry.name] = {
                        "size": entry.stat().st_size,
                        "type": "file",
                    }
        except PermissionError:
            logging.error(f"Permission denied: {directory}")
            tree["error"] = "permission_denied"
        except Exception as e:
            logging.error(f"Error scanning {directory}: {e}")
            tree["error"] = str(e)
        return tree

    def _is_safe_symlink(self, symlink: Path, base_path: Path) -> bool:
        """Ensures symlink targets remain within the base directory."""
        try:
            target = symlink.resolve()
            return base_path in target.parents
        except Exception:
            return False


def get_project_name(directory: Path) -> str:
    """Returns the project name based on the directory name."""
    return directory.name


def list_python_files(directory: Path) -> list:
    """Returns a list of Python files in the given directory and its subdirectories."""
    return [file for file in directory.glob("**/*.py") if file.is_file()]



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a file tree.")
    parser.add_argument("directory", type=Path, help="Directory to analyze.")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON file.")
    args = parser.parse_args()

    output_file = args.output or args.directory.parent / "file_tree.json"

    logging.info(f"Scanning: {args.directory}")
    generator = FileTreeGenerator()
    tree = asyncio.run(generator.generate(args.directory))

    output_file.write_text(json.dumps(tree, indent=4), encoding="utf-8")
    logging.info(f"File tree saved to {output_file}")
