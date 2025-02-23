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
    "myenv",
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
        """Allow dynamically adding more patterns at runtime."""
        self.ignore_patterns.update(patterns)

    def should_ignore(self, path: str) -> bool:
        """
        Determines if a given path should be ignored based on patterns.
        - Matches exact filenames, directory names, and subdirectory patterns.
        - Normalizes paths for cross-platform compatibility.
        """
        norm_path = os.path.normpath(path)  # Normalize Windows/Unix paths
        base_name = os.path.basename(norm_path)  # Extract last part of path

        return any(
            fnmatch.fnmatch(base_name, pattern)  # Match just filename/dirname
            or fnmatch.fnmatch(norm_path, pattern)  # Match full relative path
            or any(
                part in self.ignore_patterns for part in norm_path.split(os.sep)
            )  # Match partial path segments
            for pattern in self.ignore_patterns
        )
