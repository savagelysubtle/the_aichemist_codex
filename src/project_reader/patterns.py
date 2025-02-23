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


def __init__(self):
    self.ignore_patterns = self.DEFAULT_PATTERNS.copy()


def add_patterns(self, patterns: set):
    self.ignore_patterns.update(patterns)


def should_ignore(self, path: str) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in self.ignore_patterns)
