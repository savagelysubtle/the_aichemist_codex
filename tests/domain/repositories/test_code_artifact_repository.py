"""Tests for the CodeArtifactRepository interface."""

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.exceptions.repository_exception import RepositoryError
from the_aichemist_codex.domain.repositories.code_artifact_repository import (
    CodeArtifactRepository,
)


class MockCodeArtifactRepository(CodeArtifactRepository):
    """A mock implementation of the CodeArtifactRepository for testing."""

    def __init__(self):
        """Initialize the mock repository."""
        self.artifacts: dict[UUID, CodeArtifact] = {}
        self.error_mode = False

    def set_error_mode(self, enabled: bool):
        """Set the repository to raise errors for testing error handling."""
        self.error_mode = enabled

    def save(self, artifact: CodeArtifact) -> CodeArtifact:
        """Save a code artifact to the repository."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to save artifact",
                entity_type="CodeArtifact",
                operation="save",
                entity_id=str(artifact.id),
            )
        self.artifacts[artifact.id] = artifact
        return artifact

    def get_by_id(self, artifact_id: UUID) -> CodeArtifact | None:
        """Retrieve a code artifact by its ID."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to get artifact by ID",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )
        return self.artifacts.get(artifact_id)

    def get_by_path(self, path: Path) -> CodeArtifact | None:
        """Retrieve a code artifact by its path."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to get artifact by path",
                entity_type="CodeArtifact",
                operation="get_by_path",
            )

        for artifact in self.artifacts.values():
            if str(artifact.path) == str(path):
                return artifact
        return None

    def get_by_name(self, name: str) -> list[CodeArtifact]:
        """Retrieve code artifacts by name."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to get artifacts by name",
                entity_type="CodeArtifact",
                operation="get_by_name",
            )

        return [a for a in self.artifacts.values() if a.name == name]

    def find_all(self) -> list[CodeArtifact]:
        """Retrieve all code artifacts in the repository."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to find all artifacts",
                entity_type="CodeArtifact",
                operation="find_all",
            )

        return list(self.artifacts.values())

    def find_by_criteria(self, criteria: dict) -> list[CodeArtifact]:
        """Find code artifacts matching the given criteria."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to find artifacts by criteria",
                entity_type="CodeArtifact",
                operation="find_by_criteria",
            )

        result = []
        for artifact in self.artifacts.values():
            matches = True
            for key, value in criteria.items():
                if not hasattr(artifact, key) or getattr(artifact, key) != value:
                    matches = False
                    break
            if matches:
                result.append(artifact)
        return result

    def delete(self, artifact_id: UUID) -> bool:
        """Delete a code artifact from the repository."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to delete artifact",
                entity_type="CodeArtifact",
                operation="delete",
                entity_id=str(artifact_id),
            )

        if artifact_id in self.artifacts:
            del self.artifacts[artifact_id]
            return True
        return False

    def get_children(self, artifact_id: UUID) -> list[CodeArtifact]:
        """Get child artifacts of the specified artifact."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to get children",
                entity_type="CodeArtifact",
                operation="get_children",
                entity_id=str(artifact_id),
            )

        # Mock implementation - no child relationships
        return []

    def get_dependencies(self, artifact_id: UUID) -> list[CodeArtifact]:
        """Get dependencies of the specified artifact."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to get dependencies",
                entity_type="CodeArtifact",
                operation="get_dependencies",
                entity_id=str(artifact_id),
            )

        # Mock implementation - no dependencies
        return []

    def get_dependents(self, artifact_id: UUID) -> list[CodeArtifact]:
        """Get artifacts that depend on the specified artifact."""
        if self.error_mode:
            raise RepositoryError(
                "Failed to get dependents",
                entity_type="CodeArtifact",
                operation="get_dependents",
                entity_id=str(artifact_id),
            )

        # Mock implementation - no dependents
        return []


@pytest.mark.unit
class TestCodeArtifactRepository:
    """Test cases for the CodeArtifactRepository interface contract."""

    def setup_method(self):
        """Set up the test repository."""
        self.repository = MockCodeArtifactRepository()

        # Create sample artifacts for testing
        self.artifact1 = CodeArtifact(
            id=uuid4(),
            path=Path("/path/to/file1.py"),
            name="file1.py",
            artifact_type="python_module",
            content="def hello_world():\n    print('Hello, world!')",
            metadata={"language": "python", "loc": 2},
        )

        self.artifact2 = CodeArtifact(
            id=uuid4(),
            path=Path("/path/to/file2.py"),
            name="file2.py",
            artifact_type="python_module",
            content="def goodbye_world():\n    print('Goodbye, world!')",
            metadata={"language": "python", "loc": 2},
        )

    def test_save_and_retrieve(self):
        """Test saving and retrieving an artifact."""
        # Act - Save
        saved_artifact = self.repository.save(self.artifact1)

        # Assert - Save
        assert saved_artifact == self.artifact1

        # Act - Retrieve
        retrieved_artifact = self.repository.get_by_id(self.artifact1.id)

        # Assert - Retrieve
        assert retrieved_artifact is not None
        assert retrieved_artifact.id == self.artifact1.id
        assert retrieved_artifact.name == self.artifact1.name
        assert retrieved_artifact.path == self.artifact1.path
        assert retrieved_artifact.artifact_type == self.artifact1.artifact_type
        assert retrieved_artifact.content == self.artifact1.content
        assert retrieved_artifact.metadata == self.artifact1.metadata

    def test_get_by_path(self):
        """Test retrieving an artifact by path."""
        # Arrange
        self.repository.save(self.artifact1)

        # Act
        retrieved_artifact = self.repository.get_by_path(self.artifact1.path)

        # Assert
        assert retrieved_artifact is not None
        assert retrieved_artifact.id == self.artifact1.id

    def test_get_by_name(self):
        """Test retrieving artifacts by name."""
        # Arrange
        self.repository.save(self.artifact1)

        # Create another artifact with the same name
        same_name_artifact = CodeArtifact(
            id=uuid4(), path=Path("/path/to/another/file1.py"), name="file1.py"
        )
        self.repository.save(same_name_artifact)

        # Act
        artifacts = self.repository.get_by_name("file1.py")

        # Assert
        assert len(artifacts) == 2
        assert any(a.id == self.artifact1.id for a in artifacts)
        assert any(a.id == same_name_artifact.id for a in artifacts)

    def test_find_all(self):
        """Test retrieving all artifacts."""
        # Arrange
        self.repository.save(self.artifact1)
        self.repository.save(self.artifact2)

        # Act
        artifacts = self.repository.find_all()

        # Assert
        assert len(artifacts) == 2
        assert any(a.id == self.artifact1.id for a in artifacts)
        assert any(a.id == self.artifact2.id for a in artifacts)

    def test_find_by_criteria(self):
        """Test finding artifacts by criteria."""
        # Arrange
        self.repository.save(self.artifact1)
        self.repository.save(self.artifact2)

        # Act - Find by artifact_type
        artifacts = self.repository.find_by_criteria({"artifact_type": "python_module"})

        # Assert
        assert len(artifacts) == 2

        # Act - Find by name
        artifacts = self.repository.find_by_criteria({"name": "file1.py"})

        # Assert
        assert len(artifacts) == 1
        assert artifacts[0].id == self.artifact1.id

    def test_delete(self):
        """Test deleting an artifact."""
        # Arrange
        self.repository.save(self.artifact1)

        # Act
        result = self.repository.delete(self.artifact1.id)

        # Assert
        assert result is True
        assert self.repository.get_by_id(self.artifact1.id) is None

    def test_delete_nonexistent(self):
        """Test deleting a nonexistent artifact."""
        # Act
        result = self.repository.delete(uuid4())

        # Assert
        assert result is False

    def test_error_handling(self):
        """Test error handling for repository operations."""
        # Arrange
        self.repository.set_error_mode(True)

        # Act/Assert - Save
        with pytest.raises(RepositoryError) as exc_info:
            self.repository.save(self.artifact1)
        assert "Failed to save artifact" in str(exc_info.value)

        # Act/Assert - Get by ID
        with pytest.raises(RepositoryError) as exc_info:
            self.repository.get_by_id(self.artifact1.id)
        assert "Failed to get artifact by ID" in str(exc_info.value)

        # Act/Assert - Find all
        with pytest.raises(RepositoryError) as exc_info:
            self.repository.find_all()
        assert "Failed to find all artifacts" in str(exc_info.value)

        # Act/Assert - Delete
        with pytest.raises(RepositoryError) as exc_info:
            self.repository.delete(self.artifact1.id)
        assert "Failed to delete artifact" in str(exc_info.value)
