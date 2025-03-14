"""Global settings and configuration constants."""

import os
from pathlib import Path

# Base directories
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = DATA_DIR / "logs"

# Ensure directories exist with proper permissions
for directory in [DATA_DIR, CACHE_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)  # Secure directory permissions

# Cache settings
CACHE_TTL = 3600  # 1 hour in seconds
MAX_CACHE_SIZE = 1024 * 1024 * 100  # 100MB
MAX_MEMORY_CACHE_ITEMS = 1000

# File processing settings
MAX_FILE_SIZE = 1024 * 1024 * 50  # 50MB
CHUNK_SIZE = 1024 * 64  # 64KB chunks for file operations
MAX_BATCH_SIZE = 100  # Maximum items in a batch operation

# Search settings
MAX_SEARCH_RESULTS = 1000
SEARCH_CACHE_TTL = 300  # 5 minutes
MIN_SEARCH_TERM_LENGTH = 3

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
}
