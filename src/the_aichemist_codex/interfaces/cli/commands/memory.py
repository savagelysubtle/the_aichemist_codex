"""
Memory CLI Commands

This module is part of the interfaces layer of the AIchemist Codex.
Location: src/the_aichemist_codex/interfaces/cli/commands/memory.py

Implements CLI commands for interacting with the memory system.
"""

import asyncio
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from the_aichemist_codex.domain.entities.memory import Memory, MemoryType
from the_aichemist_codex.domain.entities.memory_association import AssociationType
from the_aichemist_codex.domain.value_objects.recall_context import (
    RecallContext,
    RecallStrategy,
)
from the_aichemist_codex.infrastructure.repositories.sqlite_memory_repository import (
    SQLiteMemoryRepository,
)

console = Console()
memory_app = typer.Typer(help="Memory management commands")

# Global variables
repository: SQLiteMemoryRepository | None = None
db_path: Path = Path("memory.db")


class MemoryTypeOption(str, Enum):
    """Memory types available in the CLI."""

    DOCUMENT = "document"
    CONCEPT = "concept"
    RELATION = "relation"
    METADATA = "metadata"
    EVENT = "event"


def get_memory_type(type_str: str) -> MemoryType:
    """Convert string type to MemoryType enum."""
    return MemoryType[type_str.upper()]


def get_association_type(type_str: str) -> AssociationType:
    """Convert string type to AssociationType enum."""
    return AssociationType[type_str.upper()]


async def get_repository() -> SQLiteMemoryRepository:
    """Get or initialize the memory repository."""
    global repository
    if repository is None:
        repository = SQLiteMemoryRepository(db_path)
        await repository.initialize()
    return repository


@memory_app.command("create")
def create_memory(
    content: str = typer.Argument(..., help="Content of the memory"),
    memory_type: MemoryTypeOption = typer.Option(
        MemoryTypeOption.DOCUMENT, "--type", "-t", help="Type of memory"
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-g", help="Tags for the memory (can be used multiple times)"
    ),
    source_id: str | None = typer.Option(
        None, "--source", "-s", help="Optional source memory ID"
    ),
) -> None:
    """
    Create a new memory with content, type, and optional tags.

    Example:
        aichemist memory create "Important concept about clean architecture" --type concept --tag architecture --tag clean
    """

    async def _create_memory() -> None:
        try:
            # Create memory entity
            memory = Memory(
                content=content,
                type=get_memory_type(memory_type),
                tags=set(tags) if tags else set(),
                source_id=UUID(source_id) if source_id else None,
            )

            # Save to repository
            repo = await get_repository()
            await repo.save_memory(memory)

            # Display success message
            console.print(
                f"✅ [green]Memory created successfully with ID: {memory.id}[/green]"
            )

            # Display memory details
            table = Table(title="Memory Details")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("ID", str(memory.id))
            table.add_row("Type", memory_type)
            table.add_row(
                "Content", content[:100] + "..." if len(content) > 100 else content
            )
            table.add_row("Created", str(memory.created_at))
            table.add_row("Tags", ", ".join(memory.tags) if memory.tags else "None")
            table.add_row("Source", source_id if source_id else "None")
            table.add_row("Strength", f"{memory.strength.current_value:.2f}")

            console.print(table)

        except Exception as e:
            console.print(f"❌ [red]Error creating memory: {str(e)}[/red]")

    asyncio.run(_create_memory())


@memory_app.command("list")
def list_memories(
    memory_type: MemoryTypeOption | None = typer.Option(
        None, "--type", "-t", help="Filter by memory type"
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-g", help="Filter by tags (can be used multiple times)"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of memories to list"
    ),
) -> None:
    """
    List existing memories with optional filtering by type and tags.

    Example:
        aichemist memory list --type concept --tag architecture --limit 20
    """

    async def _list_memories() -> None:
        try:
            repo = await get_repository()
            memories: list[Memory] = []

            # Fetch memories based on filters
            if memory_type:
                memories = await repo.find_by_type(get_memory_type(memory_type))
            elif tags:
                memories = await repo.find_by_tags(set(tags))
            else:
                # Create a context to retrieve recent memories
                context = RecallContext(
                    query="",  # Empty query to match all
                    strategy=RecallStrategy.MOST_RECENT,
                    max_results=limit,
                )
                memories = await repo.recall_memories(context)

            # Filter by tags if both type and tags are provided
            if memory_type and tags:
                memories = [m for m in memories if any(tag in m.tags for tag in tags)]

            # Limit results
            memories = memories[:limit]

            if not memories:
                console.print(
                    "[yellow]No memories found matching the criteria[/yellow]"
                )
                return

            # Display results
            table = Table(title=f"Memories ({len(memories)} results)")
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Content", style="white")
            table.add_column("Created", style="blue")
            table.add_column("Tags", style="yellow")
            table.add_column("Strength", style="magenta")

            for memory in memories:
                table.add_row(
                    str(memory.id),
                    memory.type.name,
                    memory.content[:50] + "..."
                    if len(memory.content) > 50
                    else memory.content,
                    memory.created_at.strftime("%Y-%m-%d %H:%M"),
                    ", ".join(memory.tags) if memory.tags else "-",
                    f"{memory.strength.current_value:.2f}",
                )

            console.print(table)

        except Exception as e:
            console.print(f"❌ [red]Error listing memories: {str(e)}[/red]")

    asyncio.run(_list_memories())


