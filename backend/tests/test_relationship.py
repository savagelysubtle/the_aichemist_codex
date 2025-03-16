"""
Tests for the Relationship class.

This module contains tests for the Relationship class and RelationshipType enum.
"""

import uuid
from datetime import datetime
from pathlib import Path

import pytest

from backend.src.relationships.relationship import Relationship, RelationshipType


def test_relationship_creation() -> None:
    """Test creating a relationship with default values."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS

    rel = Relationship(source, target, rel_type)

    assert rel.source_path == source  # noqa: S101
    assert rel.target_path == target  # noqa: S101
    assert rel.rel_type == rel_type  # noqa: S101
    assert rel.strength == 1.0  # noqa: S101
    assert isinstance(rel.metadata, dict)  # noqa: S101
    assert len(rel.metadata) == 0  # noqa: S101
    assert isinstance(rel.created_at, datetime)  # noqa: S101
    assert rel.updated_at == rel.created_at  # noqa: S101
    assert isinstance(rel.id, str)  # noqa: S101


def test_relationship_creation_with_custom_values() -> None:
    """Test creating a relationship with custom values."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.REFERENCES
    strength = 0.75
    metadata = {"line": 42, "context": "import statement"}
    created_at = datetime(2023, 1, 1, 12, 0, 0)
    rel_id = str(uuid.uuid4())

    rel = Relationship(
        source,
        target,
        rel_type,
        strength=strength,
        metadata=metadata,
        created_at=created_at,
        id=rel_id,
    )

    assert rel.source_path == source  # noqa: S101
    assert rel.target_path == target  # noqa: S101
    assert rel.rel_type == rel_type  # noqa: S101
    assert rel.strength == strength  # noqa: S101
    assert rel.metadata == metadata  # noqa: S101
    assert rel.created_at == created_at  # noqa: S101
    assert rel.updated_at == created_at  # noqa: S101
    assert rel.id == rel_id  # noqa: S101


def test_relationship_invalid_strength() -> None:
    """Test that creating a relationship with invalid strength raises ValueError."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS

    # Test strength < 0.0
    with pytest.raises(ValueError):
        Relationship(source, target, rel_type, strength=-0.1)

    # Test strength > 1.0
    with pytest.raises(ValueError):
        Relationship(source, target, rel_type, strength=1.1)


def test_relationship_update() -> None:
    """Test updating a relationship."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS

    rel = Relationship(source, target, rel_type)
    original_created_at = rel.created_at
    original_updated_at = rel.updated_at

    # Wait a moment to ensure updated_at will be different
    import time

    time.sleep(0.001)

    # Update the relationship
    new_strength = 0.8
    new_metadata = {"line": 42}
    rel.update(strength=new_strength, metadata=new_metadata)

    assert rel.strength == new_strength  # noqa: S101
    assert "line" in rel.metadata  # noqa: S101
    assert rel.metadata["line"] == 42  # noqa: S101
    assert rel.created_at == original_created_at  # noqa: S101
    assert rel.updated_at > original_updated_at  # noqa: S101


def test_relationship_update_invalid_strength() -> None:
    """Test that updating a relationship with invalid strength raises ValueError."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS

    rel = Relationship(source, target, rel_type)

    # Test strength < 0.0
    with pytest.raises(ValueError):
        rel.update(strength=-0.1)

    # Test strength > 1.0
    with pytest.raises(ValueError):
        rel.update(strength=1.1)


def test_relationship_to_dict() -> None:
    """Test converting a relationship to a dictionary."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.REFERENCES
    strength = 0.75
    metadata = {"line": 42, "context": "import statement"}
    created_at = datetime(2023, 1, 1, 12, 0, 0)
    rel_id = "test-id-123"

    rel = Relationship(
        source,
        target,
        rel_type,
        strength=strength,
        metadata=metadata,
        created_at=created_at,
        id=rel_id,
    )

    rel_dict = rel.to_dict()

    assert rel_dict["id"] == rel_id  # noqa: S101
    assert rel_dict["source_path"] == str(source)  # noqa: S101
    assert rel_dict["target_path"] == str(target)  # noqa: S101
    assert rel_dict["rel_type"] == rel_type.name  # noqa: S101
    assert rel_dict["strength"] == strength  # noqa: S101
    assert rel_dict["metadata"] == metadata  # noqa: S101
    assert rel_dict["created_at"] == created_at.isoformat()  # noqa: S101
    assert rel_dict["updated_at"] == created_at.isoformat()  # noqa: S101


def test_relationship_from_dict() -> None:
    """Test creating a relationship from a dictionary."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.REFERENCES
    strength = 0.75
    metadata = {"line": 42, "context": "import statement"}
    created_at = datetime(2023, 1, 1, 12, 0, 0)
    rel_id = "test-id-123"

    rel_dict = {
        "id": rel_id,
        "source_path": str(source),
        "target_path": str(target),
        "rel_type": rel_type.name,
        "strength": strength,
        "metadata": metadata,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
    }

    rel = Relationship.from_dict(rel_dict)

    assert rel.id == rel_id  # noqa: S101
    assert rel.source_path == source  # noqa: S101
    assert rel.target_path == target  # noqa: S101
    assert rel.rel_type == rel_type  # noqa: S101
    assert rel.strength == strength  # noqa: S101
    assert rel.metadata == metadata  # noqa: S101
    assert rel.created_at == created_at  # noqa: S101
    assert rel.updated_at == created_at  # noqa: S101


def test_relationship_equality() -> None:
    """Test relationship equality comparison."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS

    rel1 = Relationship(source, target, rel_type)
    rel2 = Relationship(source, target, rel_type)

    # Different relationships with same source, target, and type should be equal
    assert rel1 == rel2  # noqa: S101

    # Different relationship type
    rel3 = Relationship(source, target, RelationshipType.REFERENCES)
    assert rel1 != rel3  # noqa: S101

    # Different target
    rel4 = Relationship(source, Path("/path/to/other.py"), rel_type)
    assert rel1 != rel4  # noqa: S101

    # Different source
    rel5 = Relationship(Path("/path/to/other_source.py"), target, rel_type)
    assert rel1 != rel5  # noqa: S101

    # Not a relationship
    assert rel1 != "not a relationship"  # noqa: S101


def test_relationship_hash() -> None:
    """Test relationship hashing for use in sets and dictionaries."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS

    rel1 = Relationship(source, target, rel_type)
    rel2 = Relationship(source, target, rel_type)

    # Different relationship objects with same source, target,
    # and type should hash the same
    assert hash(rel1) == hash(rel2)  # noqa: S101

    # Can be used in a set
    rel_set = {rel1, rel2}
    assert len(rel_set) == 1  # noqa: S101  # Only one unique relationship


def test_relationship_repr() -> None:
    """Test the string representation of a relationship."""
    source = Path("/path/to/source.py")
    target = Path("/path/to/target.py")
    rel_type = RelationshipType.IMPORTS
    strength = 0.75

    rel = Relationship(source, target, rel_type, strength=strength)

    repr_str = repr(rel)
    assert str(source) in repr_str  # noqa: S101
    assert str(target) in repr_str  # noqa: S101
    assert rel_type.name in repr_str  # noqa: S101
    assert str(strength) in repr_str  # noqa: S101
