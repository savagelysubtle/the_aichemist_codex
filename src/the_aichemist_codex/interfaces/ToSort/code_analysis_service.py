"""
Code Analysis Service Implementation

!!! THIS FILE SHOULD BE MOVED TO THE APPLICATION LAYER (@ToMove) !!!
It currently violates Clean Architecture principles by depending on domain entities
and orchestrating application logic within the infrastructure layer.
The technical analysis functions have been moved to technical_analyzer.py.
This service needs refactoring in the application layer to use the repository
and the infrastructure's technical analysis implementation (via an interface).

Location: src/the_aichemist_codex/infrastructure/analysis/code_analysis_service.py

Implements the CodeAnalysisServiceInterface for analyzing code artifacts.

Dependencies:
- domain.entities.code_artifact
- domain.services.interfaces.code_analysis_service
- domain.repositories.code_artifact_repository
- infrastructure.analysis.technical_analyzer
"""

import ast
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.exceptions.repository_exception import RepositoryError
from the_aichemist_codex.domain.repositories.code_artifact_repository import (
    CodeArtifactRepository,
)
from the_aichemist_codex.infrastructure.analysis.technical_analyzer import (
    _get_python_structure,
    assess_complexity,
    calculate_basic_complexity,
    calculate_python_complexity,
    calculate_similarity,
    extract_comments,
    process_file,
)
from the_aichemist_codex.infrastructure.utils.io.async_io import AsyncFileIO

logger = logging.getLogger(__name__)


