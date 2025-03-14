from pathlib import Path
from typing import Dict, List

import tiktoken


def human_readable_size(size: int) -> str:
    """Convert a file size in bytes to a human-readable string."""
    if size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    n = 0
    while size >= 1024 and n < len(units) - 1:
        size /= 1024
        n += 1
    return f"{size:.2f} {units[n]}"


def count_tokens(context_string: str) -> int:
    """
    Return the number of tokens in a text string as an integer.

    This function uses the `tiktoken` library to encode the text and returns the total
    number of tokens.

    Parameters
    ----------
    context_string : str
        The text string for which the token count is to be estimated.

    Returns
    -------
    int
        The total number of tokens, or 0 if an error occurs.
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        total_tokens = len(encoding.encode(context_string, disallowed_special=()))
        return total_tokens
    except Exception as e:
        print(e)
        return 0


def format_token_count(total_tokens: int) -> str:
    """
    Format the token count into a human-readable string.

    For example, 1200 becomes '1.2k' and 1,500,000 becomes '1.5M'.
    """
    if total_tokens > 1_000_000:
        return f"{total_tokens / 1_000_000:.1f}M"
    elif total_tokens > 1_000:
        return f"{total_tokens / 1_000:.1f}k"
    else:
        return str(total_tokens)


def aggregate_digest(file_paths: List[Path], content_map: Dict[Path, str]) -> str:
    """
    Combines the list of file paths and their corresponding full content into a comprehensive digest string.

    The header includes:
      - Total Files
      - Total Tokens (summed over all file contents, formatted)
      - Total Size (formatted in human-readable units)

    Parameters
    ----------
    file_paths : List[Path]
        A list of file paths identified for ingestion.
    content_map : Dict[Path, str]
        A mapping of each file path to its complete text content.

    Returns
    -------
    str
        A formatted digest containing file headers, full content, and summary statistics.
    """
    lines = []
    total_files = len(file_paths)
    total_size_bytes = sum(fp.stat().st_size for fp in file_paths if fp.exists())
    total_size_hr = human_readable_size(total_size_bytes)

    # Sum the raw token counts from each file's content.
    raw_token_count = sum(count_tokens(content) for content in content_map.values())
    formatted_tokens = format_token_count(raw_token_count)

    lines.append("Project Digest Summary")
    lines.append(f"Total Files: {total_files}")
    lines.append(f"Total Tokens: {formatted_tokens}")
    lines.append(f"Total Size: {total_size_hr}")
    lines.append("")  # blank line

    for fp in file_paths:
        try:
            relative_path = fp.relative_to(fp.parents[1])
        except Exception:
            relative_path = fp
        lines.append(f"--- File: {relative_path} ---")
        lines.append(content_map.get(fp, ""))
        lines.append("")  # blank line between files

    return "\n".join(lines)
