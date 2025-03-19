"""
Core utility functions for the_aichemist_codex.

This module provides pure utility functions with no external dependencies
beyond standard library and core modules.
"""

import hashlib
import re
from datetime import datetime
from pathlib import Path

# Import directly from constants.py, not a submodule
from the_aichemist_codex.backend.core.constants.constants import BINARY_EXTENSIONS


def create_hash(text: str) -> str:
    """Create a hash from a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for file operations."""
    # Replace illegal characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Ensure filename is not empty
    if not sanitized or sanitized.isspace():
        sanitized = "unnamed_file"
    return sanitized


def get_file_extension(path: str | Path) -> str:
    """Get the file extension from a path (lowercase, without leading dot)."""
    if isinstance(path, str):
        path = Path(path)
    return path.suffix.lower()[1:] if path.suffix else ""


def is_binary_file(file_path: str | Path) -> bool:
    """Check if a file is likely binary based on its extension."""
    extension = get_file_extension(file_path)
    return extension in BINARY_EXTENSIONS


def get_mime_type(file_path: str | Path) -> str:
    """Get the MIME type of a file based on its extension."""
    import mimetypes

    if isinstance(file_path, Path):
        file_path = str(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_timestamp(timestamp: float) -> str:
    """Format a timestamp in ISO format."""
    return datetime.fromtimestamp(timestamp).isoformat()


def get_relative_path(path: str | Path, base_path: str | Path) -> str:
    """Get a relative path from a base path."""
    if isinstance(path, str):
        path = Path(path)
    if isinstance(base_path, str):
        base_path = Path(base_path)

    try:
        return str(path.relative_to(base_path))
    except ValueError:
        # Path is not relative to base_path
        return str(path)


def ensure_directory_exists(directory_path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    if isinstance(directory_path, str):
        directory_path = Path(directory_path)

    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)

    return directory_path


def list_files(directory_path: str | Path, pattern: str | None = None) -> list[Path]:
    """List files in a directory, optionally filtering by pattern."""
    if isinstance(directory_path, str):
        directory_path = Path(directory_path)

    if not directory_path.exists() or not directory_path.is_dir():
        return []

    if pattern:
        return list(directory_path.glob(pattern))
    else:
        return [p for p in directory_path.iterdir() if p.is_file()]


def list_directories(directory_path: str | Path) -> list[Path]:
    """List subdirectories in a directory."""
    if isinstance(directory_path, str):
        directory_path = Path(directory_path)

    if not directory_path.exists() or not directory_path.is_dir():
        return []

    return [p for p in directory_path.iterdir() if p.is_dir()]


def chunk_text(text: str, chunk_size: int) -> list[str]:
    """Split text into chunks of approximately equal size."""
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    # Try to chunk at paragraph boundaries
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)

        if current_length + paragraph_length <= chunk_size:
            current_chunk.append(paragraph)
            current_length += paragraph_length + 2  # +2 for the newlines
        else:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))

            # If the paragraph itself is longer than chunk_size, split it
            if paragraph_length > chunk_size:
                # Split by sentences if possible
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                current_chunk = []
                current_length = 0

                for sentence in sentences:
                    sentence_length = len(sentence)

                    if current_length + sentence_length <= chunk_size:
                        current_chunk.append(sentence)
                        current_length += sentence_length + 1  # +1 for the space
                    else:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))

                        # If the sentence itself is longer than chunk_size, just split it
                        if sentence_length > chunk_size:
                            for i in range(0, sentence_length, chunk_size):
                                chunks.append(sentence[i : i + chunk_size])
                        else:
                            current_chunk = [sentence]
                            current_length = sentence_length + 1

                if current_chunk:
                    chunks.append(" ".join(current_chunk))
            else:
                current_chunk = [paragraph]
                current_length = paragraph_length + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def extract_text_snippet(text: str, query: str, context_size: int = 50) -> str:
    """Extract a snippet of text containing the query with context."""
    if not text or not query:
        return ""

    query_lower = query.lower()
    text_lower = text.lower()

    start = text_lower.find(query_lower)
    if start == -1:
        # If exact query not found, try to find partial matches
        words = query_lower.split()
        for word in words:
            if len(word) > 3:  # Only consider significant words
                start = text_lower.find(word)
                if start != -1:
                    break

        if start == -1:
            # Return beginning of text if no match found
            return text[: min(len(text), context_size * 2)]

    # Extract snippet with context
    snippet_start = max(0, start - context_size)
    snippet_end = min(len(text), start + len(query) + context_size)

    # Adjust to avoid cutting words
    if snippet_start > 0:
        # Move back to the start of the word
        while snippet_start > 0 and text[snippet_start - 1] not in " \t\n.,:;?!":
            snippet_start -= 1

    if snippet_end < len(text):
        # Move forward to the end of the word
        while snippet_end < len(text) and text[snippet_end] not in " \t\n.,:;?!":
            snippet_end += 1

    snippet = text[snippet_start:snippet_end]

    # Add ellipsis if necessary
    if snippet_start > 0:
        snippet = "..." + snippet
    if snippet_end < len(text):
        snippet = snippet + "..."

    return snippet
