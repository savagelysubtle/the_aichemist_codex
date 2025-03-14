# Implementation Plan: Smart File Organization

## Overview

The Smart File Organization phase builds upon our recently completed metadata extraction capabilities to create more intelligent systems for organizing, tagging, and visualizing relationships between files. This plan outlines the architecture, components, and implementation steps for two key features:

1. **Intelligent Auto-Tagging**: Advanced NLP-based file classification and hierarchical tagging
2. **File Relationship Mapping**: Dynamic identification and visualization of file relationships

## 1. Intelligent Auto-Tagging

### Architecture

The Intelligent Auto-Tagging system will consist of the following components:

1. **TagClassifier**: Machine learning classifier for automatic tag assignment
2. **TagHierarchy**: System for managing hierarchical tag taxonomies
3. **TagSuggester**: Engine for suggesting relevant tags based on content and context
4. **TagManager**: Central component for managing the tag lifecycle

### Components

#### 1.1 TagClassifier

The `TagClassifier` will use machine learning to automatically classify files and assign appropriate tags. It will:

- Use pre-trained models for common document types
- Support custom training for domain-specific tagging
- Leverage our existing metadata extraction for feature generation

```python
class TagClassifier:
    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the tag classifier with optional pre-trained model."""
        # Load pre-trained model or initialize a new one

    async def classify(self, file_metadata: FileMetadata) -> List[str]:
        """Classify a file and return appropriate tags."""
        # Extract features from metadata
        # Apply classification model
        # Return predicted tags

    async def train(self, labeled_files: Dict[Path, List[str]]) -> None:
        """Train the classifier with labeled examples."""
        # Extract features from files
        # Train classification model
        # Save trained model
```

#### 1.2 TagHierarchy

The `TagHierarchy` will manage hierarchical relationships between tags, allowing for more sophisticated organization:

```python
class TagHierarchy:
    def __init__(self, taxonomy_path: Optional[Path] = None):
        """Initialize the tag hierarchy with optional taxonomy file."""
        # Load existing taxonomy or create empty one

    def add_tag(self, tag: str, parent_tag: Optional[str] = None) -> None:
        """Add a tag to the hierarchy with optional parent."""

    def get_children(self, tag: str) -> List[str]:
        """Get all direct child tags of a given tag."""

    def get_ancestors(self, tag: str) -> List[str]:
        """Get all ancestor tags of a given tag."""

    def is_related(self, tag1: str, tag2: str) -> bool:
        """Check if two tags are related in the hierarchy."""

    def save(self, path: Path) -> None:
        """Save the hierarchy to a file."""
```

#### 1.3 TagSuggester

The `TagSuggester` will recommend relevant tags based on file content, context, and user behavior:

```python
class TagSuggester:
    def __init__(self, classifier: TagClassifier, hierarchy: TagHierarchy):
        """Initialize the tag suggester with classifier and hierarchy."""

    async def suggest_tags(self, file_metadata: FileMetadata,
                           context_files: Optional[List[Path]] = None,
                           max_suggestions: int = 10) -> List[Tuple[str, float]]:
        """Suggest tags with confidence scores."""
        # Get base suggestions from classifier
        # Consider context files if provided
        # Apply tag hierarchy rules
        # Return suggestions with confidence scores

    def validate_tag(self, tag: str, file_metadata: FileMetadata) -> float:
        """Validate a tag for a file and return confidence score."""
```

#### 1.4 TagManager

The `TagManager` will serve as the central component for managing the tag lifecycle:

```python
class TagManager:
    def __init__(self, db_path: Path):
        """Initialize the tag manager with database path."""
        # Connect to SQLite database for tag storage

    async def get_tags(self, file_path: Path) -> List[str]:
        """Get all tags for a file."""

    async def add_tag(self, file_path: Path, tag: str, source: str = "manual") -> None:
        """Add a tag to a file with source information."""

    async def remove_tag(self, file_path: Path, tag: str) -> None:
        """Remove a tag from a file."""

    async def get_files_by_tag(self, tag: str) -> List[Path]:
        """Get all files with a specific tag."""

    async def merge_tags(self, source_tag: str, target_tag: str) -> None:
        """Merge two tags, replacing all instances of source with target."""

    async def get_popular_tags(self, limit: int = 20) -> List[Tuple[str, int]]:
        """Get most popular tags with usage count."""
```

