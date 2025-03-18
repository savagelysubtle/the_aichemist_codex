"""
Relationship detection functionality.

This module provides classes and utilities for detecting relationships
between files using various strategies.
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path

from ....core.models import RelationshipType
from ....registry import Registry
from .relationship import Relationship

logger = logging.getLogger(__name__)


class DetectionStrategy(ABC):
    """
    Abstract base class for relationship detection strategies.

    Concrete strategies should implement the detect_relationships method
    to identify relationships for a given file.
    """

    def __init__(self):
        """Initialize the detection strategy."""
        self._registry = Registry.get_instance()
        self._file_reader = self._registry.file_reader
        self._validator = self._registry.file_validator

    @abstractmethod
    async def detect_relationships(self, file_path: Path) -> list[Relationship]:
        """
        Detect relationships for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of detected relationships

        Raises:
            Exception: If detection fails
        """
        pass


class ImportDetectionStrategy(DetectionStrategy):
    """
    Strategy for detecting import relationships.

    This strategy analyzes code files to identify imports and includes.
    """

    # Common import patterns for different languages
    IMPORT_PATTERNS = {
        ".py": r"import\s+([^\s;]+)|from\s+([^\s;]+)\s+import",
        ".js": r"(import|require)\s*\(?[\'\"]([^\'\"]+)[\'\"]",
        ".java": r"import\s+([^;]+);",
        ".cpp": r"#include\s*[<\"]([^>\"]+)[>\"]",
        ".c": r"#include\s*[<\"]([^>\"]+)[>\"]",
        ".h": r"#include\s*[<\"]([^>\"]+)[>\"]",
        ".rb": r"require[\s\(]+[\'\":]([^\'\"]+)[\'\":]",
    }

    async def detect_relationships(self, file_path: Path) -> list[Relationship]:
        """
        Detect import relationships for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of detected import relationships
        """
        relationships = []
        file_ext = file_path.suffix.lower()

        # Check if we have a pattern for this file type
        if file_ext not in self.IMPORT_PATTERNS:
            return relationships

        try:
            # Read the file content
            file_content = await self._file_reader.read_text(str(file_path))

            # Get the pattern for this file type
            pattern = self.IMPORT_PATTERNS[file_ext]

            # Find all imports
            imports = re.findall(pattern, file_content)

            # Process the imports
            for import_match in imports:
                if isinstance(import_match, tuple):
                    # Some regex patterns return tuples
                    import_name = next((m for m in import_match if m), "")
                else:
                    import_name = import_match

                if not import_name:
                    continue

                # Convert the import to a potential file path
                import_path = self._resolve_import_to_file_path(
                    file_path, import_name, file_ext
                )
                if import_path and import_path.exists():
                    # Create a relationship
                    rel = Relationship(
                        source_path=file_path,
                        target_path=import_path,
                        rel_type=RelationshipType.IMPORTS,
                        strength=1.0,
                        metadata={"import_name": import_name},
                    )
                    relationships.append(rel)

        except Exception as e:
            logger.warning(f"Error detecting import relationships for {file_path}: {e}")

        return relationships

    def _resolve_import_to_file_path(
        self, source_file: Path, import_name: str, file_ext: str
    ) -> Path | None:
        """
        Resolve an import name to a file path.

        Args:
            source_file: Path to the source file
            import_name: The import name
            file_ext: File extension of the source file

        Returns:
            Resolved file path or None if it can't be resolved
        """
        # This is a simplified implementation. In a real system, you would need
        # more sophisticated logic to handle different import styles and language-specific rules.

        # Try to resolve relative to the source file directory
        source_dir = source_file.parent

        # For Python
        if file_ext == ".py":
            # Try with .py extension
            potential_path = source_dir / f"{import_name.replace('.', '/')}.py"
            if potential_path.exists():
                return potential_path

            # Try as a directory with __init__.py
            init_path = source_dir / import_name.replace(".", "/") / "__init__.py"
            if init_path.exists():
                return init_path

        # For JavaScript
        elif file_ext in {".js", ".jsx", ".ts", ".tsx"}:
            # Try exact path
            potential_path = source_dir / import_name
            if potential_path.exists():
                return potential_path

            # Try with .js extension
            js_path = source_dir / f"{import_name}.js"
            if js_path.exists():
                return js_path

            # Try with other common extensions
            for ext in [".jsx", ".ts", ".tsx"]:
                ext_path = source_dir / f"{import_name}{ext}"
                if ext_path.exists():
                    return ext_path

            # Try as index.js in directory
            index_path = source_dir / import_name / "index.js"
            if index_path.exists():
                return index_path

        # For C/C++
        elif file_ext in {".c", ".cpp", ".h"}:
            # Try relative to source
            potential_path = source_dir / import_name
            if potential_path.exists():
                return potential_path

        # If we couldn't resolve it, return None
        return None


class RelationshipDetector:
    """
    Orchestrates detection of file relationships.

    This class uses multiple detection strategies to identify
    relationships between files.
    """

    def __init__(self):
        """Initialize the relationship detector with default strategies."""
        self._registry = Registry.get_instance()
        self._validator = self._registry.file_validator
        self._strategies = {
            "import": ImportDetectionStrategy(),
            # Add more strategies here as they are implemented
        }

    async def detect_relationships(
        self, file_path: Path, strategies: list[str] = None
    ) -> list[Relationship]:
        """
        Detect relationships for a file using specified strategies.

        Args:
            file_path: Path to the file
            strategies: List of strategy names to use (uses all if None)

        Returns:
            List of detected relationships

        Raises:
            FileError: If the file cannot be accessed
        """
        # Validate the file path
        file_path_str = str(file_path)
        self._validator.ensure_path_safe(file_path_str)

        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            raise FileNotFoundError(f"File does not exist: {file_path}")

        # Determine which strategies to use
        if strategies is None:
            active_strategies = list(self._strategies.values())
        else:
            active_strategies = [
                self._strategies[s] for s in strategies if s in self._strategies
            ]

        if not active_strategies:
            logger.warning(f"No valid detection strategies specified: {strategies}")
            return []

        # Run each detection strategy
        all_relationships = []
        for strategy in active_strategies:
            try:
                relationships = await strategy.detect_relationships(file_path)
                all_relationships.extend(relationships)
            except Exception as e:
                logger.warning(
                    f"Error in detection strategy {strategy.__class__.__name__} for {file_path}: {e}"
                )

        return all_relationships
