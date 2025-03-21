"""
Configuration module for The Aichemist Codex.

This central aggregator exposes configuration settings and tools for:
- Loading configuration from .codexconfig (via the loader)
- Setting up logging (via the logging module)
- Secure configuration management (via the security module)
- File organization rules (via the rules module)
- Global settings and schema definitions (from settings and schemas)

The .codexconfig file (located at the root of this folder) contains user-defined configuration overrides.
"""

from .loader.config_loader import config as config_loader
from .logging.logging_config import setup_logging
from .security.secure_config import secure_config
from .rules.rules_engine import rules_engine
from .settings import *  # Exposes global constants (e.g., PROJECT_ROOT, DATA_DIR, etc.)
from .schemas import *  # Exposes schema definitions

__all__ = [
    "config_loader",
    "setup_logging",
    "secure_config",
    "rules_engine",
    # Global settings and schemas can also be imported via this central module if needed.
]