@memory_app.command("recall")
def recall_memories(
    query: str = typer.Argument(..., help="Search query for memories"),
    strategy: str = typer.Option(
        "relevant",
        "--strategy",
        "-s",
        help="Recall strategy (relevant, recent, strongest, associative)",
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-g", help="Filter by tags (can be used multiple times)"
    ),
    memory_type: MemoryTypeOption | None = typer.Option(
        None, "--type", "-t", help="Filter by memory type"
    ),
    min_relevance: float = typer.Option(
        0.2, "--min-relevance", "-r", help="Minimum relevance score"
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
) -> None:
    """
    Recall memories based on a query and optional filters.

    Example:
        aichemist memory recall "architecture patterns" --strategy relevant --tag design --min-relevance 0.3
    """

    async def _recall_memories() -> None:
        try:
            repo = await get_repository()

            # Map strategy string to enum
            strategy_map = {
                "relevant": RecallStrategy.MOST_RELEVANT,
                "recent": RecallStrategy.MOST_RECENT,
                "strongest": RecallStrategy.STRONGEST,
                "associative": RecallStrategy.ASSOCIATIVE,
            }

            recall_strategy = strategy_map.get(
                strategy.lower(), RecallStrategy.MOST_RELEVANT
            )

            # Create memory types set if provided
            memory_types = frozenset([memory_type.upper()]) if memory_type else None

            # Create recall context
            context = RecallContext(
                query=query,
                strategy=recall_strategy,
                tags=frozenset(tags) if tags else frozenset(),
                memory_types=memory_types,
                max_results=limit,
                min_relevance=min_relevance,
            )

            # Recall memories
            memories = await repo.recall_memories(context)

            if not memories:
                console.print("[yellow]No memories found matching the query[/yellow]")
                return

            # Display results
            table = Table(title=f"Recall Results: '{query}' ({len(memories)} results)")
            table.add_column("ID", style="cyan")
            table.add_column("Relevance", style="green")
            table.add_column("Content", style="white")
            table.add_column("Type", style="blue")
            table.add_column("Tags", style="yellow")

            for memory in memories:
                relevance = memory.get_relevance_score(
                    query, set(tags) if tags else None
                )
                table.add_row(
                    str(memory.id),
                    f"{relevance:.2f}",
                    memory.content[:75] + "..."
                    if len(memory.content) > 75
                    else memory.content,
                    memory.type.name,
                    ", ".join(memory.tags) if memory.tags else "-",
                )

            console.print(table)

        except Exception as e:
            console.print(f"❌ [red]Error recalling memories: {str(e)}[/red]")

    asyncio.run(_recall_memories())


@memory_app.command("strengthen")
def strengthen_memory(
    memory_id: str = typer.Argument(..., help="ID of the memory to strengthen"),
    amount: float = typer.Option(
        0.1, "--amount", "-a", help="Amount to strengthen (0.0-1.0)"
    ),
) -> None:
    """
    Strengthen a memory by a specified amount.

    Example:
        aichemist memory strengthen 123e4567-e89b-12d3-a456-426614174000 --amount 0.2
    """

    async def _strengthen_memory() -> None:
        try:
            repo = await get_repository()

            # Get the memory
            memory = await repo.get_memory(UUID(memory_id))

            if not memory:
                console.print(f"❌ [red]Memory with ID {memory_id} not found[/red]")
                return

            # Display the before state
            console.print(f"Before strengthening: {memory.strength.current_value:.2f}")

            # Strengthen the memory
            memory.strength.strengthen(amount)

            # Update in repository
            await repo.update_memory(memory)

            # Display the after state
            console.print(
                f"✅ [green]Memory strengthened to: {memory.strength.current_value:.2f}[/green]"
            )

        except Exception as e:
            console.print(f"❌ [red]Error strengthening memory: {str(e)}[/red]")

    asyncio.run(_strengthen_memory())


@memory_app.command("graph")
def show_memory_graph(
    memory_id: str | None = typer.Argument(
        None, help="Root memory ID to visualize (optional)"
    ),
    depth: int = typer.Option(2, "--depth", "-d", help="Depth of the graph to display"),
    min_strength: float = typer.Option(
        0.3, "--min-strength", "-s", help="Minimum association strength"
    ),
) -> None:
    """
    Visualize memory relationships as a tree.

    Example:
        aichemist memory graph 123e4567-e89b-12d3-a456-426614174000 --depth 3 --min-strength 0.5
    """

    async def _show_memory_graph() -> None:
        try:
            repo = await get_repository()

            # Get the root memory if provided, or find a recent one
            root_memory = None
            if memory_id:
                root_memory = await repo.get_memory(UUID(memory_id))
                if not root_memory:
                    console.print(f"❌ [red]Memory with ID {memory_id} not found[/red]")
                    return
            else:
                # Get a recent memory as the root
                context = RecallContext(
                    query="",  # Empty query to match all
                    strategy=RecallStrategy.MOST_RECENT,
                    max_results=1,
                )
                memories = await repo.recall_memories(context)
                if not memories:
                    console.print("[yellow]No memories found in the system[/yellow]")
                    return
                root_memory = memories[0]

            # Create the tree visualization
            tree = Tree(
                f"[bold cyan]{root_memory.id}[/bold cyan]: [white]{root_memory.content[:50]}...[/white]"
            )

            # Track visited memories to avoid cycles
            visited = {root_memory.id}

            # Build the tree recursively
            await _build_memory_tree(
                repo, tree, root_memory.id, visited, depth, min_strength, 1
            )

            # Display the tree
            console.print(
                Panel(
                    tree,
                    title=f"Memory Graph (Depth: {depth}, Min Strength: {min_strength})",
                )
            )

        except Exception as e:
            console.print(f"❌ [red]Error showing memory graph: {str(e)}[/red]")

    async def _build_memory_tree(
        repo: SQLiteMemoryRepository,
        parent_node: Tree,
        memory_id: UUID,
        visited: set[UUID],
        max_depth: int,
        min_strength: float,
        current_depth: int,
    ) -> None:
        """Recursively build the memory relationship tree."""
        if current_depth >= max_depth:
            return

        # Get associations for this memory
        associations = await repo.find_associations(memory_id)

        # Filter by minimum strength
        associations = [a for a in associations if a.strength >= min_strength]

        # Sort by strength (strongest first)
        associations.sort(key=lambda a: a.strength, reverse=True)

        for assoc in associations:
            # Determine the target memory ID
            target_id = (
                assoc.target_id if assoc.source_id == memory_id else assoc.source_id
            )

            # Skip if already visited to avoid cycles
            if target_id in visited:
                continue

            # Mark as visited
            visited.add(target_id)

            # Get the target memory
            target_memory = await repo.get_memory(target_id)
            if not target_memory:
                continue

            # Add to the tree
            assoc_label = f"[{assoc.association_type.name.lower()}] "
            target_node = parent_node.add(
                f"{assoc_label}[bold cyan]{target_memory.id}[/bold cyan] "
                f"({assoc.strength:.2f}): [white]{target_memory.content[:40]}...[/white]"
            )

            # Continue building the tree recursively
            await _build_memory_tree(
                repo,
                target_node,
                target_id,
                visited,
                max_depth,
                min_strength,
                current_depth + 1,
            )

    asyncio.run(_show_memory_graph())


def register_commands(app: typer.Typer, cli: Any) -> None:
    """Register memory commands with the CLI application."""
    app.add_typer(memory_app, name="memory", help="Memory management commands")

    # Set global database path based on CLI configuration
    global db_path
    if hasattr(cli, "config") and cli.config:
        config_memory_db = getattr(cli.config, "memory_db_path", None)
        if config_memory_db:
            db_path = Path(config_memory_db)

    console.print(f"Memory commands registered (DB: {db_path})")
