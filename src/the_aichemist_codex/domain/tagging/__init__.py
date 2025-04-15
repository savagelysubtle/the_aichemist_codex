"""
Tagging domain module for AIchemist Codex.

Defines core concepts related to tagging, suggestion, and hierarchy.
"""

# Import interfaces from the domain layers
from the_aichemist_codex.domain.repositories.interfaces.tag_hierarchy_repository import (
    TagHierarchyRepositoryInterface,
)
from the_aichemist_codex.domain.repositories.interfaces.tag_repository import (
    TagRepositoryInterface,
)
from the_aichemist_codex.domain.services.interfaces.tag_classifier import (
    TagClassifierInterface,
)

# Import domain services/value objects/entities related to tagging
from .suggester import TagSuggester

__all__ = [
    # Interfaces
    "TagClassifierInterface",
    "TagHierarchyRepositoryInterface",
    "TagRepositoryInterface",
    # Domain Services/Entities
    "TagSuggester",
]
