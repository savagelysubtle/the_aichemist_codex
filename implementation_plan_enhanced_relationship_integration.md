# Enhanced Implementation Plan: File Relationship Mapping with Loose Coupling

This document outlines the enhanced implementation approach for the File Relationship Mapping feature, focusing on integration with existing systems while maintaining loose coupling principles.

## 1. Architecture Overview

### Core Design Principles

1. **Loose Coupling**: Components should interact through well-defined interfaces with minimal dependencies
2. **Open/Closed Principle**: Systems should be open for extension but closed for modification
3. **Interface Segregation**: Define focused interfaces that clients only need to know about
4. **Dependency Inversion**: Depend on abstractions, not concrete implementations

### System Architecture

The relationship mapping feature will follow a modular architecture:

```
                   ┌─────────────────┐
                   │  Configuration  │
                   └────────┬────────┘
                            │
                            ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Events   │◄────┤  Core Services  ├────►│    Adapters     │
└─────────────┘     └────────┬────────┘     └────────┬────────┘
                            │                        │
                            ▼                        ▼
                  ┌─────────────────┐      ┌─────────────────┐
                  │   Detectors     │      │ Existing Systems│
                  └─────────────────┘      └─────────────────┘
```

## 2. Interface-Based Design

### Abstract Base Classes and Interfaces

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

class IRelationshipDetector(ABC):
    """Interface for relationship detection components."""

    @abstractmethod
    async def detect_relationships(
        self,
        paths: List[Path],
        **options
    ) -> List["Relationship"]:
        """Detect relationships between files."""
        pass

class IRelationshipStore(ABC):
    """Interface for relationship storage components."""

    @abstractmethod
    async def add_relationship(self, relationship: "Relationship") -> None:
        """Add a relationship to the store."""
        pass

    @abstractmethod
    async def get_relationships_for_file(
        self,
        file_path: Path,
        **filters
    ) -> List["Relationship"]:
        """Get relationships for a specific file."""
        pass

class IRelationshipGraph(ABC):
    """Interface for relationship graph operations."""

    @abstractmethod
    async def build_graph(self, **options) -> Any:
        """Build a graph from relationships."""
        pass

    @abstractmethod
    async def find_paths(
        self,
        source_path: Path,
        target_path: Path,
        **options
    ) -> List[List[Path]]:
        """Find paths between files in the relationship graph."""
        pass
```

## 3. Factory Pattern Implementation

```python
class RelationshipComponentFactory:
    """Factory for creating relationship system components."""

    @classmethod
    def create_detector(cls, config: Dict[str, Any]) -> IRelationshipDetector:
        """Create a relationship detector based on configuration."""
        detector_type = config.get("relationships.detector.type", "default")

        if detector_type == "default":
            from backend.relationships.detector import RelationshipDetector
            detector = RelationshipDetector()

            # Register strategies based on configuration
            if config.get("relationships.detection.import_analysis.enabled", True):
                from backend.relationships.detectors.import_detector import ImportAnalysisDetector
                detector.register_detector(ImportAnalysisDetector(
                    Path(config.get("project.root", "."))
                ))

            if config.get("relationships.detection.content_similarity.enabled", True):
                from backend.relationships.detectors.similarity_detector import ContentSimilarityDetector
                detector.register_detector(ContentSimilarityDetector(
                    threshold=config.get("relationships.detection.content_similarity.threshold", 0.7)
                ))

            # Add more detectors based on configuration

            return detector

        # Support for custom detector implementations
        if detector_type == "custom" and "relationships.detector.custom_class" in config:
            import importlib
            module_name, class_name = config["relationships.detector.custom_class"].rsplit(".", 1)
            module = importlib.import_module(module_name)
            detector_class = getattr(module, class_name)
            return detector_class(config)

        raise ValueError(f"Unknown detector type: {detector_type}")
```

## 4. Event-Driven Integration

### Event System

```python
class RelationshipEvent:
    """Base class for relationship events."""
    pass

class RelationshipDetectedEvent(RelationshipEvent):
    """Event fired when relationships are detected."""

    def __init__(self, source_path: Path, relationships: List["Relationship"]):
        self.source_path = source_path
        self.relationships = relationships

