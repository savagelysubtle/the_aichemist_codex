"""Default exclusion patterns for project_reader."""

import fnmatch

DEFAULT_IGNORE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "*.class",
    "*.jar",
    "node_modules",
    ".git",
    ".svn",
    ".hg",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    "target",
    ".vscode",
    ".idea",
    ".DS_Store",
    "Thumbs.db",
}


def should_ignore(path: str) -> bool:
    """Determines if a file should be ignored based on default patterns."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in DEFAULT_IGNORE_PATTERNS)
