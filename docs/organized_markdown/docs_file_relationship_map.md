# File Relationship Mapping

## Overview

The File Relationship Mapping module enables users to discover, visualize, and leverage relationships between files in their system. It provides tools for automatically detecting, storing, retrieving, and visualizing various types of relationships between files.

## Components

### 1. Relationship Class (relationship.py)

- Core data structure representing file relationships
- Features:
  - Strong typing with RelationshipType enum
  - Relationship strength scoring (0.0-1.0)
  - Rich metadata support
  - Serialization to/from dictionaries
  - Unique ID generation
  - Timestamp tracking
- Example usage:
  ```python
  from backend.src.relationships import Relationship, RelationshipType
  from pathlib import Path

  # Create a relationship
  rel = Relationship(
      source_path=Path("file1.py"),
      target_path=Path("file2.py"),
      rel_type=RelationshipType.IMPORTS,
      strength=0.8,
      metadata={"location": "line 10", "import_type": "direct"}
  )

  # Update relationship
  rel.update(strength=0.9, metadata={"additional_info": "value"})

  # Convert to dictionary for storage
  rel_dict = rel.to_dict()
  ```

### 2. Relationship Types (relationship.py)

- Comprehensive enum of relationship categories:
  - **Reference Relationships**: IMPORTS, REFERENCES, LINKS_TO
  - **Content Relationships**: SIMILAR_CONTENT, SHARED_KEYWORDS
  - **Structural Relationships**: PARENT_CHILD, SIBLING
  - **Temporal Relationships**: MODIFIED_TOGETHER, CREATED_TOGETHER
  - **Derived Relationships**: COMPILED_FROM, EXTRACTED_FROM
  - **Custom Relationships**: CUSTOM (user-defined)

### 3. Relationship Detector (detector.py)

- Engine for identifying relationships between files
- Features:
  - Composite pattern with specialized detectors
  - Async detection methods
  - Configurable detection settings
  - Batch processing support
  - Progress tracking
- Example usage:
  ```python
  from backend.src.relationships import RelationshipDetector

  # Create detector
  detector = RelationshipDetector()

  # Detect relationships for a single file
  relationships = await detector.detect_relationships(file_path)

  # Detect relationships for multiple files
  all_relationships = await detector.detect_batch(file_paths)
  ```

### 4. Relationship Store (store.py)

- Database for managing file relationships
- Features:
  - SQLite-based persistent storage
  - Asynchronous operations
  - Indexing for fast queries
  - Advanced filtering capabilities
  - Relationship CRUD operations
  - Batch operations for performance
- Example usage:
  ```python
  from backend.src.relationships import RelationshipStore

  # Initialize store
  store = RelationshipStore()

  # Add relationship
  await store.add(relationship)

  # Query by source file
  rels = await store.find_by_source(source_path)

  # Query by relationship type
  imports = await store.find_by_type(RelationshipType.IMPORTS)

  # Get all related files
  related = await store.get_related_files(file_path)
  ```

### 5. Relationship Graph (graph.py)

- Network graph representation of file relationships
- Features:
  - Directed graph structure
  - Edge weighting by relationship strength
  - Path finding algorithms
  - Centrality metrics
  - Community detection
  - Visualization preparation
- Example usage:
  ```python
  from backend.src.relationships import RelationshipGraph

  # Create graph from store
  graph = await RelationshipGraph.from_store(store)

  # Find shortest path between files
  path = graph.find_path(file1, file2)

  # Get central files
  central_files = graph.get_central_nodes(top_n=10)

  # Find communities
  communities = graph.detect_communities()

  # Get visualization data
  viz_data = graph.get_visualization_data()
  ```

### 6. Specialized Detectors (detectors/)

- Collection of specialized detection algorithms:
  - Import/reference detector for code files
  - Content similarity detector
  - Directory structure detector
  - Temporal relationship detector
  - Link detector for documents
  - Compilation relationship detector
- Each detector focuses on specific relationship types and file formats

## Implementation Details

### Relationship Data Structure

```python
class Relationship:
    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: RelationshipType,
        strength: float = 1.0,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        id: str | None = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.source_path = source_path
        self.target_path = target_path
        self.rel_type = rel_type
        self.strength = strength
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = self.created_at
```

### Relationship Store Schema

```sql
CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    target_path TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    strength REAL NOT NULL,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_path ON relationships(source_path);
CREATE INDEX IF NOT EXISTS idx_target_path ON relationships(target_path);
CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(rel_type);
```

### Graph Implementation

```python
class RelationshipGraph:
    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph for relationships

    async def build_from_store(self, store: RelationshipStore):
        """Build the graph from relationships in the store"""
        relationships = await store.get_all()
        for rel in relationships:
            self.add_relationship(rel)

    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph"""
        self.graph.add_edge(
            str(relationship.source_path),
            str(relationship.target_path),
            type=relationship.rel_type.name,
            strength=relationship.strength,
            metadata=relationship.metadata,
            id=relationship.id
        )
```

## Integration Points

### Internal Dependencies

- File Manager package for file operations
- Project Reader for code analysis
- Search package for relationship-based search
- Metadata package for file metadata

### External Dependencies

- SQLite for relationship storage
- NetworkX for graph operations
- Matplotlib for visualization (optional)
- scikit-learn for similarity calculations

## Usage Examples

### Finding Related Files

```python
# Find all files that import a specific module
related_files = await store.find_by_target(
    target_path=Path("my_module.py"),
    rel_type=RelationshipType.IMPORTS
)

# Find files with similar content
similar_files = await store.find_by_source(
    source_path=Path("document.md"),
    rel_type=RelationshipType.SIMILAR_CONTENT
)
```

### Analyzing Relationship Networks

```python
# Build relationship graph
graph = RelationshipGraph()
await graph.build_from_store(store)

# Find central files (most connected)
central_files = graph.get_central_nodes(metric="degree", top_n=5)

# Detect communities of related files
communities = graph.detect_communities()

# Find shortest path between files
path = graph.find_path(
    Path("source.py"),
    Path("target.py")
)
```

## Future Improvements

### Short-term

1. Enhanced detection algorithms for specific file types
2. Performance optimizations for large codebases
3. Additional relationship types
4. Interactive visualization improvements
5. Integration with version control systems

### Long-term

1. Machine learning for relationship prediction
2. Natural language understanding for content relationships
3. IDE plugin integration
4. Collaborative relationship annotation
5. API for third-party integrations