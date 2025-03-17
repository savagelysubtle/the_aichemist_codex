"""
Tests for the RelationshipStore class.

This module contains tests for the RelationshipStore class which handles
persisting and retrieving file relationships.
"""

import sqlite3
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from the_aichemist_codex.backend.relationships.relationship import Relationship, RelationshipType
from the_aichemist_codex.backend.relationships.store import RelationshipStore


@pytest.fixture
def temp_db_path() -> Generator[Path]:
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        yield Path(tmp.name)


@pytest.fixture
def relationship_store(temp_db_path: Path) -> RelationshipStore:
    """Create a RelationshipStore with a temporary database."""
    return RelationshipStore(temp_db_path)


@pytest.fixture
def sample_relationships() -> list[Relationship]:
    """Create a list of sample relationships for testing."""
    source1 = Path("/path/to/source1.py")
    source2 = Path("/path/to/source2.py")
    target1 = Path("/path/to/target1.py")
    target2 = Path("/path/to/target2.py")

    return [
        Relationship(
            source1,
            target1,
            RelationshipType.IMPORTS,
            strength=0.9,
            metadata={"line": 10},
        ),
        Relationship(
            source1,
            target2,
            RelationshipType.REFERENCES,
            strength=0.7,
            metadata={"line": 20},
        ),
        Relationship(
            source2,
            target1,
            RelationshipType.SIMILAR_CONTENT,
            strength=0.5,
            metadata={"similarity_score": 0.5},
        ),
        Relationship(
            source2,
            target2,
            RelationshipType.MODIFIED_TOGETHER,
            strength=0.8,
            metadata={"commit_count": 5},
        ),
    ]


@pytest.mark.unit
def test_store_initialization(temp_db_path: Path) -> None:
    """Test that the store initializes correctly and creates the database."""
    # Create the store but no need to assign it to a variable
    RelationshipStore(temp_db_path)

    # Check that the database file exists
    assert temp_db_path.exists()  # noqa: S101

    # Check that the tables were created
    with sqlite3.connect(str(temp_db_path)) as conn:
        cursor = conn.cursor()

        # Check relationships table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'"
        )
        assert cursor.fetchone() is not None  # noqa: S101

        # Check indexes
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_source_path'"
        )
        assert cursor.fetchone() is not None  # noqa: S101

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_target_path'"
        )
        assert cursor.fetchone() is not None  # noqa: S101

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_rel_type'"
        )
        assert cursor.fetchone() is not None  # noqa: S101


