"""Tests for the memory CLI commands."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from typer.testing import CliRunner

from the_aichemist_codex.domain.entities.memory import Memory, MemoryType
from the_aichemist_codex.interfaces.cli.cli import cli_app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for the database."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        yield db_path


@pytest.fixture
def mock_repository():
    """Create a mock SQLiteMemoryRepository."""
    repo = AsyncMock()
    repo.initialize = AsyncMock()
    return repo


@pytest.fixture
def repository_patch(mock_repository):
    """Patch the SQLiteMemoryRepository."""
    with patch(
        "the_aichemist_codex.interfaces.cli.commands.memory.SQLiteMemoryRepository"
    ) as mock_repo_class:
        mock_repo_class.return_value = mock_repository
        yield mock_repository


def test_create_memory_command(runner, repository_patch):
    """Test creating a memory through the CLI."""
    # Arrange
    test_uuid = UUID("11111111-1111-1111-1111-111111111111")
    test_memory = Memory(
        id=test_uuid,
        content="Test memory content",
        type=MemoryType.CONCEPT,
        tags={"test", "memory"},
    )

    # Mock save_memory to return the test_memory
    async def mock_save_memory(memory):
        memory.id = test_uuid
        return memory

    repository_patch.save_memory.side_effect = mock_save_memory

    # Act
    result = runner.invoke(
        cli_app,
        [
            "memory",
            "create",
            "Test memory content",
            "--type",
            "concept",
            "--tag",
            "test",
            "--tag",
            "memory",
        ],
    )

    # Assert
    assert result.exit_code == 0
    assert "Memory created successfully" in result.stdout
    assert str(test_uuid) in result.stdout
    assert "Test memory content" in result.stdout
    assert "concept" in result.stdout.lower()
    repository_patch.save_memory.assert_called_once()


def test_list_memories_command(runner, repository_patch):
    """Test listing memories through the CLI."""
    # Arrange
    test_memories = [
        Memory(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            content="First test memory",
            type=MemoryType.CONCEPT,
            tags={"test", "memory", "first"},
        ),
        Memory(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            content="Second test memory",
            type=MemoryType.DOCUMENT,
            tags={"test", "memory", "second"},
        ),
    ]

    # Mock recall_memories to return test_memories
    repository_patch.recall_memories.return_value = asyncio.Future()
    repository_patch.recall_memories.return_value.set_result(test_memories)

    # Act
    result = runner.invoke(cli_app, ["memory", "list"])

    # Assert
    assert result.exit_code == 0
    assert "First test memory" in result.stdout
    assert "Second test memory" in result.stdout
    assert "CONCEPT" in result.stdout
    assert "DOCUMENT" in result.stdout
    repository_patch.recall_memories.assert_called_once()


def test_recall_memories_command(runner, repository_patch):
    """Test recalling memories through the CLI."""
    # Arrange
    test_memories = [
        Memory(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            content="Memory about Python programming",
            type=MemoryType.CONCEPT,
            tags={"python", "programming"},
        ),
    ]

    # Mock recall_memories and get_relevance_score
    repository_patch.recall_memories.return_value = asyncio.Future()
    repository_patch.recall_memories.return_value.set_result(test_memories)
    test_memories[0].get_relevance_score = MagicMock(return_value=0.85)

    # Act
    result = runner.invoke(cli_app, ["memory", "recall", "python programming"])

    # Assert
    assert result.exit_code == 0
    assert "Memory about Python programming" in result.stdout
    assert "0.85" in result.stdout
    assert "CONCEPT" in result.stdout
    repository_patch.recall_memories.assert_called_once()


def test_strengthen_memory_command(runner, repository_patch):
    """Test strengthening a memory through the CLI."""
    # Arrange
    test_id = "11111111-1111-1111-1111-111111111111"
    test_memory = Memory(
        id=UUID(test_id),
        content="Memory to strengthen",
        type=MemoryType.CONCEPT,
    )

    # Mock the repository methods
    repository_patch.get_memory.return_value = asyncio.Future()
    repository_patch.get_memory.return_value.set_result(test_memory)
    repository_patch.update_memory.return_value = asyncio.Future()
    repository_patch.update_memory.return_value.set_result(None)

    # Act
    result = runner.invoke(
        cli_app, ["memory", "strengthen", test_id, "--amount", "0.2"]
    )

    # Assert
    assert result.exit_code == 0
    assert "Memory strengthened" in result.stdout
    repository_patch.get_memory.assert_called_once()
    repository_patch.update_memory.assert_called_once()


def test_memory_graph_command(runner, repository_patch):
    """Test showing a memory graph through the CLI."""
    # Arrange
    test_id = "11111111-1111-1111-1111-111111111111"
    test_memory = Memory(
        id=UUID(test_id),
        content="Root memory for graph",
        type=MemoryType.CONCEPT,
    )

    # Mock the repository methods
    repository_patch.get_memory.return_value = asyncio.Future()
    repository_patch.get_memory.return_value.set_result(test_memory)
    repository_patch.find_associations.return_value = asyncio.Future()
    repository_patch.find_associations.return_value.set_result([])

    # Act
    result = runner.invoke(cli_app, ["memory", "graph", test_id])

    # Assert
    assert result.exit_code == 0
    assert "Memory Graph" in result.stdout
    repository_patch.get_memory.assert_called_once()
    repository_patch.find_associations.assert_called_once()
