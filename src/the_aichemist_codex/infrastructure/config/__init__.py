"""Configuration management for the AIchemist Codex."""

from .manager import ConfigManager, config_manager, get_config, save_config, set_config
from .settings import *

# Export commonly used configuration functions and classes
__all__ = ["ConfigManager", "config_manager", "get_config", "set_config", "save_config"]
