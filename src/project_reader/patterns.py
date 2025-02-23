"""Default exclusion patterns for project_reader."""

import fnmatch
import os

# Define the default patterns globally so they can be imported.
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


class PatternMatcher:
    def __init__(self):
        self.ignore_patterns = set(DEFAULT_IGNORE_PATTERNS)

    def add_patterns(self, patterns: set):
        self.ignore_patterns.update(patterns)

    def should_ignore(self, path: str) -> bool:
        path = os.path.normpath(path)  # Normalize Windows/Unix paths
        return any(
            fnmatch.fnmatch(os.path.basename(path), pattern)
            or fnmatch.fnmatch(path, pattern)
            or path.startswith(pattern)  # Ensure directories are ignored
            for pattern in self.ignore_patterns
        )
