"""Repository interface for CodeArtifact entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import UUID

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact


class CodeArtifactRepository(ABC):
    """Repository interface for CodeArtifact entities.

    This abstract base class defines the contract for repositories that handle
    the persistence and retrieval of CodeArtifact entities. Implementations of
    this interface can store artifacts in various backends such as file systems,
    databases, or remote services.
    """

    @abstractmethod
    async def save(
        self: CodeArtifactRepository, artifact: CodeArtifact
    ) -> CodeArtifact:
        """Save a code artifact to the repository.

        Args:
            artifact: The code artifact to save

        Returns:
            The saved code artifact with any updates (e.g., updated ID)

        Raises:
            RepositoryError: If the artifact cannot be saved
        """
        pass

    @abstractmethod
    async def get_by_id(
        self: CodeArtifactRepository, artifact_id: UUID
    ) -> CodeArtifact | None:
        """Get a code artifact by its ID.

        Args:
            artifact_id: The ID of the artifact to retrieve

        Returns:
            The code artifact if found, None otherwise

        Raises:
            RepositoryError: If an error occurs while retrieving the artifact
        """
        pass

    @abstractmethod
    async def get_by_path(
        self: CodeArtifactRepository, path: Path
    ) -> CodeArtifact | None:
        """Get a code artifact by its path.

        Args:
            path: The path of the artifact to retrieve

        Returns:
            The code artifact if found, None otherwise

        Raises:
            RepositoryError: If an error occurs while retrieving the artifact
        """
        pass

    @abstractmethod
    async def get_by_name(
        self: CodeArtifactRepository, name: str
    ) -> list[CodeArtifact]:
        """Get code artifacts by name.

        Args:
            name: The name of the artifacts to retrieve

        Returns:
            A list of code artifacts with the given name

        Raises:
            RepositoryError: If an error occurs while retrieving the artifacts
        """
        pass

    @abstractmethod
    async def find_all(self: CodeArtifactRepository) -> list[CodeArtifact]:
        """Get all code artifacts.

        Returns:
            A list of all code artifacts in the repository

        Raises:
            RepositoryError: If an error occurs while retrieving the artifacts
        """
        pass

    @abstractmethod
    async def find_by_criteria(
        self: CodeArtifactRepository, criteria: dict[str, Any]
    ) -> list[CodeArtifact]:
        """Find code artifacts matching criteria.

        Args:
            criteria: A dictionary of attribute-value pairs to match

        Returns:
            A list of code artifacts matching the criteria

        Raises:
            RepositoryError: If an error occurs while retrieving the artifacts
        """
        pass

    @abstractmethod
    async def delete(self: CodeArtifactRepository, artifact_id: UUID) -> bool:
        """Delete a code artifact by its ID.

        Args:
            artifact_id: The ID of the artifact to delete

        Returns:
            True if the artifact was deleted, False otherwise

        Raises:
            RepositoryError: If an error occurs while deleting the artifact
        """
        pass

    @abstractmethod
    async def get_children(
        self: CodeArtifactRepository, parent_id: UUID
    ) -> list[CodeArtifact]:
        """Get child artifacts of a parent artifact.

        Args:
            parent_id: The ID of the parent artifact

        Returns:
            A list of child artifacts

        Raises:
            RepositoryError: If an error occurs while retrieving the children
        """
        pass

    @abstractmethod
    async def get_dependencies(
        self: CodeArtifactRepository, artifact_id: UUID
    ) -> list[CodeArtifact]:
        """Get dependencies of an artifact.

        Args:
            artifact_id: The ID of the artifact

        Returns:
            A list of artifacts that the given artifact depends on

        Raises:
            RepositoryError: If an error occurs while retrieving the dependencies
        """
        pass

    @abstractmethod
    async def get_dependents(
        self: CodeArtifactRepository, artifact_id: UUID
    ) -> list[CodeArtifact]:
        """Get artifacts that depend on an artifact.

        Args:
            artifact_id: The ID of the artifact

        Returns:
            A list of artifacts that depend on the given artifact

        Raises:
            RepositoryError: If an error occurs while retrieving the dependents
        """
        pass
