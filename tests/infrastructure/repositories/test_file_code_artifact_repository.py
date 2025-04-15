"""Tests for the FileCodeArtifactRepository class."""

import json
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.exceptions.repository_exception import RepositoryError
from the_aichemist_codex.infrastructure.repositories.file_code_artifact_repository import (
    FileCodeArtifactRepository,
)


@pytest.mark.integration
class TestFileCodeArtifactRepository:
    """Test cases for the FileCodeArtifactRepository class."""

    def setup_method(self):
        """Set up the test repository."""
        # Create a temporary directory for the repository
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repository = FileCodeArtifactRepository(self.temp_dir)

        # Create a sample artifact for testing
        self.sample_artifact = CodeArtifact(
            id=uuid4(),
            path=Path("/path/to/file.py"),
            name="file.py",
            artifact_type="python_module",
            content="def hello_world():\n    print('Hello, world!')",
            metadata={"language": "python", "loc": 2},
        )

    def teardown_method(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test repository initialization."""
        # Assert that the storage directory was created
        assert self.temp_dir.exists()
        assert self.temp_dir.is_dir()

    def test_save_artifact(self):
        """Test saving an artifact."""
        # Act
        saved_artifact = self.repository.save(self.sample_artifact)

        # Assert
        assert saved_artifact == self.sample_artifact

        # Check that the file was created
        artifact_path = self.temp_dir / f"{self.sample_artifact.id!s}.json"
        assert artifact_path.exists()

        # Verify the file content
        with open(artifact_path, encoding="utf-8") as f:
            data = json.load(f)
            assert data["id"] == str(self.sample_artifact.id)
            assert data["name"] == self.sample_artifact.name
            assert data["path"] == str(self.sample_artifact.path)
            assert data["artifact_type"] == self.sample_artifact.artifact_type
            assert data["content"] == self.sample_artifact.content
            assert data["metadata"] == self.sample_artifact.metadata

    def test_get_by_id(self):
        """Test retrieving an artifact by ID."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Act
        retrieved_artifact = self.repository.get_by_id(self.sample_artifact.id)

        # Assert
        assert retrieved_artifact is not None
        assert retrieved_artifact.id == self.sample_artifact.id
        assert retrieved_artifact.name == self.sample_artifact.name
        assert str(retrieved_artifact.path) == str(self.sample_artifact.path)
        assert retrieved_artifact.artifact_type == self.sample_artifact.artifact_type
        assert retrieved_artifact.content == self.sample_artifact.content
        assert retrieved_artifact.metadata == self.sample_artifact.metadata

    def test_get_by_id_nonexistent(self):
        """Test retrieving a nonexistent artifact by ID."""
        # Act
        retrieved_artifact = self.repository.get_by_id(uuid4())

        # Assert
        assert retrieved_artifact is None

    def test_get_by_path(self):
        """Test retrieving an artifact by path."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Act
        retrieved_artifact = self.repository.get_by_path(self.sample_artifact.path)

        # Assert
        assert retrieved_artifact is not None
        assert retrieved_artifact.id == self.sample_artifact.id

    def test_get_by_name(self):
        """Test retrieving artifacts by name."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Create another artifact with the same name
        another_artifact = CodeArtifact(
            path=Path("/path/to/another/file.py"), name="file.py"
        )
        self.repository.save(another_artifact)

        # Act
        artifacts = self.repository.get_by_name("file.py")

        # Assert
        assert len(artifacts) == 2
        assert any(a.id == self.sample_artifact.id for a in artifacts)
        assert any(a.id == another_artifact.id for a in artifacts)

    def test_find_all(self):
        """Test retrieving all artifacts."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Create another artifact
        another_artifact = CodeArtifact(
            path=Path("/path/to/another/file.py"), name="another_file.py"
        )
        self.repository.save(another_artifact)

        # Act
        artifacts = self.repository.find_all()

        # Assert
        assert len(artifacts) == 2
        assert any(a.id == self.sample_artifact.id for a in artifacts)
        assert any(a.id == another_artifact.id for a in artifacts)

    def test_find_by_criteria(self):
        """Test finding artifacts by criteria."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Create another artifact
        another_artifact = CodeArtifact(
            path=Path("/path/to/another/file.py"),
            name="another_file.py",
            artifact_type="python_module",
        )
        self.repository.save(another_artifact)

        # Act
        artifacts = self.repository.find_by_criteria({"artifact_type": "python_module"})

        # Assert
        assert len(artifacts) == 2

        # Test more specific criteria
        artifacts = self.repository.find_by_criteria({"name": "file.py"})
        assert len(artifacts) == 1
        assert artifacts[0].id == self.sample_artifact.id

    def test_delete(self):
        """Test deleting an artifact."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Act
        result = self.repository.delete(self.sample_artifact.id)

        # Assert
        assert result is True

        # Check that the file was deleted
        artifact_path = self.temp_dir / f"{self.sample_artifact.id!s}.json"
        assert not artifact_path.exists()

        # Check that the artifact is no longer retrievable
        assert self.repository.get_by_id(self.sample_artifact.id) is None

    def test_delete_nonexistent(self):
        """Test deleting a nonexistent artifact."""
        # Act
        result = self.repository.delete(uuid4())

        # Assert
        assert result is False

    def test_error_handling(self):
        """Test error handling when the storage directory is not accessible."""
        # Arrange - create a directory that is not writable
        read_only_dir = Path(tempfile.mkdtemp())

        try:
            # Create a file in place of a directory to cause an error
            test_file = read_only_dir / "test_file"
            test_file.touch()

            # Act/Assert - this should raise a RepositoryError
            with pytest.raises(RepositoryError):
                repository = FileCodeArtifactRepository(test_file)
        finally:
            # Clean up
            shutil.rmtree(read_only_dir)

    def test_caching(self):
        """Test that the repository caches artifacts."""
        # Arrange
        self.repository.save(self.sample_artifact)

        # Act - get the artifact twice
        first_retrieval = self.repository.get_by_id(self.sample_artifact.id)

        # Modify the file to check if the cache is being used
        artifact_path = self.temp_dir / f"{self.sample_artifact.id!s}.json"
        with open(artifact_path, encoding="utf-8") as f:
            data = json.load(f)

        data["name"] = "modified_name.py"

        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        second_retrieval = self.repository.get_by_id(self.sample_artifact.id)

        # Assert
        assert first_retrieval is not None
        assert second_retrieval is not None
        assert first_retrieval.name == "file.py"  # Original name
        assert second_retrieval.name == "file.py"  # Still using cached version

        # Force reload by clearing the cache
        self.repository._cache = {}
        third_retrieval = self.repository.get_by_id(self.sample_artifact.id)

        # Assert
        assert third_retrieval is not None
        assert third_retrieval.name == "modified_name.py"  # Now has the modified name
