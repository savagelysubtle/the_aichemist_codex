"""
Tag classification interface for the domain layer.

This module re-exports the TagClassifier implementation from the infrastructure
layer to make it available to domain components.
"""

from the_aichemist_codex.infrastructure.extraction.tagging.classifier import (
    TagClassifier,
)

__all__ = ["TagClassifier"]
