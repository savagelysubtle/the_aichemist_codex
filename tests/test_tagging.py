"""Tests for the tagging module."""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from backend.tagging.hierarchy import TagHierarchy
from backend.tagging.manager import TagManager
from backend.tagging.schema import TagSchema


class TestTagSchema:
    """Test the TagSchema class."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = Path(f.name)

        yield db_path

        # Cleanup
        if db_path.exists():
            os.unlink(db_path)

    async def test_initialize(self, db_path):
        """Test initializing the schema."""
        schema = TagSchema(db_path)
        await schema.initialize()

        # Check if tables were created
        conn = schema.get_connection()
        cursor = conn.cursor()

        # Check tags table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tags'"
        )
        assert cursor.fetchone() is not None

        # Check tag_hierarchy table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tag_hierarchy'"
        )
        assert cursor.fetchone() is not None

        # Check file_tags table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='file_tags'"
        )
        assert cursor.fetchone() is not None

        schema.close()

    async def test_reset(self, db_path):
        """Test resetting the schema."""
        schema = TagSchema(db_path)
        await schema.initialize()

        # Add some data
        conn = schema.get_connection()
        conn.execute("INSERT INTO tags (name, description) VALUES ('test', 'Test tag')")
        conn.commit()

        # Reset
        await schema.reset()

        # Check if data was removed
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tags")
        assert cursor.fetchone()[0] == 0

        schema.close()


class TestTagManager:
    """Test the TagManager class."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = Path(f.name)

        yield db_path

        # Cleanup
        if db_path.exists():
            os.unlink(db_path)

    @pytest.fixture
    async def tag_manager(self, db_path):
        """Create a TagManager instance."""
        manager = TagManager(db_path)
        await manager.initialize()

        yield manager

        await manager.close()

    @pytest.fixture
    def test_files(self):
        """Create temporary test files."""
        temp_dir = tempfile.mkdtemp()

        # Create test files
        file1 = Path(temp_dir) / "test1.txt"
        file2 = Path(temp_dir) / "test2.txt"
        file3 = Path(temp_dir) / "test3.txt"

        file1.write_text("This is test file 1.")
        file2.write_text("This is test file 2.")
        file3.write_text("This is test file 3.")

        yield {"dir": Path(temp_dir), "file1": file1, "file2": file2, "file3": file3}

        # Cleanup
        shutil.rmtree(temp_dir)

    async def test_create_tag(self, tag_manager):
        """Test creating a tag."""
        tag_id = await tag_manager.create_tag("test", "Test tag")
        assert tag_id is not None

        tag = await tag_manager.get_tag(tag_id)
        assert tag is not None
        assert tag["name"] == "test"
        assert tag["description"] == "Test tag"

    async def test_get_tag_by_name(self, tag_manager):
        """Test getting a tag by name."""
        await tag_manager.create_tag("test", "Test tag")

        tag = await tag_manager.get_tag_by_name("test")
        assert tag is not None
        assert tag["name"] == "test"
        assert tag["description"] == "Test tag"

        # Test case insensitivity
        tag = await tag_manager.get_tag_by_name("TEST")
        assert tag is not None
        assert tag["name"] == "test"

    async def test_update_tag(self, tag_manager):
        """Test updating a tag."""
        tag_id = await tag_manager.create_tag("test", "Test tag")

        # Update name
        updated = await tag_manager.update_tag(tag_id, name="updated")
        assert updated is True

        tag = await tag_manager.get_tag(tag_id)
        assert tag["name"] == "updated"
        assert tag["description"] == "Test tag"

        # Update description
        updated = await tag_manager.update_tag(
            tag_id, description="Updated description"
        )
        assert updated is True

        tag = await tag_manager.get_tag(tag_id)
        assert tag["name"] == "updated"
        assert tag["description"] == "Updated description"

    async def test_delete_tag(self, tag_manager):
        """Test deleting a tag."""
        tag_id = await tag_manager.create_tag("test", "Test tag")

        deleted = await tag_manager.delete_tag(tag_id)
        assert deleted is True

        tag = await tag_manager.get_tag(tag_id)
        assert tag is None

    async def test_get_all_tags(self, tag_manager):
        """Test getting all tags."""
        await tag_manager.create_tag("tag1", "Tag 1")
        await tag_manager.create_tag("tag2", "Tag 2")
        await tag_manager.create_tag("tag3", "Tag 3")

        tags = await tag_manager.get_all_tags()
        assert len(tags) == 3
        assert sorted([tag["name"] for tag in tags]) == ["tag1", "tag2", "tag3"]

    async def test_add_file_tag(self, tag_manager, test_files):
        """Test adding a tag to a file."""
        file_path = test_files["file1"]

        # Add tag by name (auto-create)
        added = await tag_manager.add_file_tag(file_path, tag_name="test")
        assert added is True

        # Add existing tag by ID
        tag = await tag_manager.get_tag_by_name("test")
        added = await tag_manager.add_file_tag(file_path, tag_id=tag["id"])
        assert added is False  # Already exists

        # Check tags
        tags = await tag_manager.get_file_tags(file_path)
        assert len(tags) == 1
        assert tags[0]["name"] == "test"

    async def test_add_file_tags(self, tag_manager, test_files):
        """Test adding multiple tags to a file."""
        file_path = test_files["file1"]

        # Add multiple tags
        tags = [("tag1", 1.0), ("tag2", 0.8), ("tag3", 0.6)]
        count = await tag_manager.add_file_tags(file_path, tags)
        assert count == 3

        # Check tags
        file_tags = await tag_manager.get_file_tags(file_path)
        assert len(file_tags) == 3
        assert sorted([tag["name"] for tag in file_tags]) == ["tag1", "tag2", "tag3"]

    async def test_remove_file_tag(self, tag_manager, test_files):
        """Test removing a tag from a file."""
        file_path = test_files["file1"]

        # Add tag
        tag_id = await tag_manager.create_tag("test", "Test tag")
        await tag_manager.add_file_tag(file_path, tag_id=tag_id)

        # Remove tag
        removed = await tag_manager.remove_file_tag(file_path, tag_id)
        assert removed is True

        # Check tags
        tags = await tag_manager.get_file_tags(file_path)
        assert len(tags) == 0

    async def test_get_files_by_tag(self, tag_manager, test_files):
        """Test getting files by tag."""
        tag_id = await tag_manager.create_tag("test", "Test tag")

        await tag_manager.add_file_tag(test_files["file1"], tag_id=tag_id)
        await tag_manager.add_file_tag(test_files["file2"], tag_id=tag_id)

        files = await tag_manager.get_files_by_tag(tag_id=tag_id)
        assert len(files) == 2
        assert str(test_files["file1"].resolve()) in files
        assert str(test_files["file2"].resolve()) in files
        assert str(test_files["file3"].resolve()) not in files

        # Test by tag name
        files = await tag_manager.get_files_by_tag(tag_name="test")
        assert len(files) == 2

    async def test_get_files_by_tags(self, tag_manager, test_files):
        """Test getting files by multiple tags."""
        tag1_id = await tag_manager.create_tag("tag1", "Tag 1")
        tag2_id = await tag_manager.create_tag("tag2", "Tag 2")

        # Add tags to files
        await tag_manager.add_file_tag(test_files["file1"], tag_id=tag1_id)
        await tag_manager.add_file_tag(test_files["file1"], tag_id=tag2_id)
        await tag_manager.add_file_tag(test_files["file2"], tag_id=tag1_id)
        await tag_manager.add_file_tag(test_files["file3"], tag_id=tag2_id)

        # Test OR query
        files = await tag_manager.get_files_by_tags(
            [tag1_id, tag2_id], require_all=False
        )
        assert len(files) == 3

        # Test AND query
        files = await tag_manager.get_files_by_tags(
            [tag1_id, tag2_id], require_all=True
        )
        assert len(files) == 1
        assert str(test_files["file1"].resolve()) in files

    async def test_get_tag_counts(self, tag_manager, test_files):
        """Test getting tag usage counts."""
        tag1_id = await tag_manager.create_tag("tag1", "Tag 1")
        tag2_id = await tag_manager.create_tag("tag2", "Tag 2")

        await tag_manager.add_file_tag(test_files["file1"], tag_id=tag1_id)
        await tag_manager.add_file_tag(test_files["file2"], tag_id=tag1_id)
        await tag_manager.add_file_tag(test_files["file3"], tag_id=tag2_id)

        counts = await tag_manager.get_tag_counts()
        assert len(counts) == 2

        tag1_count = next(tag for tag in counts if tag["name"] == "tag1")
        tag2_count = next(tag for tag in counts if tag["name"] == "tag2")

        assert tag1_count["count"] == 2
        assert tag2_count["count"] == 1


