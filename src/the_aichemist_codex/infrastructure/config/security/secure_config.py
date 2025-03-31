"""Provides secure configuration management with encryption."""

import base64
import json
import logging
import os
import platform
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from the_aichemist_codex.infrastructure.config.settings import determine_project_root

# Define DATA_DIR based on project root
PROJECT_ROOT = determine_project_root()
DATA_DIR = PROJECT_ROOT / "data"

logger = logging.getLogger(__name__)


class SecureConfigManager:
    """Manages secure storage and retrieval of sensitive configuration values."""

    def __init__(self, config_file: Path = DATA_DIR / "secure_config.enc") -> None:
        """
        Initialize secure configuration manager.

        Args:
            config_file: Path to the encrypted configuration file
        """
        self.config_file = config_file
        self._config: dict[str, Any] = {}
        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)
        self._load_config()

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key from environment or key file."""
        key_file = DATA_DIR / ".encryption_key"

        # Try to get key from environment
        env_key = os.environ.get("AICHEMIST_ENCRYPTION_KEY")
        if env_key:
            try:
                return base64.urlsafe_b64decode(env_key)
            except Exception as e:
                logger.error(f"Invalid encryption key in environment: {e}")

        # Try to load from key file
        if key_file.exists():
            try:
                with open(key_file, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading key file: {e}")

        # Generate new key
        logger.info("Generating new encryption key")
        key = Fernet.generate_key()

        # Save new key
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)

            # Set secure permissions if not on Windows
            if platform.system() != "Windows":
                os.chmod(key_file, 0o600)  # Secure permissions
            else:
                # On Windows, we can't easily set 0o600 equivalent
                # but we can try to make it readable only by the current user
                try:
                    import ntsecuritycon as con
                    import win32con
                    import win32security

                    # Get current user SID
                    username = os.environ.get("USERNAME")
                    if username:
                        sd = win32security.GetFileSecurity(
                            str(key_file), win32security.DACL_SECURITY_INFORMATION
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
                            str(key_file), win32security.DACL_SECURITY_INFORMATION, sd
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
        """Load and decrypt configuration from file."""
        if not self.config_file.exists():
            self._config = {}
            return

        try:
            with open(self.config_file, "rb") as f:
                encrypted_data = f.read()

            if encrypted_data:
                decrypted_data = self._fernet.decrypt(encrypted_data)
                self._config = json.loads(decrypted_data)
            else:
                self._config = {}
        except Exception as e:
            logger.error(f"Error loading secure configuration: {e}")
            self._config = {}

    def _save_config(self) -> None:
        """Encrypt and save configuration to file."""
        try:
            encrypted_data = self._fernet.encrypt(json.dumps(self._config).encode())

            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "wb") as f:
                f.write(encrypted_data)

            # Set secure permissions if not on Windows
            if platform.system() != "Windows":
                os.chmod(self.config_file, 0o600)  # Secure permissions
        except Exception as e:
            logger.error(f"Error saving secure configuration: {e}")

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
        """Clear all configuration values."""
        self._config.clear()
        self._save_config()

    def rotate_key(self) -> None:
        """Generate a new encryption key and re-encrypt configuration."""
        # Save current config
        current_config = self._config.copy()

        # Generate new key
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)

        # Save new key
        key_file = DATA_DIR / ".encryption_key"
        try:
            with open(key_file, "wb") as f:
                f.write(self._key)

            # Set secure permissions if not on Windows
            if platform.system() != "Windows":
                os.chmod(key_file, 0o600)
        except Exception as e:
            logger.error(f"Error saving new key file: {e}")
            return

        # Re-encrypt config with new key
        self._config = current_config
        self._save_config()


# Create a singleton instance for application-wide use
secure_config = SecureConfigManager()