class RelationshipChangedEvent(RelationshipEvent):
    """Event fired when relationships are changed."""

    def __init__(
        self,
        file_path: Path,
        added: List["Relationship"] = None,
        removed: List["Relationship"] = None,
        updated: List["Relationship"] = None
    ):
        self.file_path = file_path
        self.added = added or []
        self.removed = removed or []
        self.updated = updated or []

class EventBus:
    """Simple event bus for publishing and subscribing to events."""

    _subscribers = {}

    @classmethod
    def subscribe(cls, event_type: type, callback):
        """Subscribe to an event type."""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = set()
        cls._subscribers[event_type].add(callback)

    @classmethod
    def unsubscribe(cls, event_type: type, callback):
        """Unsubscribe from an event type."""
        if event_type in cls._subscribers:
            cls._subscribers[event_type].discard(callback)

    @classmethod
    def publish(cls, event):
        """Publish an event to all subscribers."""
        event_type = type(event)

        # Call specific subscribers
        if event_type in cls._subscribers:
            for callback in cls._subscribers[event_type]:
                callback(event)

        # Call any subscribers of parent event types
        for t in cls._subscribers:
            if event_type != t and issubclass(event_type, t):
                for callback in cls._subscribers[t]:
                    callback(event)
```

## 5. Integration with Existing Utils and Config

### Configuration System Integration

```python
# In config_schema.py

RELATIONSHIP_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "relationships": {
            "type": "object",
            "properties": {
                "detection": {
                    "type": "object",
                    "properties": {
                        "import_analysis": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "strength_weight": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        },
                        "content_similarity": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                                "strength_weight": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        },
                        "structure_based": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "strength_weight": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    }
                },
                "storage": {
                    "type": "object",
                    "properties": {
                        "db_location": {"type": "string"},
                        "cleanup_interval_days": {"type": "integer", "minimum": 1}
                    }
                },
                "visualization": {
                    "type": "object",
                    "properties": {
                        "default_format": {"type": "string", "enum": ["json", "dot"]},
                        "max_nodes": {"type": "integer", "minimum": 10},
                        "color_scheme": {"type": "string"}
                    }
                }
            }
        }
    }
}

# In config_defaults.py

DEFAULT_RELATIONSHIP_CONFIG = {
    "relationships": {
        "detection": {
            "import_analysis": {
                "enabled": True,
                "strength_weight": 0.9
            },
            "content_similarity": {
                "enabled": True,
                "threshold": 0.7,
                "strength_weight": 0.8
            },
            "structure_based": {
                "enabled": True,
                "strength_weight": 0.6
            }
        },
        "storage": {
            "db_location": ".relationships.db",
            "cleanup_interval_days": 30
        },
        "visualization": {
            "default_format": "json",
            "max_nodes": 100,
            "color_scheme": "relationship_type"
        }
    }
}
```

### Utils Extension

```python
# In utils/relationship_utils.py

from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import re

def normalize_path(path: Path) -> Path:
    """Normalize a path for cross-platform relationship handling."""
    return path.resolve().absolute()

def extract_import_statements(file_content: str, language: str) -> List[Dict[str, Any]]:
    """Extract import statements from file content."""
    imports = []

    if language == "python":
        # Match Python imports
        import_patterns = [
            r'^\s*import\s+([a-zA-Z0-9_.]+)',  # import module
            r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import'  # from module import
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, file_content, re.MULTILINE):
                imports.append({
                    "module": match.group(1),
                    "line": file_content.count('\n', 0, match.start()) + 1,
                    "type": "import"
                })

    elif language in ("javascript", "typescript"):
        # Match JS/TS imports
        import_patterns = [
            r'import\s+.*\s+from\s+[\'"]([^\'"]*)[\'"]',  # ES6 import
            r'require\s*\(\s*[\'"]([^\'"]*)[\'"]'  # CommonJS require
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, file_content, re.MULTILINE):
                imports.append({
                    "module": match.group(1),
                    "line": file_content.count('\n', 0, match.start()) + 1,
                    "type": "import"
                })

    return imports