class TestTagHierarchy:
    """Test the TagHierarchy class."""

    @pytest.fixture
    def db_conn(self):
        """Create a temporary database connection."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Create tables
        conn.executescript(
            """
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE tag_hierarchy (
                parent_id INTEGER NOT NULL,
                child_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES tags (id) ON DELETE CASCADE,
                FOREIGN KEY (child_id) REFERENCES tags (id) ON DELETE CASCADE,
                CHECK (parent_id != child_id)
            );
        """
        )

        yield conn

        conn.close()

    @pytest.fixture
    def hierarchy(self, db_conn):
        """Create a TagHierarchy instance with test data."""
        hierarchy = TagHierarchy(db_conn)

        # Add test tags
        db_conn.execute(
            "INSERT INTO tags (name, description) VALUES ('root', 'Root tag')"
        )
        db_conn.execute(
            "INSERT INTO tags (name, description) VALUES ('parent1', 'Parent 1')"
        )
        db_conn.execute(
            "INSERT INTO tags (name, description) VALUES ('parent2', 'Parent 2')"
        )
        db_conn.execute(
            "INSERT INTO tags (name, description) VALUES ('child1', 'Child 1')"
        )
        db_conn.execute(
            "INSERT INTO tags (name, description) VALUES ('child2', 'Child 2')"
        )
        db_conn.execute(
            "INSERT INTO tags (name, description) VALUES ('grandchild', 'Grandchild')"
        )
        db_conn.commit()

        # Set up hierarchy:
        # root -> parent1 -> child1 -> grandchild
        # root -> parent2 -> child2
        hierarchy.add_relationship(1, 2)  # root -> parent1
        hierarchy.add_relationship(1, 3)  # root -> parent2
        hierarchy.add_relationship(2, 4)  # parent1 -> child1
        hierarchy.add_relationship(3, 5)  # parent2 -> child2
        hierarchy.add_relationship(4, 6)  # child1 -> grandchild

        return hierarchy

    def test_add_relationship(self, db_conn):
        """Test adding a parent-child relationship."""
        hierarchy = TagHierarchy(db_conn)

        # Add test tags
        db_conn.execute("INSERT INTO tags (name) VALUES ('parent')")
        db_conn.execute("INSERT INTO tags (name) VALUES ('child')")
        db_conn.commit()

        added = hierarchy.add_relationship(1, 2)
        assert added is True

        # Check relationship
        cursor = db_conn.execute(
            "SELECT * FROM tag_hierarchy WHERE parent_id = 1 AND child_id = 2"
        )
        assert cursor.fetchone() is not None

        # Test add again (should fail)
        added = hierarchy.add_relationship(1, 2)
        assert added is False

        # Test adding cycle (should fail)
        added = hierarchy.add_relationship(2, 1)
        assert added is False

    def test_remove_relationship(self, hierarchy, db_conn):
        """Test removing a parent-child relationship."""
        removed = hierarchy.remove_relationship(1, 2)  # root -> parent1
        assert removed is True

        # Check relationship
        cursor = db_conn.execute(
            "SELECT * FROM tag_hierarchy WHERE parent_id = 1 AND child_id = 2"
        )
        assert cursor.fetchone() is None

        # Test remove non-existent relationship
        removed = hierarchy.remove_relationship(
            1, 6
        )  # root -> grandchild (doesn't exist)
        assert removed is False

    def test_get_parents(self, hierarchy):
        """Test getting parent tags."""
        # child1 has parent1 as parent
        parents = hierarchy.get_parents(4)  # child1
        assert len(parents) == 1
        assert parents[0]["name"] == "parent1"

        # root has no parents
        parents = hierarchy.get_parents(1)  # root
        assert len(parents) == 0

    def test_get_children(self, hierarchy):
        """Test getting child tags."""
        # root has parent1 and parent2 as children
        children = hierarchy.get_children(1)  # root
        assert len(children) == 2
        assert sorted([child["name"] for child in children]) == ["parent1", "parent2"]

        # grandchild has no children
        children = hierarchy.get_children(6)  # grandchild
        assert len(children) == 0

    def test_get_ancestors(self, hierarchy):
        """Test getting ancestor tags."""
        # grandchild has child1, parent1, root as ancestors
        ancestors = hierarchy.get_ancestors(6)  # grandchild
        assert len(ancestors) == 3
        assert sorted([a["name"] for a in ancestors]) == ["child1", "parent1", "root"]

        # root has no ancestors
        ancestors = hierarchy.get_ancestors(1)  # root
        assert len(ancestors) == 0

    def test_get_descendants(self, hierarchy):
        """Test getting descendant tags."""
        # root has all other tags as descendants
        descendants = hierarchy.get_descendants(1)  # root
        assert len(descendants) == 5
        assert sorted([d["name"] for d in descendants]) == [
            "child1",
            "child2",
            "grandchild",
            "parent1",
            "parent2",
        ]

        # grandchild has no descendants
        descendants = hierarchy.get_descendants(6)  # grandchild
        assert len(descendants) == 0

    def test_is_ancestor(self, hierarchy):
        """Test checking if a tag is an ancestor."""
        # root is ancestor of grandchild
        assert hierarchy.is_ancestor(1, 6) is True  # root -> grandchild

        # grandchild is not ancestor of root
        assert hierarchy.is_ancestor(6, 1) is False  # grandchild -> root

        # parent1 is not ancestor of parent2
        assert hierarchy.is_ancestor(2, 3) is False  # parent1 -> parent2

    def test_is_related(self, hierarchy):
        """Test checking if tags are related."""
        # child1 and child2 are related (common ancestor: root)
        assert hierarchy.is_related(4, 5) is True  # child1 <-> child2

        # parent1 and child1 are related (parent-child)
        assert hierarchy.is_related(2, 4) is True  # parent1 <-> child1

        # All tags are related to root
        assert hierarchy.is_related(1, 6) is True  # root <-> grandchild

    def test_get_path(self, hierarchy):
        """Test getting the path from root to a tag."""
        # Path from root to grandchild
        path = hierarchy.get_path(6)  # grandchild
        assert len(path) == 4
        assert [tag["name"] for tag in path] == [
            "root",
            "parent1",
            "child1",
            "grandchild",
        ]

        # Path from root to parent2
        path = hierarchy.get_path(3)  # parent2
        assert len(path) == 2
        assert [tag["name"] for tag in path] == ["root", "parent2"]

    def test_export_taxonomy(self, hierarchy):
        """Test exporting the tag hierarchy as a nested dictionary."""
        # Export from root
        taxonomy = hierarchy.export_taxonomy(1)  # root
        assert "id" in taxonomy
        assert "children" in taxonomy
        assert len(taxonomy["children"]) == 2
        assert "parent1" in taxonomy["children"]
        assert "parent2" in taxonomy["children"]

        # Check nested structure
        parent1 = taxonomy["children"]["parent1"]
        assert "children" in parent1
        assert "child1" in parent1["children"]

        child1 = parent1["children"]["child1"]
        assert "children" in child1
        assert "grandchild" in child1["children"]


@pytest.mark.asyncio
async def test_integration():
    """Integration test for the tagging system."""
    # Create temporary database and files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = Path(f.name)

    temp_dir = tempfile.mkdtemp()
    file1 = Path(temp_dir) / "document.txt"
    file2 = Path(temp_dir) / "image.jpg"
    file3 = Path(temp_dir) / "code.py"

    file1.write_text("This is a sample document.")
    file2.write_text("This is not really an image, just a test file.")
    file3.write_text(
        "def sample_function():\n    return 'This is a sample Python function.'"
    )

    try:
        # Initialize tag manager
        async with TagManager(db_path) as tag_manager:
            await tag_manager.initialize()

            # Get database connection for tag hierarchy
            conn = tag_manager.schema.get_connection()
            tag_hierarchy = TagHierarchy(conn)

            # Create some tags with hierarchy
            document_id = await tag_manager.create_tag("document", "Document files")
            text_id = await tag_manager.create_tag("text", "Text files")
            code_id = await tag_manager.create_tag("code", "Code files")
            python_id = await tag_manager.create_tag("python", "Python files")
            image_id = await tag_manager.create_tag("image", "Image files")

            # Create hierarchy
            tag_hierarchy.add_relationship(text_id, document_id)  # text -> document
            tag_hierarchy.add_relationship(text_id, code_id)  # text -> code
            tag_hierarchy.add_relationship(code_id, python_id)  # code -> python

            # Tag files
            await tag_manager.add_file_tag(file1, tag_id=document_id)
            await tag_manager.add_file_tag(file2, tag_id=image_id)
            await tag_manager.add_file_tag(file3, tag_id=python_id)

            # Add some additional tags
            await tag_manager.add_file_tag(file1, tag_name="sample")
            await tag_manager.add_file_tag(file2, tag_name="sample")
            await tag_manager.add_file_tag(file3, tag_name="sample")
            await tag_manager.add_file_tag(file3, tag_name="function")

            # Test queries

            # Get files with tag 'sample'
            sample_tag = await tag_manager.get_tag_by_name("sample")
            files = await tag_manager.get_files_by_tag(tag_id=sample_tag["id"])
            assert len(files) == 3

            # Get files with tag 'python'
            files = await tag_manager.get_files_by_tag(tag_name="python")
            assert len(files) == 1
            assert str(file3.resolve()) in files

            # Get files with tags 'python' AND 'sample'
            python_tag = await tag_manager.get_tag_by_name("python")
            files = await tag_manager.get_files_by_tags(
                [python_tag["id"], sample_tag["id"]], require_all=True
            )
            assert len(files) == 1
            assert str(file3.resolve()) in files

            # Get tag counts
            counts = await tag_manager.get_tag_counts()
            assert (
                len(counts) == 6
            )  # document, text, code, python, image, sample, function

            sample_count = next(tag for tag in counts if tag["name"] == "sample")
            assert sample_count["count"] == 3

            # Test hierarchy queries

            # Get descendants of 'text'
            text_descendants = hierarchy.get_descendants(text_id)
            assert len(text_descendants) == 3
            assert sorted([tag["name"] for tag in text_descendants]) == [
                "code",
                "document",
                "python",
            ]

            # Export taxonomy
            taxonomy = hierarchy.export_taxonomy()
            assert "text" in taxonomy
            assert "image" in taxonomy

            text_taxonomy = taxonomy["text"]
            assert "children" in text_taxonomy
            assert "document" in text_taxonomy["children"]
            assert "code" in text_taxonomy["children"]

            code_taxonomy = text_taxonomy["children"]["code"]
            assert "children" in code_taxonomy
            assert "python" in code_taxonomy["children"]

    finally:
        # Cleanup
        if db_path.exists():
            os.unlink(db_path)
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main(["-v", "test_tagging.py"])
