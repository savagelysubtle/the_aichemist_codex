"""Quick test for the FileReader class."""

import asyncio
from pathlib import Path

from src.the_aichemist_codex.fs.file_reader import FileReader


async def main():
    """Run a quick test on FileReader."""
    reader = FileReader()

    # Test with README.md
    readme_path = Path("README.md")
    mime_type = reader.get_mime_type(readme_path)
    print(f"README.md MIME type: {mime_type}")

    # Process the file
    metadata = await reader.process_file(readme_path)
    print(f"Title: {metadata.title}")
    print(f"Size: {metadata.size}")
    print(f"Preview: {metadata.preview[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
