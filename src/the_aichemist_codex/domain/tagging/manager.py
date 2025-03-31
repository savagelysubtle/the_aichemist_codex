"""
Tag management interface for the domain layer.

This module re-exports the TagManager implementation from the infrastructure
layer to make it available to domain components.
"""

from the_aichemist_codex.infrastructure.extraction.tagging.manager import TagManager

__all__ = ["TagManager"]