class CodeAnalysisService:
    """Infrastructure implementation of code analysis service.

    NOTE: This class contains application logic and should be moved.
    """

    def __init__(self, repository: CodeArtifactRepository) -> None:
        """
        Initialize the code analysis service.

        Args:
            repository: The repository to use for storing and retrieving artifacts
        """
        self.repository = repository

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

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact from the repository
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Analyze the artifact based on its content using the helper method
        return await self._analyze_content(artifact, depth)

    async def analyze_file(self, file_path: Path, depth: int = 1) -> dict[str, Any]:
        """
        Analyze a file and create a CodeArtifact if it doesn't exist.

        Args:
            file_path: The path to the file to analyze
            depth: The depth of analysis (1: basic, 2: standard, 3: deep)

        Returns:
            Analysis results as a dictionary

        Raises:
            FileNotFoundError: If the file does not exist
            RepositoryError: If there's an issue with the repository
            IOError: If there's an issue reading the file
        """
        # Check if file exists
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        # Check if an artifact already exists for this path
        existing_artifact = await self.repository.get_by_path(file_path)

        if existing_artifact:
            # Update the existing artifact with the current content
            content = await AsyncFileIO.read_text(file_path)
            if content.startswith("# Error") or content.startswith("# Encoding"):
                logger.error(f"Failed to read file {file_path}: {content}")
                raise OSError(f"Failed to read file {file_path}: {content}")

            if existing_artifact.content != content:
                existing_artifact.parse_content(content)
                existing_artifact = await self.repository.save(existing_artifact)

            return await self._analyze_content(existing_artifact, depth)

        # Create a new artifact
        content = await AsyncFileIO.read_text(file_path)
        if content.startswith("# Error") or content.startswith("# Encoding"):
            logger.error(f"Failed to read file {file_path}: {content}")
            raise OSError(f"Failed to read file {file_path}: {content}")

        artifact = CodeArtifact(
            path=file_path,
            name=file_path.name,
            artifact_type="file",
            content=content,
        )

        # Save the artifact
        saved_artifact = await self.repository.save(artifact)

        # Analyze the content
        return await self._analyze_content(saved_artifact, depth)

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

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get the direct dependencies
        dependencies = await self.repository.get_dependencies(artifact_id)

        # If not recursive, return the direct dependencies
        if not recursive:
            return dependencies

        # If recursive, find dependencies of dependencies
        all_dependencies = set(dependencies)
        processed_ids = {artifact_id}  # Avoid infinite loops in cyclic dependencies
        queue = list(dependencies)

        while queue:
            current_dep = queue.pop(0)
            if current_dep.id in processed_ids:
                continue
            processed_ids.add(current_dep.id)
            all_dependencies.add(current_dep)

            try:
                # Find dependencies of the current dependency
                dependency_deps = await self.repository.get_dependencies(current_dep.id)
                for dep_dep in dependency_deps:
                    if dep_dep.id not in processed_ids:
                        queue.append(dep_dep)
            except RepositoryError as e:
                # Skip dependencies that can't be found
                logger.warning(f"Could not find dependencies for {current_dep.id}: {e}")
                continue

        return list(all_dependencies)

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

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get the direct references (dependents)
        references = await self.repository.get_dependents(artifact_id)

        # If not recursive, return the direct references
        if not recursive:
            return references

        # If recursive, find references to references
        all_references = set(references)
        processed_ids = {artifact_id}  # Avoid infinite loops
        queue = list(references)

        while queue:
            current_ref = queue.pop(0)
            if current_ref.id in processed_ids:
                continue
            processed_ids.add(current_ref.id)
            all_references.add(current_ref)

            try:
                # Find references to the current reference
                reference_refs = await self.repository.get_dependents(current_ref.id)
                for ref_ref in reference_refs:
                    if ref_ref.id not in processed_ids:
                        queue.append(ref_ref)
            except RepositoryError as e:
                # Skip references that can't be found
                logger.warning(f"Could not find references for {current_ref.id}: {e}")
                continue

        return list(all_references)

    async def calculate_complexity(self, artifact_id: UUID) -> float:
        """
        Calculate the complexity of a code artifact.

        Args:
            artifact_id: The ID of the artifact to calculate complexity for

        Returns:
            Complexity score

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Calculate complexity based on content using functions from technical_analyzer
        if not artifact.content:
            return 0.0

        complexity = 0.0
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""

        if file_ext in [".py", ".pyw"]:
            try:
                tree = ast.parse(artifact.content)
                complexity = calculate_python_complexity(tree)
            except SyntaxError:
                logger.warning(
                    f"Syntax error in artifact {artifact.id}, calculating basic complexity."
                )
                complexity = calculate_basic_complexity(artifact.content)
            except Exception as e:
                logger.error(
                    f"Error parsing Python artifact {artifact.id} for complexity: {e}"
                )
                complexity = calculate_basic_complexity(artifact.content)
        else:
            complexity = calculate_basic_complexity(artifact.content)

        return complexity

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

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get all artifacts (consider optimization for large repositories)
        all_artifacts = await self.repository.find_all()

        # Calculate similarity scores
        similar_artifacts = []
        for other_artifact in all_artifacts:
            # Skip the same artifact
            if other_artifact.id == artifact.id:
                continue

            # Calculate similarity using function from technical_analyzer
            similarity = calculate_similarity(
                artifact.content,
                other_artifact.content,
                artifact.path,
                other_artifact.path,
            )

            if similarity >= min_similarity:
                similar_artifacts.append((other_artifact, similarity))

        # Sort by similarity (descending)
        similar_artifacts.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        return similar_artifacts[:limit]

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

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Extract knowledge items (simplified implementation)
        if not artifact.content:
            return []

        knowledge_items = []
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""

        if file_ext in [".py", ".pyw"]:
            try:
                tree = ast.parse(artifact.content)

                # Extract module docstring
                module_doc = ast.get_docstring(tree)
                if module_doc:
                    knowledge_items.append(
                        {"type": "module_doc", "content": module_doc, "importance": 0.9}
                    )

                # Use _get_python_structure for functions and classes
                structure = _get_python_structure(artifact.content)
                for func in structure.get("functions", []):
                    knowledge_items.append(
                        {
                            "type": "function",
                            "name": func["name"],
                            "docstring": func.get("docstring", "No docstring"),
                            "args": func.get("args", []),
                            "lineno": func["line"],
                            "importance": 0.8,
                        }
                    )
                for cls in structure.get("classes", []):
                    knowledge_items.append(
                        {
                            "type": "class",
                            "name": cls["name"],
                            "docstring": cls.get("docstring", "No docstring"),
                            "lineno": cls["line"],
                            "importance": 0.85,
                        }
                    )
                # Extract comments as fallback or supplement
                knowledge_items.extend(extract_comments(artifact.content))

            except SyntaxError:
                logger.warning(
                    f"Syntax error in artifact {artifact.id}, extracting only comments."
                )
                knowledge_items.extend(extract_comments(artifact.content))
            except Exception as e:
                logger.error(
                    f"Error extracting knowledge from Python artifact {artifact.id}: {e}"
                )
                knowledge_items.extend(extract_comments(artifact.content))
        else:
            # For other files, extract comments and patterns
            knowledge_items.extend(extract_comments(artifact.content))

        # Sort by importance and limit
        knowledge_items.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return knowledge_items[:max_items]

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

        Raises:
            FileNotFoundError: If the directory does not exist
            IOError: If file reading fails during artifact creation
        """
        # Check if directory exists
        directory = Path(directory).resolve()
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Directory {directory} does not exist")

        # Find all matching files
        matching_files = list(directory.glob(f"**/{file_pattern}"))

        if not matching_files:
            logger.warning(
                f"No files matching pattern {file_pattern} found in {directory}"
            )
            return {
                "status": "empty",
                "message": f"No files matching pattern {file_pattern} found in {directory}",
                "directory": str(directory),
                "pattern": file_pattern,
            }

        # Process each file to create/update artifacts
        results = {}
        artifacts = []

        for file_path in matching_files:
            try:
                # Check if an artifact already exists for this path
                existing_artifact = await self.repository.get_by_path(file_path)

                if existing_artifact:
                    # Optionally check/update content if needed, or just use existing
                    # For simplicity, assume we use existing artifact if found
                    artifacts.append(existing_artifact)
                else:
                    # Read content to create artifact
                    content = await AsyncFileIO.read_text(file_path)
                    if content.startswith("# Error") or content.startswith(
                        "# Encoding"
                    ):
                        logger.error(
                            f"Failed to read file {file_path} for analysis: {content}"
                        )
                        results[str(file_path)] = {
                            "status": "error",
                            "message": f"Read error: {content}",
                        }
                        continue  # Skip this file

                    # Create and save the artifact
                    artifact = CodeArtifact(
                        path=file_path,
                        name=file_path.name,
                        artifact_type="file",
                        content=content,
                    )
                    saved_artifact = await self.repository.save(artifact)
                    artifacts.append(saved_artifact)
            except OSError as e:
                logger.error(f"IOError processing file {file_path}: {e}")
                results[str(file_path)] = {"status": "error", "message": str(e)}
            except RepositoryError as e:
                logger.error(f"RepositoryError processing file {file_path}: {e}")
                results[str(file_path)] = {"status": "error", "message": str(e)}
            except Exception as e:
                # Log other errors but continue processing other files
                logger.exception(f"Unexpected error processing file {file_path}: {e}")
                results[str(file_path)] = {"status": "error", "message": str(e)}

        # Perform aggregate analysis on the collected artifacts
        analysis_summary: dict[str, Any] = {
            "artifacts": [
                {
                    "id": str(artifact.id),
                    "name": artifact.name,
                    "path": str(artifact.path),
                    "type": artifact.artifact_type,
                }
                for artifact in artifacts
            ],
            "summary": {  # Basic summary
                "file_count": len(artifacts),
                "total_lines": sum(
                    len(artifact.content.split("\n")) if artifact.content else 0
                    for artifact in artifacts
                ),
                "directory": str(directory),
                "pattern": file_pattern,
            },
            "errors": {
                fp: data for fp, data in results.items() if data["status"] == "error"
            },
        }

        # If depth > 1, add more detailed analysis
        if depth > 1 and artifacts:
            complexities = []
            for artifact in artifacts:
                try:
                    # Use the instance method which now calls the technical function
                    complexity = await self.calculate_complexity(artifact.id)
                    complexities.append((artifact, complexity))
                except Exception as e:
                    logger.warning(
                        f"Could not calculate complexity for {artifact.id}: {e}"
                    )
                    continue

            if complexities:
                complexities.sort(key=lambda x: x[1], reverse=True)
                avg_complexity = sum(c for _, c in complexities) / len(complexities)
                analysis_summary["complexity"] = {
                    "average": avg_complexity,
                    "max": complexities[0][1],
                    "assessment": assess_complexity(avg_complexity),
                    "most_complex": [
                        {
                            "id": str(artifact.id),
                            "name": artifact.name,
                            "path": str(artifact.path),
                            "complexity": complexity,
                        }
                        for artifact, complexity in complexities[:5]
                    ],
                }
            else:
                analysis_summary["complexity"] = {
                    "average": 0,
                    "max": 0,
                    "assessment": "N/A",
                    "most_complex": [],
                }

        # If depth > 2, add knowledge extraction
        if depth > 2 and artifacts:
            knowledge_summary = []
            # Select artifacts to analyze (prioritize by complexity or size)
            artifacts_to_analyze = (
                [a for a, _ in complexities[:10]]
                if depth > 1 and complexities  # Reuse complexities if calculated
                else artifacts[:10]
            )

            for artifact in artifacts_to_analyze:
                try:
                    # Use the instance method which now calls the technical function
                    knowledge = await self.extract_knowledge(artifact.id, 3)
                    if knowledge:
                        knowledge_summary.append(
                            {
                                "artifact": {
                                    "id": str(artifact.id),
                                    "name": artifact.name,
                                    "path": str(artifact.path),
                                },
                                "knowledge_items": knowledge,
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not extract knowledge from {artifact.id}: {e}"
                    )
                    continue

            analysis_summary["knowledge"] = knowledge_summary

        return analysis_summary

    async def get_summary(self, artifact_id: UUID) -> str:
        """
        Get a summary of a code artifact.

        Args:
            artifact_id: The ID of the artifact to summarize

        Returns:
            Summary text

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Use the process_file function from technical_analyzer
        # Note: process_file requires a Path object.
        try:
            # Check if path exists before calling process_file
            if not artifact.path.exists():
                logger.warning(
                    f"File path for artifact {artifact_id} does not exist: {artifact.path}"
                )
                return f"Summary unavailable: File not found at {artifact.path}"

            _, file_data = await process_file(artifact.path)
            # Check if process_file returned an error
            if file_data.get("error"):
                return f"Unable to generate summary: {file_data['summary']}"
            return file_data.get("summary", "Summary generation failed.")
        except Exception as e:
            logger.error(f"Error generating summary for {artifact_id}: {e}")
            return f"Unable to generate summary: {e!s}"

    async def get_structure(self, artifact_id: UUID) -> dict[str, list[dict[str, Any]]]:
        """
        Get the structure of a code artifact.

        Args:
            artifact_id: The ID of the artifact to get structure for

        Returns:
            Structure as a dictionary {classes: [...], functions: [...], variables: [...]} or empty lists.

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = await self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Initialize structure with default empty lists
        structure: dict[str, list[dict[str, Any]]] = {
            "classes": [],
            "functions": [],
            "variables": [],
        }

        # Parse the content if available
        if not artifact.content:
            return structure

        # Use the appropriate structure extraction function based on file type
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""

        if file_ext in [".py", ".pyw"]:
            # Use the technical analyzer function for Python structure
            structure = _get_python_structure(artifact.content)
        else:
            # For other file types, maybe return empty or implement basic structure extraction
            logger.info(
                f"Structure extraction not implemented for file type: {file_ext}"
            )
            pass  # Return default empty structure

        return structure

    async def _analyze_content(
        self, artifact: CodeArtifact, depth: int = 1
    ) -> dict[str, Any]:
        """
        Helper method to analyze the content of an artifact.

        Args:
            artifact: The artifact to analyze
            depth: The depth of analysis

        Returns:
            Analysis results as a dictionary
        """
        results: dict[str, Any] = {
            "artifact": {
                "id": str(artifact.id),
                "name": artifact.name,
                "path": str(artifact.path),
                "type": artifact.artifact_type,
            }
        }

        # Skip analysis if no content
        if not artifact.content:
            results["status"] = "empty"
            return results

        # Basic analysis (always performed)
        lines = artifact.content.split("\n")
        results["basic"] = {
            "line_count": len(lines),
            "size_bytes": len(artifact.content.encode("utf-8")),  # Use bytes for size
            "empty_lines": sum(1 for line in lines if not line.strip()),
            "file_type": artifact.path.suffix.lower()
            if artifact.path.suffix
            else "unknown",
        }

        # Standard analysis (depth >= 2)
        if depth >= 2:
            # Calculate complexity using the instance method
            complexity_score = await self.calculate_complexity(artifact.id)
            results["complexity"] = {
                "score": complexity_score,
                "assessment": assess_complexity(
                    complexity_score
                ),  # Use imported function
            }

            # Get structure using the instance method
            structure = await self.get_structure(artifact.id)
            results["structure"] = structure

        # Deep analysis (depth >= 3)
        if depth >= 3:
            # Extract knowledge using the instance method
            knowledge = await self.extract_knowledge(artifact.id)
            results["knowledge"] = knowledge

            # Get dependencies (if any)
            try:
                dependencies = await self.find_dependencies(artifact.id)
                results["dependencies"] = [
                    {"id": str(dep.id), "name": dep.name, "path": str(dep.path)}
                    for dep in dependencies
                ]
            except Exception as e:
                logger.warning(f"Could not find dependencies for {artifact.id}: {e}")
                results["dependencies"] = []

        results["status"] = "analyzed"
        return results
