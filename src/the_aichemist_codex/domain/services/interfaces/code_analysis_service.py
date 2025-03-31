"""
Code Analysis Service Interface

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/services/interfaces/code_analysis_service.py

Defines the interface for domain services that handle code analysis operations.
This is a protocol that must be implemented by concrete service classes.

Dependencies:
- domain.entities.code_artifact
"""

from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact


class CodeAnalysisServiceInterface(Protocol):
    """Interface for domain services dealing with code analysis operations."""

    async def analyze_artifact(
        self, artifact_id: UUID, depth: int = 1
    ) -> dict[str, Any]:
        """
        Analyze a single code artifact.

        Args:
            artifact_id: The ID of the artifact to analyze
            depth: The depth of analysis (1: basic, 2: standard, 3: deep)

        Returns:
            Analysis results as a dictionary
        """
        ...

    async def analyze_file(self, file_path: Path, depth: int = 1) -> dict[str, Any]:
        """
        Analyze a file and create a CodeArtifact if it doesn't exist.

        Args:
            file_path: The path to the file to analyze
            depth: The depth of analysis (1: basic, 2: standard, 3: deep)

        Returns:
            Analysis results as a dictionary
        """
        ...

    async def find_dependencies(
        self, artifact_id: UUID, recursive: bool = False
    ) -> list[CodeArtifact]:
        """
        Find dependencies of a code artifact.

        Args:
            artifact_id: The ID of the artifact to find dependencies for
            recursive: Whether to recursively find dependencies of dependencies

        Returns:
            List of dependency artifacts
        """
        ...

    async def find_references(
        self, artifact_id: UUID, recursive: bool = False
    ) -> list[CodeArtifact]:
        """
        Find references to a code artifact.

        Args:
            artifact_id: The ID of the artifact to find references for
            recursive: Whether to recursively find references to references

        Returns:
            List of referencing artifacts
        """
        ...

    async def calculate_complexity(self, artifact_id: UUID) -> float:
        """
        Calculate the complexity of a code artifact.

        Args:
            artifact_id: The ID of the artifact to calculate complexity for

        Returns:
            Complexity score
        """
        ...

    async def find_similar_artifacts(
        self, artifact_id: UUID, min_similarity: float = 0.5, limit: int = 10
    ) -> list[tuple[CodeArtifact, float]]:
        """
        Find artifacts similar to the given artifact.

        Args:
            artifact_id: The ID of the artifact to find similar artifacts for
            min_similarity: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of (artifact, similarity_score) tuples
        """
        ...

    async def extract_knowledge(
        self, artifact_id: UUID, max_items: int = 10
    ) -> list[dict[str, Any]]:
        """
        Extract knowledge items from a code artifact.

        Args:
            artifact_id: The ID of the artifact to extract knowledge from
            max_items: Maximum number of knowledge items to extract

        Returns:
            List of knowledge items as dictionaries
        """
        ...

    async def analyze_codebase(
        self, directory: Path, depth: int = 1, file_pattern: str = "*.py"
    ) -> dict[str, Any]:
        """
        Analyze a codebase directory.

        Args:
            directory: The directory to analyze
            depth: The depth of analysis (1: basic, 2: standard, 3: deep)
            file_pattern: Glob pattern to match files

        Returns:
            Analysis results as a dictionary
        """
        ...

    async def get_summary(self, artifact_id: UUID) -> str:
        """
        Get a summary of a code artifact.

        Args:
            artifact_id: The ID of the artifact to summarize

        Returns:
            Summary text
        """
        ...

    async def get_structure(self, artifact_id: UUID) -> dict[str, list[dict[str, Any]]]:
        """
        Get the structure of a code artifact.

        Args:
            artifact_id: The ID of the artifact to get structure for

        Returns:
            Structure as a dictionary
        """
        ...
