"""Test package for the AIchemist Codex."""

import pytest

# Define pytest markers
pytest.register_marker = lambda marker: None  # No-op function
pytest.register_marker("unit")
pytest.register_marker("integration")
pytest.register_marker("slow")
