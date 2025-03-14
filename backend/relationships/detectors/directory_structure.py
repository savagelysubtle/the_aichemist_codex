"""
Directory structure relationship detector.

This module provides the DirectoryStructureDetector class for identifying
relationships based on file system hierarchy and naming patterns.
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Pattern, Tuple

from ..detector import DetectionStrategy, RelationshipDetectorBase
from ..relationship import Relationship, RelationshipType

logger = logging.getLogger(__name__)


class DirectoryStructureDetector(RelationshipDetectorBase):
    """
    Detects relationships based on directory structure and naming patterns.

    This detector identifies parent-child relationships between directories and files,
    sibling relationships between files in the same directory, and relationships
    based on naming patterns.
    """

    # Regular expression patterns for identifying related files by name
    NAME_PATTERNS = [
        # Test files: file.py -> file_test.py, test_file.py
        (r"^(.+)\.(.+)$", r"\1_test.\2", 0.9),  # file.py -> file_test.py
        (r"^(.+)\.(.+)$", r"test_\1.\2", 0.9),  # file.py -> test_file.py
        # Implementation & interface pairs
        (r"^(.+)\.py$", r"\1_impl.py", 0.8),  # interface.py -> interface_impl.py
        (r"^(.+)_impl\.py$", r"\1.py", 0.8),  # interface_impl.py -> interface.py
        (r"^(.+)\.ts$", r"\1.d.ts", 0.8),  # file.ts -> file.d.ts
        # Component pairs (common in web development)
        (r"^(.+)\.jsx$", r"\1.css", 0.7),  # Component.jsx -> Component.css
        (r"^(.+)\.tsx$", r"\1.css", 0.7),  # Component.tsx -> Component.css
        (r"^(.+)\.vue$", r"\1.scss", 0.7),  # Component.vue -> Component.scss
        # Module & spec/test files
        (r"^(.+)\.js$", r"\1.spec.js", 0.9),  # file.js -> file.spec.js
        (r"^(.+)\.ts$", r"\1.spec.ts", 0.9),  # file.ts -> file.spec.ts
    ]

    def __init__(self, workspace_root: Path, max_depth: int = 1):
        """
        Initialize the directory structure detector.

        Args:
            workspace_root: Root directory of the workspace
            max_depth: Maximum depth for parent-child relationships (default: 1)
        """
        self.workspace_root = workspace_root
        self.max_depth = max_depth
        self._compiled_patterns: List[Tuple[Pattern, str, float]] = []

        # Compile regex patterns for better performance
        for pattern, replacement, strength in self.NAME_PATTERNS:
            self._compiled_patterns.append((re.compile(pattern), replacement, strength))

    @property
    def strategy(self) -> DetectionStrategy:
        """Get the detection strategy used by this detector."""
        return DetectionStrategy.DIRECTORY_STRUCTURE

    def detect_relationships(self, path: Path) -> List[Relationship]:
        """
        Detect directory structure relationships for the given file.

        Args:
            path: Path to the file to analyze

        Returns:
            List of detected relationships
        """
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return []

        relationships = []

        # Detect parent-child relationships
        parent_child_rels = self._detect_parent_child_relationships(path)
        relationships.extend(parent_child_rels)

        # Detect sibling relationships
        sibling_rels = self._detect_sibling_relationships(path)
        relationships.extend(sibling_rels)

        # Detect relationships based on naming patterns
        naming_rels = self._detect_naming_pattern_relationships(path)
        relationships.extend(naming_rels)

        return relationships

    def _detect_parent_child_relationships(self, path: Path) -> List[Relationship]:
        """
        Detect parent-child relationships for the given path.

        Args:
            path: Path to analyze

        Returns:
            List of parent-child relationships
        """
        relationships = []

        # Skip directories
        if path.is_dir():
            return relationships

        # Create relationship between file and its parent directory
        parent_dir = path.parent
        if parent_dir != self.workspace_root:
            # File is contained in a directory
            relationships.append(
                Relationship(
                    source_path=parent_dir,
                    target_path=path,
                    rel_type=RelationshipType.PARENT_CHILD,
                    strength=1.0,
                    metadata={"level": 1},
                )
            )

            # Check parent directories up to max_depth
            current_dir = parent_dir
            level = 2

            while level <= self.max_depth:
                parent_of_parent = current_dir.parent

                # Stop if we reached the workspace root or filesystem root
                if (
                    parent_of_parent == self.workspace_root
                    or parent_of_parent == current_dir
                ):
                    break

                # Create relationship with higher level parent
                relationships.append(
                    Relationship(
                        source_path=parent_of_parent,
                        target_path=path,
                        rel_type=RelationshipType.PARENT_CHILD,
                        strength=1.0
                        / level,  # Weaker relationship for more distant parents
                        metadata={"level": level},
                    )
                )

                current_dir = parent_of_parent
                level += 1

        return relationships

    def _detect_sibling_relationships(self, path: Path) -> List[Relationship]:
        """
        Detect sibling relationships (files in the same directory).

        Args:
            path: Path to analyze

        Returns:
            List of sibling relationships
        """
        relationships = []

        # Skip directories
        if path.is_dir():
            return relationships

        # Get all files in the same directory
        parent_dir = path.parent

        try:
            siblings = [
                parent_dir / f
                for f in os.listdir(parent_dir)
                if (parent_dir / f).is_file() and (parent_dir / f) != path
            ]
        except (PermissionError, FileNotFoundError) as e:
            logger.warning(f"Cannot list directory {parent_dir}: {e}")
            return relationships

        # Create sibling relationships
        for sibling in siblings:
            # Files in the same directory with the same extension have stronger relationship
            strength = 0.7
            if sibling.suffix == path.suffix:
                strength = 0.9

            relationships.append(
                Relationship(
                    source_path=path,
                    target_path=sibling,
                    rel_type=RelationshipType.SIBLING,
                    strength=strength,
                    metadata={"directory": str(parent_dir)},
                )
            )

        return relationships

    def _detect_naming_pattern_relationships(self, path: Path) -> List[Relationship]:
        """
        Detect relationships based on common naming patterns.

        Args:
            path: Path to analyze

        Returns:
            List of detected relationships
        """
        relationships = []

        # Skip directories
        if path.is_dir():
            return relationships

        filename = path.name
        parent_dir = path.parent

        # Check all patterns
        for pattern, replacement, strength in self._compiled_patterns:
            match = pattern.match(filename)
            if not match:
                continue

            # Generate the target filename using the pattern
            try:
                if isinstance(replacement, str):
                    target_filename = pattern.sub(replacement, filename)
                else:
                    # For more complex replacements that might use groups
                    target_filename = replacement(match)
            except Exception as e:
                logger.warning(f"Error applying pattern {pattern} to {filename}: {e}")
                continue

            # Check if the target file exists
            target_path = parent_dir / target_filename
            if target_path.exists() and target_path.is_file():
                # Create a relationship
                rel_type = RelationshipType.REFERENCES

                # Determine relationship type based on naming pattern
                if (
                    "_test" in target_filename
                    or "test_" in target_filename
                    or ".spec." in target_filename
                ):
                    rel_type = RelationshipType.EXTRACTED_FROM
                    metadata = {"relationship": "test-code"}
                elif target_filename.endswith(".d.ts") and filename.endswith(".ts"):
                    rel_type = RelationshipType.EXTRACTED_FROM
                    metadata = {"relationship": "typescript-definition"}
                elif (
                    target_filename.endswith(".css")
                    or target_filename.endswith(".scss")
                ) and (
                    filename.endswith(".jsx")
                    or filename.endswith(".tsx")
                    or filename.endswith(".vue")
                ):
                    rel_type = RelationshipType.REFERENCES
                    metadata = {"relationship": "component-style"}
                else:
                    metadata = {"relationship": "naming-pattern"}

                relationships.append(
                    Relationship(
                        source_path=path,
                        target_path=target_path,
                        rel_type=rel_type,
                        strength=strength,
                        metadata=metadata,
                    )
                )

        return relationships
