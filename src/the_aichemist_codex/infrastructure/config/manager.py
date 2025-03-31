"""Configuration management system for The AIchemist Codex."""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from .settings import PROJECT_ROOT

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "ignore_patterns": [
        "__pycache__",
        ".git",
        ".vscode",
        ".idea",
        "*.pyc",
        "*.pyo",
    ],
    "data_dir": None,  # Will be auto-populated
    "max_file_size_mb": 100,
    "scan_depth": 5,
    "extraction": {
        "enabled_extractors": ["text", "code", "document", "media"],
        "cache_results": True,
        "cache_ttl_seconds": 3600,
    },
    "parsing": {
        "max_preview_length": 1000,
        "fallback_to_text": True,
    },
    "file_organization": {
        "rules": [],
        "auto_organize": False,
    },
}


class ConfigManager:
    """
    Manages configuration settings for the application.

    Provides a singleton pattern for accessing configuration with
    merging of default values, environment overrides, and user settings.
    """

    _instance = None
    _initialized = False
    _config: dict[str, Any] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: Path | None = None):
        # Only initialize once
        if ConfigManager._initialized:
            return

        self._config = DEFAULT_CONFIG.copy()

        # Get config directory
        if config_path is None:
            self.config_dir = self._get_config_dir()
            self.config_path = self.config_dir / "config.json"
        else:
            self.config_path = config_path
            self.config_dir = config_path.parent

        # Ensure data directory is set
        if self._config["data_dir"] is None:
            self._config["data_dir"] = str(self._get_data_dir())

        # Load user config if it exists
        self._load_config()

        # Apply environment overrides
        self._apply_env_overrides()

        ConfigManager._initialized = True
        logger.debug(f"Configuration initialized from {self.config_path}")

    def _get_config_dir(self) -> Path:
        """Get configuration directory."""
        if env_config_dir := os.environ.get("AICHEMIST_CONFIG_DIR"):
            config_dir = Path(env_config_dir)
        else:
            if os.name == "nt":  # Windows
                config_dir = Path(os.environ.get("APPDATA", "")) / "AichemistCodex"
            else:  # Linux/Mac
                config_dir = Path.home() / ".aichemist"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _get_data_dir(self) -> Path:
        """Get data directory."""
        if env_data_dir := os.environ.get("AICHEMIST_DATA_DIR"):
            data_dir = Path(env_data_dir)
        else:
            data_dir = PROJECT_ROOT / "data"

        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    user_config = json.load(f)

                # Perform deep merge with default config
                self._deep_merge(self._config, user_config)
                logger.info(f"Loaded user configuration from {self.config_path}")
            else:
                # Write default config
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> None:
        """
        Deeply merge override dict into base dict.

        Args:
            base: Base dictionary to merge into
            override: Dictionary with values to override
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        prefix = "AICHEMIST_"
        for env_name, env_value in os.environ.items():
            if env_name.startswith(prefix):
                # Convert AICHEMIST_MAX_FILE_SIZE_MB to ["max_file_size_mb"]
                config_key = env_name[len(prefix) :].lower()

                # Handle nested keys like AICHEMIST_EXTRACTION_CACHE_TTL_SECONDS
                if "_" in config_key:
                    parts = config_key.split("_")

                    # Check if this could be a nested key
                    current = self._config
                    for i, part in enumerate(parts):
                        if (
                            part in current
                            and isinstance(current[part], dict)
                            and i < len(parts) - 1
                        ):
                            current = current[part]
                        else:
                            # Found the leaf level, set the value
                            try:
                                # Try to convert to appropriate type
                                if env_value.lower() in ("true", "yes", "1"):
                                    current[part] = True
                                elif env_value.lower() in ("false", "no", "0"):
                                    current[part] = False
                                elif env_value.isdigit():
                                    current[part] = int(env_value)
                                elif env_value.replace(".", "", 1).isdigit():
                                    current[part] = float(env_value)
                                else:
                                    current[part] = env_value

                                logger.debug(
                                    f"Applied environment override {env_name}={env_value}"
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to apply environment override {env_name}: {e}"
                                )
                            break

    def save_config(self) -> bool:
        """
        Save current configuration to file.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    @lru_cache(maxsize=128)
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key, can use dot notation for nested keys
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default
        """
        if "." in key:
            # Handle dot notation (e.g., "extraction.enabled_extractors")
            parts = key.split(".")
            current = self._config
            for part in parts:
                if part not in current:
                    return default
                current = current[part]
            return current
        else:
            # Simple top-level key
            return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key, can use dot notation for nested keys
            value: Value to set
        """
        if "." in key:
            # Handle dot notation (e.g., "extraction.enabled_extractors")
            parts = key.split(".")
            current = self._config
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    # Handle case where intermediate key exists but isn't a dict
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            # Simple top-level key
            self._config[key] = value

    def get_all(self) -> dict[str, Any]:
        """
        Get complete configuration.

        Returns:
            Dict: Full configuration
        """
        return self._config.copy()


# Create a singleton instance
config_manager = ConfigManager()


# Convenience function for getting config values
def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.

    Args:
        key: Configuration key, can use dot notation for nested keys
        default: Default value if key doesn't exist

    Returns:
        The configuration value or default
    """
    return config_manager.get(key, default)


def set_config(key: str, value: Any) -> None:
    """
    Set a configuration value.

    Args:
        key: Configuration key, can use dot notation for nested keys
        value: Value to set
    """
    config_manager.set(key, value)


def save_config() -> bool:
    """
    Save current configuration to file.

    Returns:
        bool: True if successful, False otherwise
    """
    return config_manager.save_config()
