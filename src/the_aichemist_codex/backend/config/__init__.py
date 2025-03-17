"""
Configuration module for The Aichemist Codex.

This module provides configuration settings and utilities for the application,
including settings for file paths, permissions, and application behavior.

Available configuration options:
- Base directories (PROJECT_ROOT, DATA_DIR, etc.)
- Security settings
- Logging configuration
- File processing limits and rules

Data Directory Configuration:
The data directory can be configured using environment variables:
- AICHEMIST_ROOT_DIR: Set the project root directory
- AICHEMIST_DATA_DIR: Set the data directory directly

If not specified, the system will automatically detect appropriate directories.
"""

# ✅ Ensure consistent import reference
from .config_loader import config
from .logging_config import setup_logging

__all__ = ["config", "setup_logging"]
