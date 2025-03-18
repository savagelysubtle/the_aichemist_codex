"""
Secure configuration management with encryption.

This module provides functionality for securely storing and retrieving
sensitive configuration values using encryption.
"""

import base64
import json
import logging
import os
import platform
from typing import Any

from cryptography.fernet import Fernet

from ...core.exceptions import ConfigError
from ...registry import Registry

logger = logging.getLogger(__name__)


class SecureConfigManager:
    """Manages secure storage and retrieval of sensitive configuration values."""

    def __init__(self):
        """
        Initialize secure configuration manager.

        The encryption key and config file are determined based on project paths.
        """
        self._registry = Registry.get_instance()
        self._project_paths = self._registry.project_paths

        # Set up paths
        data_dir = self._project_paths.get_data_dir()
        self._config_file = data_dir / "secure_config.enc"
        self._key_file = data_dir / ".encryption_key"

        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)
        self._config: dict[str, Any] = {}
        self._load_config()

    def _get_or_create_key(self) -> bytes:
        """
        Get or create encryption key from environment or key file.

        Returns:
            Encryption key as bytes
        """
        # Try to get key from environment
        env_key = os.environ.get("AICHEMIST_ENCRYPTION_KEY")
        if env_key:
            try:
                return base64.urlsafe_b64decode(env_key)
            except Exception as e:
                logger.error(f"Invalid encryption key in environment: {e}")

        # Try to load from key file
        if self._key_file.exists():
            try:
                with open(self._key_file, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading key file: {e}")

        # Generate new key
        logger.info("Generating new encryption key")
        key = Fernet.generate_key()

        # Save new key
        try:
            self._key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._key_file, "wb") as f:
                f.write(key)

            # Set secure permissions if not on Windows
            if platform.system() != "Windows":
                os.chmod(self._key_file, 0o600)  # Secure permissions
            else:
                # On Windows, attempt to set limited permissions
                try:
                    import ntsecuritycon as con
                    import win32security

                    # Get current user SID
                    username = os.environ.get("USERNAME")
                    if username:
                        sd = win32security.GetFileSecurity(
                            str(self._key_file), win32security.DACL_SECURITY_INFORMATION
                        )
                        dacl = win32security.ACL()

                        # Add current user with read/write access
                        user_sid, _, _ = win32security.LookupAccountName(None, username)
                        dacl.AddAccessAllowedAce(
                            win32security.ACL_REVISION,
                            con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE,
                            user_sid,
                        )

                        # Set the DACL
                        sd.SetSecurityDescriptorDacl(1, dacl, 0)
                        win32security.SetFileSecurity(
                            str(self._key_file),
                            win32security.DACL_SECURITY_INFORMATION,
                            sd,
                        )
                except ImportError:
                    logger.warning(
                        "pywin32 not installed, cannot set Windows file permissions"
                    )
                except Exception as e:
                    logger.error(f"Error setting Windows file permissions: {e}")

        except Exception as e:
            logger.error(f"Error saving key file: {e}")

        return key

    def _load_config(self) -> None:
        """
        Load and decrypt configuration from file.

        Initializes an empty configuration if the file doesn't exist.
        """
        if not self._config_file.exists():
            self._config = {}
            return

        try:
            with open(self._config_file, "rb") as f:
                encrypted_data = f.read()

            if encrypted_data:
                decrypted_data = self._fernet.decrypt(encrypted_data)
                self._config = json.loads(decrypted_data)
            else:
                self._config = {}

            logger.debug(f"Loaded secure configuration from {self._config_file}")
        except Exception as e:
            logger.error(f"Error loading secure configuration: {e}")
            self._config = {}

    def _save_config(self) -> None:
        """
        Encrypt and save configuration to file.

        Raises:
            ConfigError: If the configuration cannot be saved
        """
        try:
            encrypted_data = self._fernet.encrypt(json.dumps(self._config).encode())

            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "wb") as f:
                f.write(encrypted_data)

            # Set secure permissions if not on Windows
            if platform.system() != "Windows":
                os.chmod(self._config_file, 0o600)  # Secure permissions

            logger.debug(f"Saved secure configuration to {self._config_file}")
        except Exception as e:
            logger.error(f"Error saving secure configuration: {e}")
            raise ConfigError(f"Failed to save secure configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Raises:
            ConfigError: If the configuration cannot be saved
        """
        self._config[key] = value
        self._save_config()

    def delete(self, key: str) -> bool:
        """
        Delete a configuration value.

        Args:
            key: Configuration key

        Returns:
            True if key existed and was deleted, False otherwise

        Raises:
            ConfigError: If the configuration cannot be saved
        """
        if key in self._config:
            del self._config[key]
            self._save_config()
            return True
        return False

    def get_all(self) -> dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary containing all configuration values
        """
        return self._config.copy()

    def clear(self) -> None:
        """
        Clear all configuration values.

        Raises:
            ConfigError: If the configuration cannot be saved
        """
        self._config.clear()
        self._save_config()

    def rotate_key(self) -> None:
        """
        Generate a new encryption key and re-encrypt configuration.

        Raises:
            ConfigError: If the key rotation fails
        """
        try:
            # Save current config
            current_config = self._config.copy()

            # Generate new key
            new_key = Fernet.generate_key()
            new_fernet = Fernet(new_key)

            # Save new key
            with open(self._key_file, "wb") as f:
                f.write(new_key)

            # Set secure permissions if not on Windows
            if platform.system() != "Windows":
                os.chmod(self._key_file, 0o600)

            # Update instance variables
            self._key = new_key
            self._fernet = new_fernet

            # Re-encrypt config with new key
            self._config = current_config
            self._save_config()

            logger.info("Encryption key rotated successfully")
        except Exception as e:
            logger.error(f"Error rotating encryption key: {e}")
            raise ConfigError(f"Failed to rotate encryption key: {e}")
