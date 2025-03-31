"""
Code Analysis Service Implementation

This module is part of the infrastructure layer of the AIchemist Codex.
Location: src/the_aichemist_codex/infrastructure/analysis/code_analysis_service.py

Implements the CodeAnalysisServiceInterface for analyzing code artifacts.

Dependencies:
- domain.entities.code_artifact
- domain.services.interfaces.code_analysis_service
- domain.repositories.code_artifact_repository
- infrastructure.analysis.code
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.exceptions.repository_exception import RepositoryError
from the_aichemist_codex.domain.repositories.code_artifact_repository import (
    CodeArtifactRepository,
)
from the_aichemist_codex.infrastructure.analysis.code import process_file

logger = logging.getLogger(__name__)


class CodeAnalysisService:
    """Infrastructure implementation of code analysis service."""

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
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Analyze the artifact based on its content
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
        """
        # Check if file exists
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")

        # Check if an artifact already exists for this path
        existing_artifact = self.repository.get_by_path(file_path)

        if existing_artifact:
            # Update the existing artifact with the current content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if existing_artifact.content != content:
                existing_artifact.parse_content(content)
                existing_artifact = self.repository.save(existing_artifact)

            return await self._analyze_content(existing_artifact, depth)

        # Create a new artifact
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        artifact = CodeArtifact(
            path=file_path,
            name=file_path.name,
            artifact_type="file",
            content=content,
        )

        # Save the artifact
        saved_artifact = self.repository.save(artifact)

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
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get the direct dependencies
        dependencies = self.repository.get_dependencies(artifact_id)

        # If not recursive, return the direct dependencies
        if not recursive:
            return dependencies

        # If recursive, find dependencies of dependencies
        all_dependencies = set(dependencies)
        for dependency in dependencies:
            try:
                dependency_deps = await self.find_dependencies(dependency.id, True)
                all_dependencies.update(dependency_deps)
            except RepositoryError as e:
                # Skip dependencies that can't be found
                logger.warning(f"Could not find dependencies for {dependency.id}: {e}")
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
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get the direct references (dependents)
        references = self.repository.get_dependents(artifact_id)

        # If not recursive, return the direct references
        if not recursive:
            return references

        # If recursive, find references to references
        all_references = set(references)
        for reference in references:
            try:
                reference_refs = await self.find_references(reference.id, True)
                all_references.update(reference_refs)
            except RepositoryError as e:
                # Skip references that can't be found
                logger.warning(f"Could not find references for {reference.id}: {e}")
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
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Calculate complexity based on content
        if not artifact.content:
            return 0.0

        # Basic complexity calculation
        complexity = 0.0

        # Calculate based on file extension
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""

        if file_ext in [".py", ".pyw"]:
            # For Python files, use AST to calculate complexity
            try:
                tree = ast.parse(artifact.content)
                complexity = self._calculate_python_complexity(tree)
            except SyntaxError:
                # If there's a syntax error, use a simpler approach
                complexity = self._calculate_basic_complexity(artifact.content)
        else:
            # For other files, use a basic complexity calculation
            complexity = self._calculate_basic_complexity(artifact.content)

        return complexity

    def _calculate_python_complexity(self, tree: ast.AST) -> float:
        """
        Calculate complexity of Python code using AST.

        Args:
            tree: The AST of the Python code

        Returns:
            Complexity score
        """
        # Count functions and classes
        function_count = 0
        class_count = 0
        max_nesting = 0
        current_nesting = 0
        branch_count = 0

        # Count various syntax elements that contribute to complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                function_count += 1

            elif isinstance(node, ast.ClassDef):
                class_count += 1

            elif isinstance(node, ast.If | ast.For | ast.While | ast.With):
                branch_count += 1
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)

            elif isinstance(node, ast.Try):
                branch_count += (
                    len(node.handlers)
                    + (1 if node.orelse else 0)
                    + (1 if node.finalbody else 0)
                )
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)

        # Calculate complexity score
        complexity = (
            function_count * 0.5
            + class_count * 0.7
            + branch_count * 0.3
            + max_nesting * 1.0
        )

        return complexity

    def _calculate_basic_complexity(self, content: str) -> float:
        """
        Calculate basic complexity based on content.

        Args:
            content: The content to analyze

        Returns:
            Complexity score
        """
        # Count lines
        lines = content.split("\n")
        line_count = len(lines)

        # Count logical elements that might indicate complexity
        control_flow_count = len(
            re.findall(
                r"\b(if|else|for|while|switch|case|try|catch|finally)\b", content
            )
        )
        function_count = len(re.findall(r"\b(function|def|class|method)\b", content))

        # Calculate complexity score
        complexity = line_count * 0.01 + control_flow_count * 0.3 + function_count * 0.5

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
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get all artifacts
        all_artifacts = self.repository.find_all()

        # Calculate similarity scores
        similar_artifacts = []
        for other in all_artifacts:
            # Skip the same artifact
            if other.id == artifact.id:
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(artifact, other)

            if similarity >= min_similarity:
                similar_artifacts.append((other, similarity))

        # Sort by similarity (descending)
        similar_artifacts.sort(key=lambda x: x[1], reverse=True)

        # Limit results
        return similar_artifacts[:limit]

    def _calculate_similarity(
        self, artifact1: CodeArtifact, artifact2: CodeArtifact
    ) -> float:
        """
        Calculate similarity between two artifacts.

        Args:
            artifact1: The first artifact
            artifact2: The second artifact

        Returns:
            Similarity score (0.0-1.0)
        """
        # This is a simple implementation for demonstration
        # A real implementation would use more sophisticated algorithms

        if not artifact1.content or not artifact2.content:
            return 0.0

        # Check if they're the same file type
        path1 = artifact1.path
        path2 = artifact2.path

        file_type_match = 0.0
        if path1.suffix.lower() == path2.suffix.lower():
            file_type_match = 0.2

        # Check name similarity
        name_similarity = 0.0
        if artifact1.name == artifact2.name:
            name_similarity = 0.3

        # Check content similarity (very basic)
        content_similarity = 0.0
        lines1 = set(artifact1.content.split("\n"))
        lines2 = set(artifact2.content.split("\n"))

        # Jaccard similarity of lines
        if lines1 and lines2:
            intersection = len(lines1.intersection(lines2))
            union = len(lines1.union(lines2))
            if union > 0:
                content_similarity = intersection / union * 0.5

        return file_type_match + name_similarity + content_similarity

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
        artifact = self.repository.get_by_id(artifact_id)

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

        # Process based on file type
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""

        if file_ext in [".py", ".pyw"]:
            # For Python files, extract docstrings, functions, classes
            try:
                tree = ast.parse(artifact.content)

                # Extract module docstring
                module_doc = ast.get_docstring(tree)
                if module_doc:
                    knowledge_items.append(
                        {"type": "module_doc", "content": module_doc, "importance": 0.9}
                    )

                # Extract function and class definitions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        doc = ast.get_docstring(node)
                        knowledge_items.append(
                            {
                                "type": "function",
                                "name": node.name,
                                "docstring": doc or "No docstring",
                                "args": [arg.arg for arg in node.args.args],
                                "lineno": node.lineno,
                                "importance": 0.8,
                            }
                        )
                    elif isinstance(node, ast.ClassDef):
                        doc = ast.get_docstring(node)
                        knowledge_items.append(
                            {
                                "type": "class",
                                "name": node.name,
                                "docstring": doc or "No docstring",
                                "lineno": node.lineno,
                                "importance": 0.85,
                            }
                        )
            except SyntaxError:
                # If there's a syntax error, extract comments
                knowledge_items.extend(self._extract_comments(artifact.content))
        else:
            # For other files, extract comments and patterns
            knowledge_items.extend(self._extract_comments(artifact.content))

        # Sort by importance and limit
        knowledge_items.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return knowledge_items[:max_items]

    def _extract_comments(self, content: str) -> list[dict[str, Any]]:
        """
        Extract comments from code content.

        Args:
            content: The code content

        Returns:
            List of knowledge items from comments
        """
        knowledge_items = []

        # Extract comments (simplified)
        # This is a very basic implementation that would be enhanced in a real system
        comment_patterns = [
            (r"#\s*(.*?)$", "python"),  # Python
            (r"//\s*(.*?)$", "c-style"),  # C-style
            (r"/\*(.*?)\*/", "block"),  # Block comments
        ]

        for pattern, comment_type in comment_patterns:
            comments = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for i, comment in enumerate(comments):
                if len(comment.strip()) > 10:  # Ignore very short comments
                    knowledge_items.append(
                        {
                            "type": f"{comment_type}_comment",
                            "content": comment.strip(),
                            "importance": 0.5,
                            "index": i,
                        }
                    )

        return knowledge_items

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
        """
        # Check if directory exists
        directory = Path(directory).resolve()
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Directory {directory} does not exist")

        # Find all matching files
        matching_files = list(directory.glob(f"**/{file_pattern}"))

        if not matching_files:
            return {
                "status": "empty",
                "message": f"No files matching pattern {file_pattern} found in {directory}",
                "directory": str(directory),
                "pattern": file_pattern,
            }

        # Analyze each file
        results = {}
        artifacts = []

        for file_path in matching_files:
            try:
                # Check if an artifact already exists for this path
                existing_artifact = self.repository.get_by_path(file_path)

                if existing_artifact:
                    artifacts.append(existing_artifact)
                else:
                    # Process the file
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Create and save the artifact
                    artifact = CodeArtifact(
                        path=file_path,
                        name=file_path.name,
                        artifact_type="file",
                        content=content,
                    )

                    saved_artifact = self.repository.save(artifact)
                    artifacts.append(saved_artifact)
            except Exception as e:
                # Log errors but continue processing other files
                results[str(file_path)] = {"status": "error", "message": str(e)}

        # Analyze the codebase structure
        results["artifacts"] = [
            {
                "id": str(artifact.id),
                "name": artifact.name,
                "path": str(artifact.path),
                "type": artifact.artifact_type,
            }
            for artifact in artifacts
        ]

        # Calculate aggregate metrics
        total_lines = sum(
            len(artifact.content.split("\n")) if artifact.content else 0
            for artifact in artifacts
        )

        results["summary"] = {
            "file_count": len(artifacts),
            "total_lines": total_lines,
            "directory": str(directory),
            "pattern": file_pattern,
        }

        # If depth > 1, add more detailed analysis
        if depth > 1:
            # Calculate complexity for each artifact
            complexities = []
            for artifact in artifacts:
                try:
                    complexity = await self.calculate_complexity(artifact.id)
                    complexities.append((artifact, complexity))
                except Exception as e:
                    # Skip artifacts that can't be analyzed
                    logger.warning(
                        f"Could not calculate complexity for {artifact.id}: {e}"
                    )
                    continue

            # Find the most complex artifacts
            complexities.sort(key=lambda x: x[1], reverse=True)

            results["complexity"] = {
                "average": sum(c for _, c in complexities) / len(complexities)
                if complexities
                else 0,
                "max": complexities[0][1] if complexities else 0,
                "most_complex": [
                    {
                        "id": str(artifact.id),
                        "name": artifact.name,
                        "path": str(artifact.path),
                        "complexity": complexity,
                    }
                    for artifact, complexity in complexities[:5]
                ]
                if complexities
                else [],
            }

        # If depth > 2, add knowledge extraction
        if depth > 2:
            # Extract knowledge from the most important artifacts
            knowledge_summary = []

            # Select artifacts to analyze (prioritize by complexity or size)
            artifacts_to_analyze = (
                [a for a, _ in complexities[:10]]
                if depth > 1 and complexities
                else artifacts[:10]
            )

            for artifact in artifacts_to_analyze:
                try:
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
                    # Skip artifacts that can't be analyzed
                    logger.warning(
                        f"Could not extract knowledge from {artifact.id}: {e}"
                    )
                    continue

            results["knowledge"] = knowledge_summary

        return results

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
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Get the file path
        file_path = artifact.path

        # Use the existing process_file function
        try:
            _, file_data = await process_file(file_path)
            return file_data["summary"]
        except Exception as e:
            # If there's an error, return a basic summary
            return f"Unable to generate summary: {str(e)}"

    async def get_structure(self, artifact_id: UUID) -> dict[str, list[dict[str, Any]]]:
        """
        Get the structure of a code artifact.

        Args:
            artifact_id: The ID of the artifact to get structure for

        Returns:
            Structure as a dictionary

        Raises:
            RepositoryError: If the artifact cannot be found
        """
        # Get the artifact
        artifact = self.repository.get_by_id(artifact_id)

        if not artifact:
            raise RepositoryError(
                message="Artifact not found",
                entity_type="CodeArtifact",
                operation="get_by_id",
                entity_id=str(artifact_id),
            )

        # Initialize structure
        structure = {"classes": [], "functions": [], "variables": []}

        # Parse the content if available
        if not artifact.content:
            return structure

        # Process based on file type
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""

        if file_ext in [".py", ".pyw"]:
            # For Python files, use AST to extract structure
            try:
                tree = ast.parse(artifact.content)

                # Extract classes
                for node in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                    methods = []

                    # Extract methods
                    for method in [
                        n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)
                    ]:
                        methods.append(
                            {
                                "name": method.name,
                                "line": method.lineno,
                                "docstring": ast.get_docstring(method) or "",
                            }
                        )

                    structure["classes"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node) or "",
                            "methods": methods,
                        }
                    )

                # Extract top-level functions
                for node in [
                    n
                    for n in ast.iter_child_nodes(tree)
                    if isinstance(n, ast.FunctionDef)
                ]:
                    structure["functions"].append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node) or "",
                            "args": [arg.arg for arg in node.args.args],
                        }
                    )

                # Extract top-level variables
                for node in [
                    n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.Assign)
                ]:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            structure["variables"].append(
                                {"name": target.id, "line": node.lineno}
                            )
            except SyntaxError:
                # If there's a syntax error, return basic structure
                pass

        return structure

    async def _analyze_content(
        self, artifact: CodeArtifact, depth: int = 1
    ) -> dict[str, Any]:
        """
        Analyze the content of an artifact.

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
            "size_bytes": len(artifact.content),
            "empty_lines": sum(1 for line in lines if not line.strip()),
            "file_type": artifact.path.suffix.lower()
            if artifact.path.suffix
            else "unknown",
        }

        # Standard analysis (depth >= 2)
        if depth >= 2:
            # Calculate complexity
            complexity = await self.calculate_complexity(artifact.id)
            results["complexity"] = {
                "score": complexity,
                "assessment": self._assess_complexity(complexity),
            }

            # Get structure
            structure = await self.get_structure(artifact.id)
            results["structure"] = structure

        # Deep analysis (depth >= 3)
        if depth >= 3:
            # Extract knowledge
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
                # Skip if dependencies can't be found
                logger.warning(f"Could not find dependencies for {artifact.id}: {e}")
                results["dependencies"] = []

        return results

    def _assess_complexity(self, complexity: float) -> str:
        """
        Assess the complexity score.

        Args:
            complexity: The complexity score

        Returns:
            Assessment description
        """
        if complexity < 5:
            return "Low complexity"
        elif complexity < 15:
            return "Moderate complexity"
        elif complexity < 30:
            return "High complexity"
        else:
            return "Very high complexity"