### Implementation Steps

1. Create the database schema for tag storage
   - Tags table (id, name, description, created_at)
   - TagHierarchy table (parent_id, child_id)
   - FileTags table (file_path, tag_id, source, confidence, added_at)

2. Implement the TagManager with basic CRUD operations
   - SQLite integration with async support
   - Basic tag operations (add, remove, query)
   - Tag statistics and analytics

3. Implement the TagHierarchy for managing tag relationships
   - In-memory hierarchy representation
   - Persistence to/from database
   - Relationship query operations

4. Create the TagClassifier for automatic classification
   - Feature extraction pipeline from existing metadata
   - Integration with scikit-learn for classification
   - Model training and persistence

5. Build the TagSuggester for tag recommendations
   - Combine classifier predictions and hierarchy
   - Context-aware suggestions
   - Confidence scoring

6. Integrate with CLI for tag management
   - Add commands for tag CRUD operations
   - Add commands for tag hierarchy management
   - Add commands for tag suggestions

7. Develop automated tagging pipeline
   - Integrate with file processing workflow
   - Schedule periodic re-tagging
   - Add manual tag correction feedback loop

## 2. File Relationship Mapping

### Architecture

The File Relationship Mapping system will consist of:

1. **RelationshipDetector**: Engine for identifying relationships between files
2. **RelationshipStore**: Database for storing and querying relationships
3. **RelationshipGraph**: Graph-based representation of file relationships
4. **RelationshipVisualizer**: Tools for visualizing file relationships

### Components

#### 2.1 RelationshipDetector

The `RelationshipDetector` will identify relationships between files using various strategies:

```python
class RelationshipDetector:
    def __init__(self):
        """Initialize the relationship detector."""
        # Register detection strategies

    async def detect_relationships(self, file_path: Path,
                                  context_paths: Optional[List[Path]] = None) -> List[Relationship]:
        """Detect relationships for a file."""
        # Apply each detection strategy
        # Score and filter relationships
        # Return list of relationships

    async def detect_batch_relationships(self, file_paths: List[Path]) -> Dict[Path, List[Relationship]]:
        """Detect relationships for multiple files efficiently."""

class Relationship:
    """Represents a relationship between files."""
    def __init__(self, source: Path, target: Path,
                 relationship_type: str, confidence: float,
                 metadata: Optional[Dict] = None):
        self.source = source
        self.target = target
        self.relationship_type = relationship_type
        self.confidence = confidence
        self.metadata = metadata or {}
```

#### 2.2 RelationshipStore

The `RelationshipStore` will manage persistence of file relationships:

```python
class RelationshipStore:
    def __init__(self, db_path: Path):
        """Initialize the relationship store with database path."""
        # Connect to SQLite database

    async def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the store."""

    async def get_relationships(self, file_path: Path,
                               relationship_type: Optional[str] = None) -> List[Relationship]:
        """Get relationships for a file with optional type filter."""

    async def remove_relationship(self, source: Path, target: Path,
                                 relationship_type: Optional[str] = None) -> None:
        """Remove a relationship from the store."""

    async def get_related_files(self, file_path: Path,
                               max_depth: int = 2) -> Dict[Path, List[Relationship]]:
        """Get related files up to a specified depth."""
```

#### 2.3 RelationshipGraph

The `RelationshipGraph` will provide a graph-based API for querying and analyzing relationships:

```python
class RelationshipGraph:
    def __init__(self, relationship_store: RelationshipStore):
        """Initialize the relationship graph with a store."""

    async def build_graph(self, root_files: List[Path],
                         max_depth: int = 2) -> 'Graph':
        """Build a graph starting from root files."""

    async def find_paths(self, source: Path, target: Path,
                        max_depth: int = 3) -> List[List[Relationship]]:
        """Find all paths between two files."""

    async def compute_centrality(self, files: List[Path]) -> Dict[Path, float]:
        """Compute centrality metrics for files in the graph."""

    async def find_clusters(self) -> List[List[Path]]:
        """Find clusters of related files."""
```

