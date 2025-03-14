# Configuration Package

## Overview

The Configuration package provides essential configuration management, logging setup, rules processing, and settings handling for The Aichemist Codex. It implements a streamlined approach to configuration with TOML-based settings, comprehensive file ignore patterns, structured logging, and secure storage for sensitive configuration values.

## Components

### 1. Config Loader (`config_loader.py`)

Provides a centralized configuration management system using TOML files.

```python
from backend.config.config_loader import config

# Access configuration values
max_file_size = config.get("max_file_size")
log_level = config.get("log_level", "INFO")  # With default value
```

### 2. Secure Configuration Manager (`secure_config.py`)

Provides encrypted storage for sensitive configuration values like API keys, credentials, and other secrets.

```python
from backend.config.secure_config import secure_config

# Store sensitive data
secure_config.set("api_key", "secret-api-key-value")

# Retrieve sensitive data
api_key = secure_config.get("api_key")

# Delete a configuration value
secure_config.delete("old_key")

# Get all configuration values
all_config = secure_config.get_all()

# Clear all configuration
secure_config.clear()

# Rotate encryption key periodically for enhanced security
secure_config.rotate_key()
```

#### Security Features

- **Encryption**: Uses Fernet symmetric encryption for data security
- **Key Management**:
  - Loads from environment variable `AICHEMIST_ENCRYPTION_KEY` if available
  - Falls back to key file stored in `DATA_DIR/.encryption_key`
  - Generates new key if neither exists
- **Key Rotation**: Supports periodic key rotation while preserving data
- **Secure Storage**: Implements secure file permissions
- **Cross-Platform**: Handles security differences between Unix and Windows

### 3. Settings (`settings.py`)

Defines global configuration constants and default values.

```python
from backend.config.settings import MAX_FILE_SIZE, CACHE_TTL, FEATURES

# Use configuration constants
if file_size > MAX_FILE_SIZE:
    raise ValueError(f"File too large (max: {MAX_FILE_SIZE} bytes)")

# Check feature flags
if FEATURES["enable_caching"]:
    # Use caching functionality
```

#### Key Settings

- **Directory Paths**: `ROOT_DIR`, `DATA_DIR`, `CACHE_DIR`, `LOG_DIR`, `EXPORT_DIR`
- **File Processing**: `MAX_FILE_SIZE`, `CHUNK_SIZE`, `MAX_BATCH_SIZE`
- **Caching**: `CACHE_TTL`, `MAX_CACHE_SIZE`, `MAX_MEMORY_CACHE_ITEMS`
- **Security**: `PASSWORD_MIN_LENGTH`, `PASSWORD_COMPLEXITY`, `TOKEN_EXPIRY`
- **Performance**: `THREAD_POOL_SIZE`, `TASK_QUEUE_SIZE`, `RATE_LIMIT`
- **Feature Flags**: `FEATURES` dictionary for enabling/disabling functionality

### 4. Logging Config (`logging_config.py`)

Configures global logging settings with standardized formats.

```python
from backend.config.logging_config import setup_logging

# Initialize logging
setup_logging()

# Use logger
import logging
logger = logging.getLogger(__name__)
logger.info("Operation completed successfully")
logger.error("An error occurred: %s", error_message)
```

## Dependencies

The configuration package relies on the following dependencies (defined in `pyproject.toml`):

- **Core Dependencies**:
  - `tomli`: For TOML configuration file parsing
  - `cryptography`: For secure configuration encryption
  - `python-dotenv`: For environment variable loading

- **Windows-specific Dependencies** (optional):
  - `pywin32`: For secure file permissions on Windows platforms

## Best Practices

1. **Sensitive Data**: Always use `secure_config` for storing sensitive information like:
   - API keys
   - Database credentials
   - Authentication tokens
   - User secrets

2. **Configuration Access**: Use the appropriate configuration source:
   - `settings.py` for constants and default values
   - `config_loader.py` for user-configurable settings
   - `secure_config.py` for sensitive data

3. **Key Rotation**: Implement periodic key rotation for enhanced security:

   ```python
   # Schedule this to run periodically (e.g., monthly)
   secure_config.rotate_key()
   ```

4. **Environment Variables**: For production deployments, use environment variables:

   ```bash
   # Set encryption key via environment variable
   export AICHEMIST_ENCRYPTION_KEY="your-base64-encoded-key"
   ```

## Testing

The configuration package includes comprehensive tests:

```bash
# Run all tests
python -m pytest tests/test_config_loader.py tests/test_secure_config.py tests/test_settings.py

# Run specific test
python -m pytest tests/test_secure_config.py::test_key_rotation
```
