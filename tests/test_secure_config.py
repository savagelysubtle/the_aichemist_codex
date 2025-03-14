"""Tests for secure configuration management."""

import os
from unittest.mock import patch

import pytest

from backend.config.secure_config import SecureConfigManager
from backend.config.settings import DATA_DIR


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def secure_config(temp_config_dir):
    """Create a SecureConfigManager instance with temporary files."""
    config_file = temp_config_dir / "secure_config.enc"
    return SecureConfigManager(config_file)


def test_init_creates_new_key(temp_config_dir, secure_config):
    """Test that initialization creates a new key when none exists."""
    key_file = DATA_DIR / ".encryption_key"
    assert key_file.exists()
    assert os.stat(key_file).st_mode & 0o777 == 0o600


def test_get_nonexistent_key(secure_config):
    """Test getting a nonexistent key returns the default value."""
    assert secure_config.get("nonexistent") is None
    assert secure_config.get("nonexistent", "default") == "default"


def test_set_and_get(secure_config):
    """Test setting and getting a configuration value."""
    secure_config.set("test_key", "test_value")
    assert secure_config.get("test_key") == "test_value"


def test_set_and_get_complex_value(secure_config):
    """Test setting and getting a complex configuration value."""
    complex_value = {"nested": {"key": "value", "list": [1, 2, 3], "bool": True}}
    secure_config.set("complex", complex_value)
    assert secure_config.get("complex") == complex_value


def test_delete_existing_key(secure_config):
    """Test deleting an existing configuration key."""
    secure_config.set("test_key", "test_value")
    assert secure_config.delete("test_key") is True
    assert secure_config.get("test_key") is None


def test_delete_nonexistent_key(secure_config):
    """Test deleting a nonexistent configuration key."""
    assert secure_config.delete("nonexistent") is False


def test_get_all(secure_config):
    """Test getting all configuration values."""
    test_config = {"key1": "value1", "key2": "value2"}
    for k, v in test_config.items():
        secure_config.set(k, v)

    assert secure_config.get_all() == test_config


def test_clear(secure_config):
    """Test clearing all configuration values."""
    secure_config.set("test_key", "test_value")
    secure_config.clear()
    assert secure_config.get_all() == {}


def test_persistence(temp_config_dir):
    """Test that configuration persists between instances."""
    config_file = temp_config_dir / "secure_config.enc"

    # First instance
    config1 = SecureConfigManager(config_file)
    config1.set("test_key", "test_value")

    # Second instance
    config2 = SecureConfigManager(config_file)
    assert config2.get("test_key") == "test_value"


def test_key_rotation(secure_config):
    """Test key rotation functionality."""
    # Set initial value
    secure_config.set("test_key", "test_value")

    # Rotate key
    secure_config.rotate_key()

    # Verify value is still accessible
    assert secure_config.get("test_key") == "test_value"

    # Verify key file was updated
    key_file = DATA_DIR / ".encryption_key"
    assert key_file.exists()
    assert os.stat(key_file).st_mode & 0o777 == 0o600


def test_environment_key(temp_config_dir):
    """Test using encryption key from environment."""
    test_key = b"test_key_123456789012345678901234567890=="
    with patch.dict(os.environ, {"AICHEMIST_ENCRYPTION_KEY": test_key.decode()}):
        config = SecureConfigManager(temp_config_dir / "secure_config.enc")
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"


def test_invalid_config_file(secure_config):
    """Test handling of invalid configuration file."""
    # Write invalid data to config file
    with open(secure_config.config_file, "wb") as f:
        f.write(b"invalid data")

    # Create new instance - should handle error gracefully
    config = SecureConfigManager(secure_config.config_file)
    assert config.get_all() == {}