def resolve_python_import(import_name: str, source_file: Path, workspace_root: Path) -> Optional[Path]:
    """Resolve a Python import to a file path."""
    # Handle relative imports
    if import_name.startswith('.'):
        # Count leading dots for relative import level
        level = 0
        while level < len(import_name) and import_name[level] == '.':
            level += 1

        # Get the source file's package path
        source_package = source_file.parent

        # Go up the directory tree based on the relative import level
        for _ in range(level - 1):
            source_package = source_package.parent

        # Handle the module part of the import
        module_path = import_name[level:].replace('.', '/')
        if module_path:
            potential_path = source_package / f"{module_path}.py"
            if potential_path.exists():
                return potential_path

            # Check for package (directory with __init__.py)
            package_path = source_package / module_path / "__init__.py"
            if package_path.exists():
                return package_path

        # Just the package with __init__.py
        else:
            init_path = source_package / "__init__.py"
            if init_path.exists():
                return init_path

    # Handle absolute imports
    else:
        # Try to find the module in the workspace
        module_path = import_name.replace('.', '/')

        # Check for direct .py file
        potential_path = workspace_root / f"{module_path}.py"
        if potential_path.exists():
            return potential_path

        # Check for package with __init__.py
        package_path = workspace_root / module_path / "__init__.py"
        if package_path.exists():
            return package_path

    return None
```

## 6. Service Locator Pattern

```python
class ServiceRegistry:
    """Registry for relationship services."""

    _services = {}
    _config = None

    @classmethod
    def initialize(cls, config: Dict[str, Any]):
        """Initialize the registry with configuration."""
        cls._config = config

    @classmethod
    def get_service(cls, service_key: str):
        """Get a service by key, initializing if necessary."""
        if service_key not in cls._services:
            if service_key == "relationship_detector":
                cls._services[service_key] = RelationshipComponentFactory.create_detector(cls._config)
            elif service_key == "relationship_store":
                from backend.relationships.store import RelationshipStore
                db_path = Path(cls._config.get("relationships.storage.db_location", ".relationships.db"))
                cls._services[service_key] = RelationshipStore(db_path)
            elif service_key == "relationship_graph":
                from backend.relationships.graph import RelationshipGraph
                store = cls.get_service("relationship_store")
                cls._services[service_key] = RelationshipGraph(store)

        return cls._services[service_key]

    @classmethod
    def register_service(cls, service_key: str, service_instance):
        """Register a custom service implementation."""
        cls._services[service_key] = service_instance
```

## 7. File Processing Integration

```python
# In file_processor.py

async def process_file(self, file_path: Path) -> Dict[str, Any]:
    """Process a single file, extract metadata, and detect relationships."""

    # Original processing
    metadata = await self.metadata_extractor.extract_metadata(file_path)

    # Relationship detection (if enabled)
    if self.config.get("relationships.detection.enabled", False):
        try:
            # Use service locator to get detector
            detector = ServiceRegistry.get_service("relationship_detector")

            # Detect relationships
            relationships = await detector.detect_relationships([file_path])

            # Store relationships
            if relationships:
                store = ServiceRegistry.get_service("relationship_store")
                await store.add_relationships(relationships)

                # Add relationship count to metadata
                metadata["relationship_count"] = len(relationships)

                # Publish event
                EventBus.publish(RelationshipDetectedEvent(file_path, relationships))

        except Exception as e:
            logger.error(f"Error detecting relationships for {file_path}: {str(e)}")

    # Continue with original processing
    await self.index_file(file_path, metadata)
    return metadata
```

## 8. Search Engine Integration

```python
# In search_adapter.py

