import json
from pathlib import Path
from unittest.mock import patch

import pytest

from project_generator.generator import ProjectGenerator


@pytest.fixture
def temp_dirs(tmp_path):
    """Creates temporary directories for testing."""
    template_dir = tmp_path / "templates"
    output_dir = tmp_path / "projects"
    template_dir.mkdir()
    output_dir.mkdir()
    return template_dir, output_dir


@pytest.fixture
def mock_logging():
    """Mock logging to suppress output during testing."""
    with patch("project_generator.generator.logging") as mock_log:
        yield mock_log


def test_create_project_success(temp_dirs, mock_logging):
    """Tests successful project creation."""
    print("Running test_create_project_success ✅")  # Debugging output
    template_dir, output_dir = temp_dirs
    generator = ProjectGenerator(str(template_dir), str(output_dir))

    project_name = "TestProject"
    generator.create_project(project_name)
    project_path = output_dir / project_name

    assert project_path.exists() and project_path.is_dir()


def test_save_project_structure(temp_dirs, mock_logging):
    """Tests saving the project structure with mocked project_reader functions."""
    template_dir, output_dir = temp_dirs
    generator = ProjectGenerator(str(template_dir), str(output_dir))

    project_name = "StructuredProject"
    project_path = output_dir / project_name
    project_path.mkdir()
    (project_path / "src").mkdir()
    (project_path / "src" / "main.py").write_text("print('Test')")

    with patch(
        "project_generator.generator.list_python_files",
        return_value=[Path("src/main.py")],  # ✅ Use Path object instead of string
    ):
        generator.save_project_structure(project_name)

    structure_file = project_path / "project_structure.json"
    assert structure_file.exists()

    with structure_file.open("r") as f:
        data = json.load(f)

    assert project_name in data

    # ✅ Normalize the path check to be OS-independent
    expected_path = str(Path("src/main.py")).replace("\\", "/")  # Convert Windows paths
    saved_paths = {p.replace("\\", "/") for p in data[project_name]}  # Normalize paths

    assert expected_path in saved_paths  # ✅ Check against normalized paths
