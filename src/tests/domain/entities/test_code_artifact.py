"""Tests for the CodeArtifact entity."""

from pathlib import Path
from uuid import UUID

import pytest

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.exceptions.validation_exception import (
    ValidationException,
)


@pytest.mark.unit
class TestCodeArtifact:
    """Test cases for the CodeArtifact entity."""

    def test_create_code_artifact_with_minimum_attributes(self):
        """Test creation of a CodeArtifact with minimum required attributes."""
        # Arrange
        path = Path("/path/to/file.py")
        name = "file.py"

        # Act
        artifact = CodeArtifact(path=path, name=name)

        # Assert
        assert artifact.id is not None
        assert isinstance(artifact.id, UUID)
        assert artifact.path == path
        assert artifact.name == name
        assert artifact.artifact_type == "file"
        assert artifact.content is None
        assert artifact.metadata == {}
        assert artifact.is_valid is True

    def test_create_code_artifact_with_all_attributes(self):
        """Test creation of a CodeArtifact with all attributes."""
        # Arrange
        path = Path("/path/to/file.py")
        name = "file.py"
        artifact_type = "python_module"
        content = "def hello_world():\n    print('Hello, world!')"
        metadata = {"language": "python", "loc": 2}

        # Act
        artifact = CodeArtifact(
            path=path,
            name=name,
            artifact_type=artifact_type,
            content=content,
            metadata=metadata,
        )

        # Assert
        assert artifact.id is not None
        assert artifact.path == path
        assert artifact.name == name
        assert artifact.artifact_type == artifact_type
        assert artifact.content == content
        assert artifact.metadata == metadata
        assert artifact.is_valid is True

    def test_code_artifact_equality(self):
        """Test that two CodeArtifacts with the same ID are considered equal."""
        # Arrange
        artifact1 = CodeArtifact(path=Path("/path/to/file.py"), name="file.py")
        # Create a copy with the same ID
        artifact2 = CodeArtifact(
            id=artifact1.id, path=Path("/path/to/file.py"), name="file.py"
        )
        # Create a different artifact
        artifact3 = CodeArtifact(path=Path("/path/to/other.py"), name="other.py")

        # Assert
        assert artifact1 == artifact2
        assert artifact1 != artifact3
        assert artifact2 != artifact3

    def test_code_artifact_invalid_path(self):
        """Test validation for invalid path."""
        # Act/Assert
        with pytest.raises(ValidationException) as exc_info:
            CodeArtifact(path=None, name="file.py")

        assert "path is required" in str(exc_info.value)

    def test_code_artifact_invalid_name(self):
        """Test validation for invalid name."""
        # Act/Assert
        with pytest.raises(ValidationException) as exc_info:
            CodeArtifact(path=Path("/path/to/file.py"), name="")

        assert "name cannot be empty" in str(exc_info.value)

    def test_code_artifact_string_representation(self):
        """Test the string representation of a CodeArtifact."""
        # Arrange
        artifact = CodeArtifact(path=Path("/path/to/file.py"), name="file.py")

        # Act
        str_representation = str(artifact)

        # Assert
        assert "file.py" in str_representation
        assert str(artifact.id) in str_representation

    def test_update_metadata(self):
        """Test updating metadata of a CodeArtifact."""
        # Arrange
        artifact = CodeArtifact(
            path=Path("/path/to/file.py"),
            name="file.py",
            metadata={"language": "python"},
        )

        # Act
        artifact.update_metadata({"loc": 100, "complexity": 5})

        # Assert
        assert artifact.metadata == {"language": "python", "loc": 100, "complexity": 5}

    def test_get_snippet(self):
        """Test getting a code snippet from a CodeArtifact."""
        # Arrange
        content = "line 1\nline 2\nline 3\nline 4\nline 5"
        artifact = CodeArtifact(
            path=Path("/path/to/file.py"), name="file.py", content=content
        )

        # Act
        snippet = artifact.get_snippet(start_line=2, end_line=4)

        # Assert
        assert snippet == "line 2\nline 3\nline 4"

    def test_get_snippet_out_of_range(self):
        """Test getting a snippet with out-of-range line numbers."""
        # Arrange
        content = "line 1\nline 2\nline 3"
        artifact = CodeArtifact(
            path=Path("/path/to/file.py"), name="file.py", content=content
        )

        # Act/Assert
        with pytest.raises(ValueError) as exc_info:
            artifact.get_snippet(start_line=2, end_line=10)

        assert "end_line exceeds content length" in str(exc_info.value)

    def test_parse_content(self):
        """Test parsing content of a CodeArtifact."""
        # Arrange
        path = Path("/path/to/file.py")
        name = "file.py"
        artifact = CodeArtifact(path=path, name=name)
        content = "def hello_world():\n    print('Hello, world!')"

        # Act
        artifact.parse_content(content)

        # Assert
        assert artifact.content == content
        assert artifact.metadata.get("parsed") is True
        assert "loc" in artifact.metadata
