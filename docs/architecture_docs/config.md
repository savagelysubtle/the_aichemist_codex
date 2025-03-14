# Configuration Package Documentation

## Overview

The Configuration package provides essential configuration management, logging setup, rules processing, and settings handling for The Aichemist Codex. It implements a streamlined approach to configuration with TOML-based settings, comprehensive file ignore patterns, structured logging, and secure storage for sensitive configuration values.

## Components

### 1. Config Loader (config_loader.py)

- Implements singleton pattern for configuration management
- Uses TOML for configuration files
- Provides default fallback settings
- Supports dynamic configuration updates
- Example usage:

  ```python
  from config_loader import config
  max_file_size = config.get("max_file_size")
  ```

### 2. Secure Configuration Manager (secure_config.py)

- Provides encrypted storage for sensitive configuration values
- Uses Fernet symmetric encryption for data security
- Supports key rotation for enhanced security
- Handles environment variable-based key configuration
- Cross-platform secure file permissions
- Example usage:

  ```python
  from backend.config.secure_config import secure_config

  # Store sensitive data
  secure_config.set("api_key", "secret-api-key-value")

  # Retrieve sensitive data
  api_key = secure_config.get("api_key")

  # Rotate encryption key periodically
  secure_config.rotate_key()
  ```

### 3. Logging Config (logging_config.py)

- Configures global logging settings
- Implements dual logging (file and stdout)
- Uses standardized log format
- Automatically creates log directories
- Configuration:
  ```python
  format="%(asctime)s - %(levelname)s - %(message)s"
  handlers=[
      logging.FileHandler(LOG_FILE),
      logging.StreamHandler(sys.stdout)
  ]
  ```

### 4. Rules Engine (rules_engine.py)

- Manages file ignore patterns
- Implements pattern matching logic
- Provides safe file handling rules
- Example:
  ```python
  from rules_engine import rules_engine
  if rules_engine.should_ignore(file_path):
      # Skip file processing
  ```

### 5. Schemas (schemas.py)

- Defines JSON schemas for data validation
- Supports file tree structure validation
- Implements code summary validation
- Key schemas:

  ```json
  file_tree_schema = {
      "type": "object",
      "patternProperties": {".*": {"type": ["object", "null"]}}
  }

  code_summary_schema = {
      "type": "object",
      "patternProperties": {
          ".*": {
              "type": "array",
              "items": {
                  "type": "object",
                  "properties": {
                      "type": {"type": "string"},
                      "name": {"type": "string"},
                      "args": {"type": "array"},
                      "lineno": {"type": "integer"}
                  }
              }
          }
      }
  }
  ```

### 6. Settings (settings.py)

- Defines global configuration constants
- Manages directory paths:
  - ROOT_DIR: Root directory
  - DATA_DIR: Data storage
  - LOG_DIR: Log files
  - EXPORT_DIR: Export outputs
  - CACHE_DIR: Cache storage
- Implements comprehensive ignore patterns
- Sets system limits and parameters:
  - MAX_FILE_SIZE: 50MB
  - CHUNK_SIZE: 64KB for streaming operations
  - MAX_BATCH_SIZE: 100 items
  - MAX_TOKENS: 8000
  - CACHE_TTL: 3600 seconds (1 hour)
  - THREAD_POOL_SIZE: Based on CPU count
- Search settings:
  - MAX_SEARCH_RESULTS: 1000
  - SEARCH_CACHE_TTL: 300 seconds (5 minutes)
  - MIN_SEARCH_TERM_LENGTH: 3
- Regex search settings:
  - REGEX_MAX_COMPLEXITY: 1000 (complexity score limit)
  - REGEX_TIMEOUT_MS: 500 (timeout for regex operations)
  - REGEX_CACHE_TTL: 300 seconds (5 minutes)
  - REGEX_MAX_RESULTS: 100
- Security settings:
  - PASSWORD_MIN_LENGTH: 12 characters
  - PASSWORD_COMPLEXITY: Requirements for different character types
  - TOKEN_EXPIRY: 3600 seconds (1 hour)
  - MAX_LOGIN_ATTEMPTS: 5 attempts
  - LOGIN_COOLDOWN: 300 seconds (5 minutes)
- Feature flags for enabling/disabling functionality:
  - enable_caching
  - enable_compression
  - enable_rate_limiting
  - enable_batch_processing
  - enable_async_processing
  - enable_regex_search

## Implementation Details

### Configuration Management

- Uses singleton pattern for global access
- Loads from TOML configuration files
- Provides default values for all settings
- Supports environment-specific configurations

### Secure Configuration Storage

- Encrypts sensitive configuration data
- Supports key rotation for periodic security updates
- Provides environment variable-based key configuration
- Implements secure file permissions
- Handles cross-platform security differences

### Logging System

- Centralizes log configuration
- Supports both file and console output
- Uses consistent formatting
- Automatically manages log directories

### Rules Processing

- Simple and efficient pattern matching
- Extensive ignore patterns list
- Safe file handling checks
- Easy pattern customization

### Schema Validation

- JSON Schema based validation
- Supports complex nested structures
- Validates file trees and code summaries
- Enforces data structure consistency

## Integration Points

### Internal Dependencies

- Utils package for common operations
- File Manager for file operations
- Project Reader for code analysis
- Output Formatter for data export

### External Dependencies

- Python standard library (pathlib, logging)
- TOML for configuration files
- JSON Schema for validation
- Cryptography for secure configuration
- PyWin32 for Windows file permissions (optional)

## Testing

The configuration package includes comprehensive tests:

- test_config_loader.py
- test_logging_config.py
- test_rules_engine.py
- test_schemas.py
- test_settings.py
- test_secure_config.py

## Future Improvements

### Short-term

- Configuration hot-reload support
- Enhanced validation for configuration values
- Expanded schema definitions
- Additional ignore patterns for new file types
- Secure configuration backup and recovery

### Long-term

- Remote configuration support
- Configuration versioning
- Dynamic rule updates
- Advanced logging features (log rotation, compression)
- Hardware-based encryption key storage
- Multi-factor authentication for sensitive configuration access
