"""
Application Code Analysis Service

This module provides the application service for code analysis operations.
It orchestrates the use of domain services and repositories to analyze code artifacts.
"""

from pathlib import Path
from typing import Any
from uuid import UUID

from the_aichemist_codex.application.dto.analysis_result_dto import AnalysisResultDTO
from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.repositories.code_artifact_repository import (
    CodeArtifactRepository,
)
from the_aichemist_codex.domain.services.interfaces.code_analysis_service import (
    CodeAnalysisServiceInterface,
)


class ApplicationCodeAnalysisService:
    """Application service for code analysis operations."""

    def __init__(
        self: "ApplicationCodeAnalysisService",
        repository: CodeArtifactRepository,
        technical_analyzer: CodeAnalysisServiceInterface,
    ) -> None:
        """Initialize with the required dependencies."""
        self.repository = repository
        self.technical_analyzer = technical_analyzer

    async def get_artifact_analysis(
        self: "ApplicationCodeAnalysisService",
        artifact_id: UUID,
        include_structure: bool = False,
        max_knowledge_items: int = 10,
    ) -> AnalysisResultDTO:
        """Get comprehensive analysis of an artifact.

        Args:
            artifact_id: The unique ID of the artifact to analyze
            include_structure: Whether to include structure analysis (more expensive)
            max_knowledge_items: Maximum number of knowledge items to extract

        Returns:
            A data transfer object with the analysis results

        Raises:
            ValueError: If the artifact doesn't exist
        """
        # Verify artifact exists
        artifact = await self.repository.get_by_id(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact with id {artifact_id} not found")

        # Collect analysis tasks
        complexity = await self.technical_analyzer.calculate_complexity(artifact_id)
        summary = await self.technical_analyzer.get_summary(artifact_id)
        knowledge_items = await self.technical_analyzer.extract_knowledge(
            artifact_id, max_items=max_knowledge_items
        )

        # Structure analysis is optional (more expensive)
        structure = None
        if include_structure:
            structure = await self.technical_analyzer.get_structure(artifact_id)

        # Create and return the DTO
        return AnalysisResultDTO(
            artifact_id=artifact_id,
            complexity=complexity,
            summary=summary,
            knowledge_items=knowledge_items,
            structure=structure,
        )

    async def analyze_file(
        self: "ApplicationCodeAnalysisService", file_path: str, depth: int = 1
    ) -> AnalysisResultDTO:
        """Analyze a file and create an artifact if it doesn't exist.

        Args:
            file_path: Path to the file to analyze
            depth: Analysis depth (1: basic, 2: standard, 3: deep)

        Returns:
            Analysis results as a DTO

        Raises:
            ValueError: If the file doesn't exist
        """
        # Convert string path to Path object
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Analyze the file
        analysis = await self.technical_analyzer.analyze_file(path, depth)

        # Check if artifact exists
        artifact = await self.repository.get_by_path(path)
        if not artifact:
            # Read file content
            content = path.read_text()
            # Create new artifact
            new_artifact = CodeArtifact(
                path=path,
                name=path.name,  # Use filename as name
                content=content,
                artifact_type="file",
                metadata={"depth": depth},
            )
            artifact = await self.repository.save(new_artifact)

        # Return results as DTO
        return AnalysisResultDTO(
            artifact_id=artifact.id,
            complexity=analysis.get("complexity"),
            summary=analysis.get("summary", ""),
            knowledge_items=analysis.get("knowledge_items", []),
            structure=analysis.get("structure") if depth > 1 else None,
        )

    async def find_similar_artifacts(
        self: "ApplicationCodeAnalysisService",
        artifact_id: UUID,
        min_similarity: float = 0.5,
        limit: int = 10,
    ) -> list[AnalysisResultDTO]:
        """Find artifacts similar to the given one.

        Args:
            artifact_id: The ID of the artifact to find similar ones for
            min_similarity: Minimum similarity score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of similar artifacts as DTOs
        """
        similar = await self.technical_analyzer.find_similar_artifacts(
            artifact_id, min_similarity, limit
        )

        return [
            AnalysisResultDTO(
                artifact_id=artifact.id,
                complexity=await self.technical_analyzer.calculate_complexity(
                    artifact.id
                ),
                summary=await self.technical_analyzer.get_summary(artifact.id),
            )
            for artifact, _ in similar
        ]

    async def analyze_codebase(
        self: "ApplicationCodeAnalysisService",
        directory: str,
        depth: int = 1,
        file_pattern: str = "*.py",
    ) -> dict[str, Any]:
        """Analyze an entire codebase.

        Args:
            directory: Path to the directory to analyze
            depth: Analysis depth (1: basic, 2: standard, 3: deep)
            file_pattern: Glob pattern to match files

        Returns:
            Analysis results for the entire codebase

        Raises:
            ValueError: If the directory doesn't exist
        """
        path = Path(directory)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        return await self.technical_analyzer.analyze_codebase(path, depth, file_pattern)