@pytest.mark.unit
def test_add_relationship(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test adding a single relationship to the store."""
    rel = sample_relationships[0]
    relationship_store.add_relationship(rel)

    # Retrieve the relationship and check it matches
    retrieved = relationship_store.get_relationship(rel.id)
    assert retrieved is not None  # noqa: S101
    assert retrieved.id == rel.id  # noqa: S101
    assert retrieved.source_path == rel.source_path  # noqa: S101
    assert retrieved.target_path == rel.target_path  # noqa: S101
    assert retrieved.rel_type == rel.rel_type  # noqa: S101
    assert retrieved.strength == rel.strength  # noqa: S101
    assert retrieved.metadata == rel.metadata  # noqa: S101


@pytest.mark.unit
def test_add_relationships(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test adding multiple relationships to the store."""
    relationship_store.add_relationships(sample_relationships)

    # Check that all relationships were added
    for rel in sample_relationships:
        retrieved = relationship_store.get_relationship(rel.id)
        assert retrieved is not None  # noqa: S101
        assert retrieved.id == rel.id  # noqa: S101


@pytest.mark.unit
def test_get_relationship_not_found(relationship_store: RelationshipStore) -> None:
    """Test getting a relationship that doesn't exist."""
    retrieved = relationship_store.get_relationship("non-existent-id")
    assert retrieved is None  # noqa: S101


@pytest.mark.unit
def test_get_relationships_for_file(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test getting all relationships for a specific file."""
    relationship_store.add_relationships(sample_relationships)

    # Get relationships where source1 is the source
    source1 = sample_relationships[0].source_path
    rels_source = relationship_store.get_relationships_for_file(
        source1, as_source=True, as_target=False
    )
    assert len(rels_source) == 2  # noqa: S101

    # Get relationships where target1 is the target
    target1 = sample_relationships[0].target_path
    rels_target = relationship_store.get_relationships_for_file(
        target1, as_source=False, as_target=True
    )
    assert len(rels_target) == 2  # noqa: S101

    # Get all relationships involving source1
    rels_both = relationship_store.get_relationships_for_file(source1)
    assert len(rels_both) == 2  # noqa: S101  # source1 is only used as source in our samples

    # Filter by relationship type
    rels_filtered = relationship_store.get_relationships_for_file(
        source1, rel_types=[RelationshipType.IMPORTS]
    )
    assert len(rels_filtered) == 1  # noqa: S101
    assert rels_filtered[0].rel_type == RelationshipType.IMPORTS  # noqa: S101


@pytest.mark.unit
def test_get_related_files(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test getting all files related to a specific file."""
    relationship_store.add_relationships(sample_relationships)

    # Get files related to source1
    source1 = sample_relationships[0].source_path
    related_files = relationship_store.get_related_files(source1)

    assert len(related_files) == 2  # noqa: S101

    # Check that the related files are correct
    related_paths = [path for path, _, _ in related_files]
    assert sample_relationships[0].target_path in related_paths  # noqa: S101
    assert sample_relationships[1].target_path in related_paths  # noqa: S101

    # Filter by relationship type
    related_files_filtered = relationship_store.get_related_files(
        source1, rel_types=[RelationshipType.IMPORTS]
    )
    assert len(related_files_filtered) == 1  # noqa: S101
    assert related_files_filtered[0][1] == RelationshipType.IMPORTS  # noqa: S101

    # Filter by minimum strength
    related_files_strong = relationship_store.get_related_files(
        source1, min_strength=0.8
    )
    assert len(related_files_strong) == 1  # noqa: S101
    assert related_files_strong[0][2] >= 0.8  # noqa: S101


@pytest.mark.unit
def test_delete_relationship(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test deleting a relationship by ID."""
    relationship_store.add_relationships(sample_relationships)

    # Delete one relationship
    rel_id = sample_relationships[0].id
    result = relationship_store.delete_relationship(rel_id)

    assert result is True  # noqa: S101
    assert relationship_store.get_relationship(rel_id) is None  # noqa: S101

    # Try to delete a non-existent relationship
    result = relationship_store.delete_relationship("non-existent-id")
    assert result is False  # noqa: S101


@pytest.mark.unit
def test_delete_relationships_for_file(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test deleting all relationships involving a specific file."""
    relationship_store.add_relationships(sample_relationships)

    # Delete relationships for source1
    source1 = sample_relationships[0].source_path
    count = relationship_store.delete_relationships_for_file(source1)

    assert count == 2  # noqa: S101

    # Check that the relationships were deleted
    rels = relationship_store.get_relationships_for_file(source1)
    assert len(rels) == 0  # noqa: S101


@pytest.mark.unit
def test_clear_all_relationships(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test clearing all relationships from the store."""
    relationship_store.add_relationships(sample_relationships)

    # Clear all relationships
    count = relationship_store.clear_all_relationships()

    assert count == len(sample_relationships)  # noqa: S101

    # Check that all relationships were deleted
    for rel in sample_relationships:
        assert relationship_store.get_relationship(rel.id) is None  # noqa: S101


@pytest.mark.unit
def test_get_all_relationships(
    relationship_store: RelationshipStore, sample_relationships: list[Relationship]
) -> None:
    """Test getting all relationships from the store."""
    relationship_store.add_relationships(sample_relationships)

    # Get all relationships
    all_rels = relationship_store.get_all_relationships()

    assert len(all_rels) == len(sample_relationships)  # noqa: S101

    # Filter by relationship type
    imports_rels = relationship_store.get_all_relationships(
        rel_types=[RelationshipType.IMPORTS]
    )
    assert len(imports_rels) == 1  # noqa: S101
    assert imports_rels[0].rel_type == RelationshipType.IMPORTS  # noqa: S101

    # Filter by minimum strength
    strong_rels = relationship_store.get_all_relationships(min_strength=0.8)
    assert len(strong_rels) == 2  # noqa: S101
    for rel in strong_rels:
        assert rel.strength >= 0.8  # noqa: S101
