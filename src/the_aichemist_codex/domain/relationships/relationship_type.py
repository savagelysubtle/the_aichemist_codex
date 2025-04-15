# FILE: src/the_aichemist_codex/domain/relationships/relationship_type.py
"""Consolidated Relationship types enum for AIchemist Codex."""

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
    LINKS_TO = "links_to"

    # Similarity relationships
    SIMILAR_TO = "similar_to"
    RELATED_TO = "related_to"

    # Structural relationships
    PART_OF = "part_of"

    # Temporal relationships
    PRECEDES = "precedes"
    FOLLOWS = "follows"

    # Creation relationships
    GENERATED_FROM = "generated_from"
    DERIVED_FROM = "derived_from"

    # Custom relationship
    CUSTOM = "custom"

    @classmethod
    def file_extension_map(cls) -> dict[str, set["RelationshipType"]]:
        """Get a mapping of file extensions to common default relationship types.

        Returns:
            Dictionary mapping file extensions to sets of relationship types
        """
        return {
            # Python
            ".py": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            # JavaScript/TypeScript
            ".js": {cls.IMPORTS, cls.EXTENDS, cls.REFERENCES, cls.REQUIRES, cls.CALLS},
            ".jsx": {cls.IMPORTS, cls.EXTENDS, cls.REFERENCES, cls.REQUIRES, cls.CALLS},
            ".ts": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            ".tsx": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            # Web
            ".html": {cls.INCLUDES, cls.REFERENCES, cls.LINKS_TO},
            ".css": {cls.REFERENCES, cls.IMPORTS},  # CSS can import
            ".scss": {cls.IMPORTS, cls.REFERENCES, cls.USES},
            # C/C++
            ".c": {cls.INCLUDES, cls.REFERENCES, cls.CALLS},
            ".cpp": {
                cls.INCLUDES,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            ".h": {cls.INCLUDES, cls.REFERENCES},
            ".hpp": {cls.INCLUDES, cls.EXTENDS, cls.IMPLEMENTS, cls.REFERENCES},
            # Java
            ".java": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            # C#
            ".cs": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
                cls.USES,
            },  # 'using' maps to IMPORTS or USES
            # Go
            ".go": {
                cls.IMPORTS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },  # Go uses interfaces implicitly
            # Rust
            ".rs": {cls.IMPORTS, cls.USES, cls.IMPLEMENTS, cls.REFERENCES, cls.CALLS},
            # Ruby
            ".rb": {cls.REQUIRES, cls.EXTENDS, cls.INCLUDES, cls.REFERENCES, cls.CALLS},
            # PHP
            ".php": {
                cls.REQUIRES,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
                cls.USES,
            },  # PHP 'use' for traits
            # Swift
            ".swift": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            # Kotlin
            ".kt": {
                cls.IMPORTS,
                cls.EXTENDS,
                cls.IMPLEMENTS,
                cls.REFERENCES,
                cls.CALLS,
            },
            # General
            ".json": {cls.REFERENCES},
            ".xml": {cls.REFERENCES, cls.INCLUDES},  # e.g., XInclude
            ".yaml": {cls.REFERENCES},
            ".yml": {cls.REFERENCES},
            ".md": {cls.REFERENCES, cls.LINKS_TO},
        }

    @classmethod
    def get_supported_types_for_extension(
        cls, extension: str
    ) -> set["RelationshipType"]:
        """Get the supported relationship types for a file extension.

        Args:
            extension: The file extension (including dot, e.g., '.py')

        Returns:
            Set of relationship types that can be detected for the file extension
        """
        extension = extension.lower()

        # Get the predefined mappings
        mappings = cls.file_extension_map()

        # Return the mapped types or a default set (just REFERENCES)
        return mappings.get(extension, {cls.REFERENCES})

    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get a list of all relationship type values.

        Returns:
            List of all relationship type values
        """
        return [t.value for t in cls]

    @classmethod
    def from_string(cls, value: str) -> "RelationshipType":
        """Convert a string to a RelationshipType enum member."""
        try:
            return cls(value.lower())
        except ValueError:
            # Fallback for potential case mismatches or return CUSTOM
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
            # If no match found, return CUSTOM or raise error
            # Let's default to CUSTOM for flexibility
            return cls.CUSTOM