class SearchRelationshipAdapter:
    """Adapter for integrating relationships with search functionality."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._store = None

    def _get_store(self):
        """Get the relationship store (lazy initialization)."""
        if self._store is None:
            self._store = ServiceRegistry.get_service("relationship_store")
        return self._store

    def enhance_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance search results with relationship information."""
        if not self.config.get("relationships.search.enhance_results", True):
            return results

        enhanced_results = []
        store = self._get_store()

        for result in results:
            # Create a copy of the result
            enhanced = dict(result)

            # Add relationship data if available
            path = Path(enhanced["path"])
            try:
                relationships = store.get_relationships_for_file(path)
                if relationships:
                    enhanced["relationships"] = {
                        "count": len(relationships),
                        "types": list(set(r.rel_type.name for r in relationships))
                    }
            except Exception as e:
                logger.debug(f"Error enhancing search result with relationships: {str(e)}")

            enhanced_results.append(enhanced)

        return enhanced_results

    def rerank_with_relationships(
        self,
        results: List[Dict[str, Any]],
        context_file: Path
    ) -> List[Dict[str, Any]]:
        """Rerank search results based on relationships to a context file."""
        if not context_file or not self.config.get("relationships.search.rerank_results", True):
            return results

        store = self._get_store()

        try:
            # Get related files
            related_files = store.get_related_files(context_file)

            # Create a boost map
            boosts = {}
            for path, rel_type, strength in related_files:
                boosts[str(path)] = strength

            # Apply boosts to search scores
            for result in results:
                path_str = str(Path(result["path"]))
                if path_str in boosts:
                    result["original_score"] = result["score"]
                    result["score"] *= (1.0 + boosts[path_str])
                    result["relationship_boost"] = boosts[path_str]

            # Rerank results
            results.sort(key=lambda x: x["score"], reverse=True)
        except Exception as e:
            logger.error(f"Error reranking with relationships: {str(e)}")

        return results
```

## 9. Tagging System Integration

```python
# In tagging_adapter.py

class TagRelationshipAdapter:
    """Adapter for integrating relationships with the tagging system."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._store = None
        self._tag_manager = None

    def _get_store(self):
        """Get the relationship store (lazy initialization)."""
        if self._store is None:
            self._store = ServiceRegistry.get_service("relationship_store")
        return self._store

    def _get_tag_manager(self):
        """Get the tag manager (lazy initialization)."""
        if self._tag_manager is None:
            self._tag_manager = ServiceRegistry.get_service("tag_manager")
        return self._tag_manager

    async def suggest_tags_from_relationships(self, file_path: Path) -> List[Dict[str, Any]]:
        """Suggest tags based on relationships to other files."""
        if not self.config.get("relationships.tagging.suggest_from_relationships", True):
            return []

        store = self._get_store()
        tag_manager = self._get_tag_manager()

        try:
            # Get related files
            related_files = store.get_related_files(file_path)

            # Collect tags from related files
            tag_scores = {}
            for path, rel_type, strength in related_files:
                # Get tags for the related file
                related_tags = await tag_manager.get_tags(path)

                # Add to tag scores with relationship strength as weight
                for tag in related_tags:
                    if tag in tag_scores:
                        tag_scores[tag] += strength
                    else:
                        tag_scores[tag] = strength

            # Convert to suggestions
            suggestions = []
            for tag, score in sorted(tag_scores.items(), key=lambda x: x[1], reverse=True):
                suggestions.append({
                    "tag": tag,
                    "confidence": min(score, 1.0),
                    "source": "relationship"
                })

            return suggestions
        except Exception as e:
            logger.error(f"Error suggesting tags from relationships: {str(e)}")
            return []
```

## 10. Implementation Sequence

### Phase 1: Core Framework

1. **Configuration System Updates**
   - Add relationship configuration schema
   - Implement default configuration values
   - Create configuration validation

2. **Interface & Factory Implementation**
   - Create abstract interfaces
   - Implement factory pattern
   - Set up service registry

3. **Event System Setup**
   - Define relationship events
   - Implement event bus
   - Create event handlers

### Phase 2: Core Implementations

4. **Complete Detector Implementations**
   - Enhance import analysis detector
   - Implement content similarity detector
   - Create structure-based detector

5. **Visualization Tools**
   - Implement graph export enhancements
   - Create visualization adapters

6. **CLI Interface Development**
   - Complete CLI command implementations
   - Add consistent parameter handling

### Phase 3: Integration

7. **System Integration**
   - Integrate with file processing pipeline
   - Connect to search engine
   - Link with tagging system

8. **Testing & Documentation**
   - Write unit tests for all components
   - Create integration tests
   - Update documentation

## 11. Success Criteria

The File Relationship Mapping feature will be considered complete when:

1. All core components are implemented with proper interfaces
2. Integration with existing systems is working through appropriate adapters
3. Configuration system supports all relationship settings
4. Event system correctly propagates relationship changes
5. CLI provides complete interface for all operations
6. Tests cover all components and integration points
7. Documentation is complete and up-to-date
