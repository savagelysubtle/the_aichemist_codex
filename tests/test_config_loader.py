# test_config_loader.py
from src.config.config_loader import CodexConfig


def test_default_config(tmp_path, monkeypatch):
    # Create a temporary config directory with an empty config file.
    temp_config_dir = tmp_path / "config"
    temp_config_dir.mkdir()
    config_file = temp_config_dir / ".codexconfig"
    config_file.write_text("", encoding="utf-8")

    # Override the CONFIG_FILE variable in config_loader.
    monkeypatch.setattr("backend.src.config.config_loader.CONFIG_FILE", config_file)

    config = CodexConfig()
    # Check that essential default settings are present.
    assert "ignore_patterns" in config.settings
    assert "max_file_size" in config.settings
