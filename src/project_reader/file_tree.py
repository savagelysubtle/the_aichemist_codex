import argparse
import asyncio
import json
import logging
from pathlib import Path

from common.safety import SafeDirectoryScanner
from config.config_manager import CodexConfig
from project_reader.logging_config import setup_logging
from project_reader.patterns import PatternMatcher

# Initialize logging and load config
setup_logging()
config = CodexConfig()  # Future use for modularizing per package

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_DEPTH = 10


class FileTreeGenerator:
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.scanner = SafeDirectoryScanner()

    async def generate(self, directory: Path, depth=0) -> dict:
        """
        Asynchronously generates a file tree dictionary structure.
        Applies pattern exclusion and checks symlink safety.
        """
        if depth > MAX_DEPTH:
            return {"error": "max_depth_exceeded"}

        tree = {}
        try:
            for entry in sorted(directory.iterdir(), key=lambda e: e.name.lower()):
                rel_path = str(entry.relative_to(directory))

                # Ignore patterns
                if self.pattern_matcher.should_ignore(rel_path):
                    continue

                # Symlink safety check
                if entry.is_symlink() and not self.scanner.is_safe_path(
                    entry, directory
                ):
                    continue

                if entry.is_dir():
                    tree[entry.name] = await self.generate(entry, depth + 1)
                else:
                    tree[entry.name] = None
        except PermissionError:
            logging.error(f"Permission denied: {directory}")
            tree["error"] = "permission_denied"
        except Exception as e:
            logging.error(f"Unexpected error while reading {directory}: {e}")
            tree["error"] = str(e)
        return tree


def get_project_name(directory: Path) -> str:
    """Returns the project name based on the directory name."""
    return directory.name


def list_python_files(directory: Path) -> list:
    """Returns a list of Python files in the given directory and its subdirectories."""
    return [file for file in directory.glob("**/*.py") if file.is_file()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a file tree for a given directory."
    )
    parser.add_argument(
        "directory", type=Path, help="Path to the directory to analyze."
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output JSON file for file tree."
    )
    args = parser.parse_args()

    project_name = get_project_name(args.directory)
    output_file = (
        args.output
        if args.output
        else args.directory.parent / f"{project_name}_file_tree.json"
    )

    logging.info(f"Generating file tree for {args.directory}")
    generator = FileTreeGenerator()
    tree = asyncio.run(generator.generate(args.directory))

    output_file.write_text(json.dumps(tree, indent=4), encoding="utf-8")
    logging.info(f"File tree saved to {output_file}")
