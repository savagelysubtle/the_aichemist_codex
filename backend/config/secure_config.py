"""Provides secure configuration management with encryption."""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.config.settings import DATA_DIR

logger = logging.getLogger(__name__)


class SecureConfigManager:
    """Manages secure storage and retrieval of sensitive configuration values."""

    def __init__(self, config_file: Path = DATA_DIR / "secure_config.enc"):
        """
        Initialize secure configuration manager.

        Args:
            config_file: Path to the encrypted configuration file
        """
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
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
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))

        # Save new key
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Secure permissions
        except Exception as e:
            logger.error(f"Error saving key file: {e}")

        return key

    def _load_config(self):
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

    def _save_config(self):
        """Encrypt and save configuration to file."""
        try:
            encrypted_data = self._fernet.encrypt(json.dumps(self._config).encode())

            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "wb") as f:
                f.write(encrypted_data)
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

    def get_all(self) -> Dict[str, Any]:
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
        self._key = base64.urlsafe_b64encode(os.urandom(32))
        self._fernet = Fernet(self._key)

        # Save new key
        key_file = DATA_DIR / ".encryption_key"
        try:
            with open(key_file, "wb") as f:
                f.write(self._key)
            os.chmod(key_file, 0o600)
        except Exception as e:
            logger.error(f"Error saving new key file: {e}")
            return

        # Re-encrypt config with new key
        self._config = current_config
        self._save_config()


# Create a singleton instance for application-wide use
secure_config = SecureConfigManager()
