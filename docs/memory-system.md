# AIchemist Codex Memory System

The Memory System is a core component of the AIchemist Codex that enables the storage, retrieval, and management of information as memories. This system incorporates strength-based recall, association between memories, and metadata tracking to create a knowledge graph that can evolve over time.

## Memory System Design

The memory system is designed with clean architecture principles:

```
Domain Layer:
  - Memory entity
  - MemoryAssociation entity
  - MemoryStrength value object
  - RecallContext value object
  - MemoryRepositoryInterface

Infrastructure Layer:
  - SQLiteMemoryRepository implementation

Interface Layer:
  - CLI memory commands
```

### Memory Entities

A Memory represents a single unit of stored information. Each memory has:

- **Content**: The actual information stored in the memory
- **Type**: The kind of memory (DOCUMENT, CONCEPT, RELATION, METADATA, EVENT)
- **Tags**: A set of keywords that categorize the memory
- **Strength**: A value object that tracks the memory's strength and decay over time
- **Metadata**: Additional information about the memory
- **Created/Updated timestamps**: When the memory was created and last updated

### Memory Associations

Memories can be associated with each other through MemoryAssociation entities. Each association has:

- **Source and Target**: The two memories being associated
- **Association Type**: The kind of relationship between these memories
- **Strength**: The strength of the association
- **Directionality**: Whether the association is directional or bidirectional
- **Metadata**: Additional information about the association

### Recall Strategies

The memory system supports different recall strategies:

1. **Most Relevant**: Finds memories most semantically relevant to a query
2. **Most Recent**: Finds the most recently created/updated memories
3. **Strongest**: Finds memories with the highest strength values
4. **Associative**: Finds memories through their associations with other memories

### Memory Strength

Memory strength is a dynamic value that:

- Increases when a memory is accessed, strengthened, or found useful
- Gradually decays over time following forgetting curves
- Can be explicitly modified through CLI commands

## Using the Memory System CLI

The memory system can be accessed through the AIchemist CLI:

### Creating Memories

```bash
aichemist memory create "Important concept about clean architecture" --type concept --tag architecture --tag clean
```

### Listing Memories

```bash
# List all memories (most recent first)
aichemist memory list

# Filter by type
aichemist memory list --type concept

# Filter by tags
aichemist memory list --tag architecture --tag important
```

### Recalling Memories

```bash
# Search for memories relevant to a query
aichemist memory recall "clean architecture patterns"

# Use different recall strategies
aichemist memory recall "design patterns" --strategy strongest
aichemist memory recall "python" --strategy recent
aichemist memory recall "software design" --strategy associative --min-relevance 0.5
```

### Managing Memory Strength

```bash
# Strengthen a specific memory
aichemist memory strengthen 123e4567-e89b-12d3-a456-426614174000 --amount 0.2
```

### Visualizing the Memory Graph

```bash
# Show the memory graph starting from a specific memory
aichemist memory graph 123e4567-e89b-12d3-a456-426614174000 --depth 3

# Filter by minimum association strength
aichemist memory graph --min-strength 0.5
```

## Integration with Other Systems

The memory system is designed to integrate with other components of the AIchemist Codex:

- **Code Artifacts**: Code artifacts can be linked to memories to create a knowledge graph of your codebase
- **Analysis Tools**: Analysis results can be stored as memories for later retrieval
- **Content Extraction**: Information extracted from documentation can be stored as memories

## Implementation Details

### SQLite Repository

The memory system uses SQLite for persistent storage with:

- Asynchronous database operations
- Structured query for different recall strategies
- JSON serialization for complex attributes
- Atomic transactions for data consistency

### Efficient Recall

Memory recall is optimized using:

- Relevance scoring algorithms
- Tag-based filtering
- Memory type filtering
- Custom SQL queries per recall strategy

## Future Enhancements

Planned enhancements for the memory system include:

1. Vector embedding support for more sophisticated semantic matching
2. Enhanced forgetting curves with configurable parameters
3. Support for additional storage backends
4. Automatic association discovery based on content similarity
5. Advanced visualization tools for the memory graph
