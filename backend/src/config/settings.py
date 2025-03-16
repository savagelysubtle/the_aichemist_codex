"""Global settings and configuration constants."""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Project root detection - more robust approach
def determine_project_root() -> Path:
    """
    Determine the project root directory using multiple methods.

    First checks for environment variable, then tries to detect based on
    repository structure, with a fallback to the parent of the backend directory.

    Returns:
        Path: The detected project root directory
    """
    # 1. First priority: Check environment variable
    env_root = os.environ.get("AICHEMIST_ROOT_DIR")
    if env_root:
        root_dir = Path(env_root).resolve()
        if root_dir.exists():
            logger.info(f"Using root directory from environment: {root_dir}")
            return root_dir
        else:
            logger.warning(f"Environment root directory doesn't exist: {root_dir}")

    # 2. Second priority: Look for repository indicators
    current_file = Path(__file__).resolve()
    potential_root = (
        current_file.parent.parent.parent.parent
    )  # Go up to the project root

    # Check for indicators of project root (like README.md, pyproject.toml, etc.)
    root_indicators = ["README.md", "pyproject.toml", ".git"]
    if any((potential_root / indicator).exists() for indicator in root_indicators):
        logger.info(f"Detected project root at: {potential_root}")
        return potential_root

    # 3. Fallback: Use parent of backend directory
    backend_parent = current_file.parent.parent.parent  # This is backend/
    logger.info(f"Using backend parent as root: {backend_parent}")
    return backend_parent


# Determine data directory location
def determine_data_dir() -> Path:
    """
    Determine the data directory location.

    Checks for environment variable first, then uses a subdirectory
    of the project root.

    Returns:
        Path: The data directory path
    """
    # Check for environment variable override
    env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
    if env_data_dir:
        data_dir = Path(env_data_dir).resolve()
        logger.info(f"Using data directory from environment: {data_dir}")
        return data_dir

    # Default: Use data/ subdirectory in project root
    data_dir = PROJECT_ROOT / "data"
    logger.info(f"Using default data directory: {data_dir}")
    return data_dir


# Base directories
PROJECT_ROOT = determine_project_root()
DATA_DIR = determine_data_dir()
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = DATA_DIR / "logs"
EXPORT_DIR = DATA_DIR / "exports"
VERSION_DIR = DATA_DIR / "versions"

# Ensure directories exist with proper permissions
for directory in [DATA_DIR, CACHE_DIR, LOG_DIR, EXPORT_DIR, VERSION_DIR]:
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

# Versioning settings
DEFAULT_VERSIONING_SETTINGS = {
    "auto_create_versions": True,  # Automatically create versions on file changes
    "version_on_modify": True,  # Create versions when files are modified
    "max_versions_per_file": 20,  # Maximum number of versions to keep per file
    "default_policy": "HYBRID",  # Default versioning policy (FULL_COPY, DIFF_BASED, HYBRID)
    "version_retention_days": 30,  # Number of days to keep versions before cleanup
    "compression_enabled": True,  # Use compression for stored versions
    "include_patterns": [  # File patterns to include in versioning
        "*.py",
        "*.js",
        "*.ts",
        "*.html",
        "*.css",
        "*.md",
        "*.txt",
        "*.json",
        "*.yaml",
        "*.yml",
        "*.xml",
        "*.csv",
        "*.sql",
    ],
    "exclude_patterns": [  # File patterns to exclude from versioning
        "*.log",
        "*.tmp",
        "*.temp",
        "*.swp",
        "*.bak",
        "*.backup",
        "*.pyc",
        "*.class",
        "*.o",
        "*.obj",
    ],
}

# Notification system settings
NOTIFICATION_SETTINGS = {
    "enabled": True,  # Master toggle for the notification system
    "retention_days": 30,  # How long to keep notifications (in days)
    "max_notifications_per_type": 1000,  # Maximum number of notifications to keep per type
    "notification_levels": [
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ],  # Valid notification levels
    "default_level": "INFO",  # Default notification level
    "channels": {
        "log": {
            "enabled": True,  # Whether to log notifications to the log file
            "min_level": "INFO",  # Minimum level to log
        },
        "email": {
            "enabled": False,  # Whether to send email notifications
            "min_level": "WARNING",  # Minimum level to send email
            "recipients": [],  # List of email recipients
            "from_address": "",  # From email address
            "subject_prefix": "[Aichemist Codex] ",  # Prefix for email subjects
        },
        "webhook": {
            "enabled": False,  # Whether to send webhook notifications
            "min_level": "WARNING",  # Minimum level to send webhook
            "endpoints": [],  # List of webhook endpoints
            "headers": {},  # Headers to send with webhook requests
        },
        "database": {
            "enabled": True,  # Whether to store notifications in the database
            "min_level": "INFO",  # Minimum level to store
            "max_age_days": 30,  # Maximum age of notifications to keep
        },
    },
    "throttling": {
        "enabled": True,  # Whether to throttle notifications
        "window_seconds": 60,  # Time window for throttling (in seconds)
        "max_similar": 5,  # Maximum number of similar notifications in the window
    },
}


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
