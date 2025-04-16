"""
Analysis Result Data Transfer Object

This module contains the DTO for transferring code analysis results between layers.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact


@dataclass
class AnalysisResultDTO:
    """Data Transfer Object for code analysis results."""

    artifact_id: UUID
    complexity: float | None = None
    summary: str | None = None
    knowledge_items: list[dict[str, Any]] | None = None
    structure: dict[str, list[dict[str, Any]]] | None = None
    dependencies: list[UUID] | None = None
    references: list[UUID] | None = None
    similar_artifacts: list[tuple[UUID, float]] | None = None
    analysis_depth: int = 1
    analysis_results: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_artifact_and_analysis(
        cls: type["AnalysisResultDTO"],
        artifact: CodeArtifact,
        analysis_results: dict[str, Any],
    ) -> "AnalysisResultDTO":
        """Create DTO from a CodeArtifact and analysis results."""
        return cls(
            artifact_id=artifact.id,
            analysis_results=analysis_results,
            complexity=analysis_results.get("complexity"),
            summary=analysis_results.get("summary"),
            knowledge_items=analysis_results.get("knowledge_items"),
            structure=analysis_results.get("structure"),
            dependencies=[d.id for d in analysis_results.get("dependencies", [])],
            references=[r.id for r in analysis_results.get("references", [])],
            similar_artifacts=[
                (a.id, s) for a, s in analysis_results.get("similar_artifacts", [])
            ],
            analysis_depth=analysis_results.get("depth", 1),
        )
