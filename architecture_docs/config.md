# Configuration Package Documentation

## Overview

The Configuration package provides essential configuration management, logging setup, rules processing, and settings handling for The Aichemist Codex. It implements a streamlined approach to configuration with TOML-based settings, comprehensive file ignore patterns, and structured logging.

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

### 2. Logging Config (logging_config.py)
Configures global logging settings
Implements dual logging (file and stdout)
Uses standardized log format
Automatically creates log directories
Configuration:
format="%(asctime)s - %(levelname)s - %(message)s"
handlers=[
    logging.FileHandler(LOG_FILE),
    logging.StreamHandler(sys.stdout)
]

### 3. Rules Engine (rules_engine.py)
Manages file ignore patterns
Implements pattern matching logic
Provides safe file handling rules
Example:
from rules_engine import rules_engine
if rules_engine.should_ignore(file_path):

   ### Skip file processing

### 4. Schemas (schemas.py)
Defines JSON schemas for data validation
Supports file tree structure validation
Implements code summary validation
Key schemas:

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

### 5. Settings (settings.py)
Defines global configuration constants
Manages directory paths:
BASE_DIR: Root directory
DATA_DIR: Data storage
LOG_DIR: Log files
EXPORT_DIR: Export outputs
CACHE_DIR: Cache storage
Implements comprehensive ignore patterns for:
Python files and caches
JavaScript/Node modules
Java build files
C/C++ binaries
Swift/Xcode files
Ruby gems
Rust targets
Go packages
.NET/C# builds
Version control
Media files
Virtual environments
IDE files
Temporary files
Build artifacts
Documentation
Sets system limits:
MAX_FILE_SIZE: 10MB
MAX_TOKENS: 8000
Implementation Details
Configuration Management
Uses singleton pattern for global access
Loads from TOML configuration files
Provides default values for all settings
Supports environment-specific configurations
Logging System
Centralizes log configuration
Supports both file and console output
Uses consistent formatting
Automatically manages log directories
Rules Processing
Simple and efficient pattern matching
Extensive ignore patterns list
Safe file handling checks
Easy pattern customization
Schema Validation
JSON Schema based validation
Supports complex nested structures
Validates file trees and code summaries
Enforces data structure consistency
Integration Points
Internal Dependencies
Utils package for common operations
File Manager for file operations
Project Reader for code analysis
Output Formatter for data export
External Dependencies
Python standard library (pathlib, logging)
TOML for configuration files
JSON Schema for validation
Testing
The configuration package includes comprehensive tests:

test_config_loader.py
test_logging_config.py
test_rules_engine.py
test_schemas.py
test_settings.py
Future Improvements
Short-term
Configuration hot-reload support
Enhanced validation for configuration values
Expanded schema definitions
Additional ignore patterns for new file types
Long-term
Remote configuration support
Configuration versioning
Dynamic rule updates
Advanced logging features (log rotation, compression)
