"""
Implementation of the ConfigProvider interface.

This module provides concrete implementation for configuration management,
addressing circular dependencies with other modules.
"""

import json
import os
from pathlib import Path
from typing import Any

import yaml

from ...core.exceptions import ConfigError
from ...core.interfaces import ConfigProvider
from ...registry import Registry


class ConfigProviderImpl(ConfigProvider):
    """Concrete implementation of the ConfigProvider interface."""

    def __init__(self):
        """Initialize the ConfigProvider instance."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._config_data: dict[str, Any] = {}
        self._config_file: Path | None = None

        # Load default configuration
        self._load_config()

    def _load_config(self) -> None:
        """
        Load configuration from default locations.

        The method checks for configuration files in the following order:
        1. Environment variable specified path
        2. Default config directory
        3. Project root directory

        If no configuration is found, a default one is created.
        """
        # Check for config file path in environment variable
        env_config_path = os.environ.get("AICHEMIST_CONFIG")
        if env_config_path:
            try:
                self.load_config_file(env_config_path)
                return
            except Exception:
                # If loading from env var fails, continue to next option
                pass

        # Try loading from default config directory
        config_dir = self._paths.get_config_dir()
        for config_name in ["config.yaml", "config.yml", "config.json"]:
            config_path = config_dir / config_name
            if config_path.exists():
                try:
                    self.load_config_file(str(config_path))
                    return
                except Exception:
                    # If loading fails, try next file
                    continue

        # Try loading from project root
        project_root = self._paths.get_project_root()
        for config_name in ["config.yaml", "config.yml", "config.json"]:
            config_path = project_root / config_name
            if config_path.exists():
                try:
                    self.load_config_file(str(config_path))
                    return
                except Exception:
                    # If loading fails, try next file
                    continue

        # If no config was found, create default
        self._create_default_config()

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "application": {
                "name": "The AIChemist Codex",
                "version": "0.1.0",
                "debug": False,
                "log_level": "INFO",
            },
            "security": {
                "allow_external_requests": False,
                "unsafe_patterns": [
                    r"\.\./",  # Directory traversal
                    r"~/",  # Home directory
                    r"^/",  # Absolute paths
                    r'[<>:"|?*]',  # Invalid characters for most filesystems
                ],
                "blocked_extensions": [
                    ".exe",
                    ".bat",
                    ".cmd",
                    ".com",
                    ".dll",
                    ".vbs",
                    ".js",
                    ".ps1",
                    ".sh",
                ],
            },
            "paths": {
                "allowed_paths": []  # Will be populated with project root and app dirs
            },
            "cache": {
                "ttl": 3600,  # 1 hour in seconds
                "max_size_mb": 1024,  # 1 GB
                "cleanup_interval": 3600,  # 1 hour in seconds
            },
            "performance": {
                "max_concurrent_tasks": 10,
                "default_timeout": 30,  # 30 seconds
                "chunk_size": 4096,
            },
        }

        # Add project root and app directories to allowed paths
        default_config["paths"]["allowed_paths"].append(
            str(self._paths.get_project_root())
        )
        default_config["paths"]["allowed_paths"].append(
            str(self._paths.get_app_data_dir())
        )

        # Save default config
        self._config_data = default_config
        self._config_file = self._paths.get_default_config_file()

        # Ensure config directory exists
        os.makedirs(self._config_file.parent, exist_ok=True)

        # Write the config file
        with open(self._config_file, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key (can be nested using dots, e.g., "security.allow_external_requests")
            default: Default value if the key doesn't exist

        Returns:
            The configuration value or default if not found
        """
        # Handle nested keys (e.g., "security.allow_external_requests")
        if "." in key:
            parts = key.split(".")
            current = self._config_data

            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]

            return current

        # Handle simple keys
        return self._config_data.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key (can be nested using dots, e.g., "security.allow_external_requests")
            value: The value to set
        """
        # Handle nested keys (e.g., "security.allow_external_requests")
        if "." in key:
            parts = key.split(".")
            current = self._config_data

            # Navigate to the parent of the leaf node
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    current[part] = {}

                current = current[part]

            # Set the value at the leaf node
            current[parts[-1]] = value
        else:
            # Handle simple keys
            self._config_data[key] = value

    def load_config_file(self, file_path: str) -> None:
        """
        Load configuration from a file.

        Args:
            file_path: Path to the configuration file

        Raises:
            ConfigError: If the file cannot be loaded
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            raise ConfigError(
                f"Configuration file does not exist: {file_path}", file_path
            )

        try:
            # Determine file type
            if path_obj.suffix.lower() in [".yaml", ".yml"]:
                self._load_yaml_config(path_obj)
            elif path_obj.suffix.lower() == ".json":
                self._load_json_config(path_obj)
            else:
                raise ConfigError(
                    f"Unsupported configuration file type: {path_obj.suffix}", file_path
                )

            # Store the config file path
            self._config_file = path_obj

        except Exception as e:
            if isinstance(e, ConfigError):
                raise

            raise ConfigError(f"Failed to load configuration file: {str(e)}", file_path)

    def _load_yaml_config(self, file_path: Path) -> None:
        """
        Load configuration from a YAML file.

        Args:
            file_path: Path to the YAML configuration file
        """
        with open(file_path) as f:
            self._config_data = yaml.safe_load(f) or {}

    def _load_json_config(self, file_path: Path) -> None:
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to the JSON configuration file
        """
        with open(file_path) as f:
            self._config_data = json.load(f)

    def save_config(self) -> None:
        """
        Save the current configuration to the default configuration file.

        Raises:
            ConfigError: If the configuration cannot be saved
        """
        if not self._config_file:
            self._config_file = self._paths.get_default_config_file()

        # Ensure directory exists
        os.makedirs(self._config_file.parent, exist_ok=True)

        try:
            # Save based on file extension
            if self._config_file.suffix.lower() in [".yaml", ".yml"]:
                with open(self._config_file, "w") as f:
                    yaml.dump(self._config_data, f, default_flow_style=False)
            elif self._config_file.suffix.lower() == ".json":
                with open(self._config_file, "w") as f:
                    json.dump(self._config_data, f, indent=2)
            else:
                # Default to YAML if extension is not recognized
                with open(self._config_file, "w") as f:
                    yaml.dump(self._config_data, f, default_flow_style=False)

        except Exception as e:
            raise ConfigError(
                f"Failed to save configuration: {str(e)}", str(self._config_file)
            )