#### 2.4 RelationshipVisualizer

The `RelationshipVisualizer` will generate visual representations of file relationships:

```python
class RelationshipVisualizer:
    def __init__(self, graph: RelationshipGraph):
        """Initialize the visualizer with a relationship graph."""

    async def generate_graph_json(self, root_files: List[Path],
                                 max_depth: int = 2) -> Dict:
        """Generate a JSON representation of the graph for visualization."""

    async def export_graphviz(self, root_files: List[Path],
                             output_path: Path,
                             max_depth: int = 2) -> None:
        """Export the graph in Graphviz DOT format."""

    async def export_html(self, root_files: List[Path],
                         output_path: Path,
                         max_depth: int = 2) -> None:
        """Export an interactive HTML visualization."""
```

### Implementation Steps

1. Create the database schema for relationship storage
   - Relationships table (source_path, target_path, relationship_type, confidence, metadata)
   - RelationshipTypes table (type_id, name, description)

2. Implement common relationship detection strategies
   - Content similarity based on our existing vector embeddings
   - Reference detection (imports, includes, links)
   - Name pattern matching (e.g., file_test.py → file.py)
   - Temporal relationships (modified around same time)
   - Structural relationships (same directory, parent/child directories)

3. Build the RelationshipDetector with pluggable strategies
   - Strategy registration system
   - Composite scoring mechanism
   - Batch processing optimization

4. Implement the RelationshipStore for persistence
   - SQLite integration with async support
   - Efficient query operations
   - Relationship metadata storage

5. Develop the RelationshipGraph for analysis
   - NetworkX integration for graph algorithms
   - Path finding and traversal
   - Centrality and clustering

6. Create the RelationshipVisualizer for visualization
   - JSON export for web visualization
   - Graphviz export for DOT format
   - D3.js based HTML visualization

7. Integrate with CLI for relationship management
   - Add commands for relationship detection
   - Add commands for relationship queries
   - Add commands for visualization export

## Integration Plan

### Combining Auto-Tagging and Relationship Mapping

To maximize the value of both features, we'll implement integrations between them:

1. Use relationships to improve tag suggestions
   - Suggest tags based on related files
   - Consider relationship types in suggestion ranking

2. Use tags to improve relationship detection
   - Consider common tags as signals for relationships
   - Use tag hierarchies to infer relationship types

3. Create a unified API for organization-related operations
   - Combined queries for tags and relationships
   - Joint visualization of tags and relationships

### Integration with Existing Components

1. Metadata Extraction
   - Use extracted metadata for feature generation in TagClassifier
   - Extract references and links for RelationshipDetector

2. Search Engine
   - Add tag-based filtering to search queries
   - Enable relationship-based search (e.g., "find all files related to X")

3. File Reader
   - Augment FileMetadata with tag and relationship information
   - Add relationship detection to file processing pipeline

## Timeline and Milestones

### Week 1: Core Infrastructure

- Tag database schema and storage
- Relationship database schema and storage
- Basic CLI commands for both systems

### Week 2: Intelligent Auto-Tagging

- TagClassifier implementation
- TagHierarchy implementation
- Integration with metadata extraction

### Week 3: File Relationship Mapping

- Core relationship detection strategies
- RelationshipGraph implementation
- Basic visualization export

### Week 4: Integration and Refinement

- Combined tag and relationship operations
- Advanced visualization features
- Performance optimization and testing

## Testing Strategy

1. Unit tests for all components
   - Tag management operations
   - Relationship detection and storage
   - Graph algorithms

2. Integration tests
   - End-to-end tagging workflow
   - Relationship detection pipeline
   - Visualization export

3. Performance benchmarks
   - Measure tagging throughput
   - Benchmark relationship detection
   - Graph operation performance

## Documentation Plan

1. Architecture documentation
   - Component diagrams
   - Data flow descriptions
   - Database schema

2. User documentation
   - CLI command reference
   - Configuration options
   - Visualization guide

3. Developer documentation
   - API reference
   - Extension points
   - Example workflows
