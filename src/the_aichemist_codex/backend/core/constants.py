"""
Core constants for the application.

This module defines constants used throughout the application.
These constants provide a central place for configuring default values
and behavior.
"""

import os

# File and path constants
MAX_FILE_SIZE_MB = 100  # Maximum file size in MB
DEFAULT_ENCODING = "utf-8"  # Default file encoding
DEFAULT_LINE_ENDING = os.linesep  # Default line ending for the current platform
MAX_PATH_LENGTH = 260  # Maximum path length on Windows
MAX_FILENAME_LENGTH = 255  # Maximum filename length on most filesystems

# Cache constants
DEFAULT_CACHE_TTL = 3600  # Default cache TTL in seconds (1 hour)
MAX_CACHE_SIZE_MB = 1024  # Maximum cache size in MB (1 GB)
CACHE_CLEANUP_INTERVAL = 3600  # Cache cleanup interval in seconds (1 hour)
CACHE_STALE_THRESHOLD = 86400  # Cache stale threshold in seconds (1 day)

# Security constants
UNSAFE_PATH_PATTERNS = [
    r"\.\./",  # Directory traversal
    r"~/",  # Home directory
    r"^/",  # Absolute paths
    r'[<>:"|?*]',  # Invalid characters for most filesystems
]
BLOCKED_EXTENSIONS = [
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".vbs",
    ".js",
    ".ps1",
    ".sh",
]

# Performance constants
MAX_CONCURRENT_TASKS = 10  # Maximum number of concurrent tasks
DEFAULT_TIMEOUT = 30  # Default timeout in seconds
DEFAULT_CHUNK_SIZE = 4096  # Default chunk size for file operations

# Search constants
MAX_SEARCH_RESULTS = 100  # Maximum number of search results
DEFAULT_SEARCH_LIMIT = 10  # Default search result limit

# Metadata constants
METADATA_EXTRACTION_TIMEOUT = 10  # Metadata extraction timeout in seconds

# Directory structure constants
APP_DIRS = {
    "config": "config",
    "cache": "cache",
    "data": "data",
    "logs": "logs",
    "temp": "temp",
}

# Environment variable names
ENV_VAR_PROJECT_ROOT = "AICHEMIST_ROOT"
ENV_VAR_CONFIG_PATH = "AICHEMIST_CONFIG"
ENV_VAR_LOG_LEVEL = "AICHEMIST_LOG_LEVEL"
ENV_VAR_CACHE_DIR = "AICHEMIST_CACHE_DIR"

# Default log levels
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File-related constants
ALLOWED_EXTENSIONS = {
    "text": ["txt", "md", "rst", "log"],
    "code": ["py", "js", "html", "css", "json", "xml", "yaml", "yml", "ini", "toml"],
    "document": ["pdf", "doc", "docx", "odt", "rtf"],
    "spreadsheet": ["csv", "xls", "xlsx", "ods"],
    "image": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"],
    "audio": ["mp3", "wav", "ogg", "flac", "m4a"],
    "video": ["mp4", "avi", "mov", "mkv", "webm"],
    "archive": ["zip", "tar", "gz", "bz2", "7z", "rar"],
    "database": ["db", "sqlite", "sqlite3"],
}

BINARY_EXTENSIONS: set[str] = set().union(
    ALLOWED_EXTENSIONS["image"],
    ALLOWED_EXTENSIONS["audio"],
    ALLOWED_EXTENSIONS["video"],
    ALLOWED_EXTENSIONS["archive"],
    ALLOWED_EXTENSIONS["database"],
)

# Environment constants
ENV_DEV = "development"
ENV_PROD = "production"
ENV_TEST = "test"

# Directory structure constants
DEFAULT_DIRS = {
    "cache": ".cache",
    "config": "config",
    "data": "data",
    "logs": "logs",
    "tmp": "tmp",
}

# Search constants
SEARCH_SCORE_THRESHOLD = 0.5
SNIPPET_LENGTH = 200
