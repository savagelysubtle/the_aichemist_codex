"""Global settings and configuration constants."""

import os
from pathlib import Path
from typing import Any

# Base directories
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = DATA_DIR / "logs"
EXPORT_DIR = DATA_DIR / "exports"

# Ensure directories exist with proper permissions
for directory in [DATA_DIR, CACHE_DIR, LOG_DIR, EXPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)  # Secure directory permissions

# File settings
DEFAULT_JSON_INDENT = 4
DEFAULT_IGNORE_PATTERNS: list[str] = [
    # Python
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "poetry.lock",
    "Pipfile.lock",
    # JavaScript/Node
    "node_modules",
    "bower_components",
    "package-lock.json",
    "yarn.lock",
    ".npm",
    ".yarn",
    ".pnpm-store",
    # Java
    "*.class",
    "*.jar",
    "*.war",
    "*.ear",
    "*.nar",
    "target/",
    ".gradle/",
    "build/",
    ".settings/",
    ".project",
    ".classpath",
    "gradle-app.setting",
    "*.gradle",
    # C/C++
    "*.o",
    "*.obj",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.exe",
    "*.lib",
    "*.out",
    "*.a",
    "*.pdb",
    # Swift/Xcode
    ".build/",
    "*.xcodeproj/",
    "*.xcworkspace/",
    "*.pbxuser",
    "*.mode1v3",
    "*.mode2v3",
    "*.perspectivev3",
    "*.xcuserstate",
    "xcuserdata/",
    ".swiftpm/",
    # Ruby
    "*.gem",
    ".bundle/",
    "vendor/bundle",
    "Gemfile.lock",
    ".ruby-version",
    ".ruby-gemset",
    ".rvmrc",
    # Rust
    "target/",
    "Cargo.lock",
    "**/*.rs.bk",
    # Go
    "bin/",
    "pkg/",
    # .NET/C#
    "bin/",
    "obj/",
    "*.suo",
    "*.user",
    "*.userosscache",
    "*.sln.docstates",
    "packages/",
    "*.nupkg",
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    # Images and media
    "*.svg",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.pdf",
    "*.mov",
    "*.mp4",
    "*.mp3",
    "*.wav",
    # Virtual environments
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    # IDEs and editors
    ".idea",
    ".vscode",
    ".vs",
    "*.swp",
    "*.swo",
    "*.swn",
    ".settings",
    ".project",
    ".classpath",
    "*.sublime-*",
    # Temporary and cache files
    "*.log",
    "*.bak",
    "*.swp",
    "*.tmp",
    "*.temp",
    ".cache",
    ".sass-cache",
    ".eslintcache",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    # Build directories and artifacts
    "build",
    "dist",
    "target",
    "out",
    "*.egg-info",
    "*.egg",
    "*.whl",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.class",
    # Documentation
    "site-packages",
    ".docusaurus",
    ".next",
    ".nuxt",
    # Other common patterns
    ## Minified files
    "*.min.js",
    "*.min.css",
    ## Source maps
    "*.map",
    ## Terraform
    ".terraform",
    "*.tfstate*",
    ## Dependencies in various languages
    "vendor/",
]

# Cache settings
CACHE_TTL = 3600  # 1 hour in seconds
MAX_CACHE_SIZE = 1024 * 1024 * 100  # 100MB
MAX_MEMORY_CACHE_ITEMS = 1000

# File processing settings
MAX_FILE_SIZE = 1024 * 1024 * 50  # 50MB
CHUNK_SIZE = 1024 * 64  # 64KB chunks for file operations
MAX_BATCH_SIZE = 100  # Maximum items in a batch operation
MAX_TOKENS = 8000  # Token limit for analysis

# Search settings
MAX_SEARCH_RESULTS = 1000
SEARCH_CACHE_TTL = 300  # 5 minutes
MIN_SEARCH_TERM_LENGTH = 3

# Regex search settings
REGEX_MAX_COMPLEXITY = 1000  # Maximum complexity score for regex patterns
REGEX_TIMEOUT_MS = 500  # Timeout for regex search operations in milliseconds
REGEX_CACHE_TTL = 300  # 5 minutes
REGEX_MAX_RESULTS = 100  # Maximum number of results to return

# Similarity search settings
SIMILARITY_THRESHOLD = 0.75  # Minimum similarity score (0.0-1.0)
SIMILARITY_MAX_RESULTS = 50  # Maximum number of similar files to return
SIMILARITY_CACHE_TTL = 300  # 5 minutes
SIMILARITY_MIN_GROUP_SIZE = 2  # Minimum number of files to form a group
SIMILARITY_GROUP_THRESHOLD = 0.8  # Threshold for group membership

# Security settings
PASSWORD_MIN_LENGTH = 12
PASSWORD_COMPLEXITY = {
    "min_lowercase": 1,
    "min_uppercase": 1,
    "min_digits": 1,
    "min_special": 1,
}
TOKEN_EXPIRY = 3600  # 1 hour in seconds
MAX_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN = 300  # 5 minutes

# Logging settings
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"
MAX_LOG_SIZE = 1024 * 1024 * 10  # 10MB
MAX_LOG_FILES = 5

# API settings
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Performance settings
THREAD_POOL_SIZE = os.cpu_count() or 4
TASK_QUEUE_SIZE = 1000
RATE_LIMIT = {"default": 60, "search": 30, "batch": 10}  # requests per minute

# Feature flags
FEATURES = {
    "enable_caching": True,
    "enable_compression": True,
    "enable_rate_limiting": True,
    "enable_batch_processing": True,
    "enable_async_processing": True,
    "enable_regex_search": True,  # Enable regex search functionality
    "enable_similarity_search": True,  # Enable similarity search functionality
    "enable_semantic_search": False,  # Disable semantic search by default
}

# Metadata Extraction Settings
ENABLE_ENHANCED_METADATA = True
METADATA_CACHE_TTL = 3600  # 1 hour cache TTL for metadata
METADATA_MAX_CONCURRENT = 5  # Maximum concurrent metadata extraction tasks
METADATA_CONFIDENCE_THRESHOLD = (
    0.5  # Minimum confidence threshold for metadata extraction
)


def get_settings() -> dict[str, Any]:
    """
    Get all settings as a dictionary.

    Returns:
        Dict[str, Any]: Dictionary containing all settings from this module
    """
    settings = {}
    for key, value in globals().items():
        # Only include uppercase variables and not built-ins
        if key.isupper() and not key.startswith("_"):
            settings[key] = value
    return settings
