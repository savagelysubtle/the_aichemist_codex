"""Relationship types for AIchemist Codex.

This module provides the RelationshipType class which defines the different
types of relationships that can exist between files in a codebase.
"""

from enum import Enum


class RelationshipType(str, Enum):
    """Defines the different types of relationships between files.

    The RelationshipType enum provides a set of predefined relationship types
    that can be used to categorize the connections between files.
    """

    # Inheritance relationships
    EXTENDS = "extends"
    IMPLEMENTS = "implements"

    # Dependency relationships
    IMPORTS = "imports"
    INCLUDES = "includes"
    USES = "uses"
    REQUIRES = "requires"

    # Composition relationships
    CONTAINS = "contains"
    COMPOSES = "composes"

    # Reference relationships
    REFERENCES = "references"
    CALLS = "calls"

    # Custom relationship
    CUSTOM = "custom"

    @classmethod
    def file_extension_map(cls) -> dict[str, set[str]]:
        """Get a mapping of file extensions to default relationship types.

        Returns:
            Dictionary mapping file extensions to sets of relationship types
        """
        return {
            # Python
            ".py": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # JavaScript/TypeScript
            ".js": {cls.IMPORTS, cls.EXTENDS, cls.REFERENCES, cls.REQUIRES},
            ".jsx": {cls.IMPORTS, cls.EXTENDS, cls.REFERENCES, cls.REQUIRES},
            ".ts": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            ".tsx": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Web
            ".html": {cls.INCLUDES, cls.REFERENCES},
            ".css": {cls.REFERENCES},
            ".scss": {cls.IMPORTS, cls.REFERENCES},
            # C/C++
            ".c": {cls.INCLUDES, cls.REFERENCES, cls.CALLS},
            ".cpp": {cls.INCLUDES, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            ".h": {cls.INCLUDES, cls.REFERENCES},
            ".hpp": {cls.INCLUDES, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Java
            ".java": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # C#
            ".cs": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Go
            ".go": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Rust
            ".rs": {cls.IMPORTS, cls.USES, cls.IMPLEMENTS, cls.REFERENCES},
            # Ruby
            ".rb": {cls.REQUIRES, cls.EXTENDS, cls.INCLUDES, cls.REFERENCES},
            # PHP
            ".php": {cls.REQUIRES, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Swift
            ".swift": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Kotlin
            ".kt": {cls.IMPORTS, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # General
            ".json": {cls.REFERENCES},
            ".xml": {cls.REFERENCES, cls.INCLUDES},
            ".yaml": {cls.REFERENCES},
            ".md": {cls.REFERENCES},
        }

    @classmethod
    def get_supported_types_for_extension(cls, extension: str) -> set[str]:
        """Get the supported relationship types for a file extension.

        Args:
            extension: The file extension (including dot, e.g., '.py')

        Returns:
            Set of relationship types that can be detected for the file extension
        """
        extension = extension.lower()

        # Get the predefined mappings
        mappings = cls.file_extension_map()

        # Return the mapped types or a default set
        return mappings.get(extension, {cls.REFERENCES})

    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get a list of all relationship types.

        Returns:
            List of all relationship type values
        """
        return [t.value for t in cls]
