---
created: '2025-03-28'
last_modified: '2025-03-28'
layer: domain
status: documented
type: entity
---

# Domain Model Knowledge Graph

The AIchemist Codex domain model consists of these key entities and their relationships:

## Core Entities

- [[Memory]] - Stores knowledge with metadata
- [[Relationship]] - Connects entities
- [[Tag]] - Categorizes entities
- [[File]] - Represents filesystem objects

## Value Objects

- [[Metadata]] - Additional information
- [[Strength]] - Relationship strength indicator
- [[Content]] - Actual content data

## Services

- [[MemoryService]] - Manages memory operations
- [[RelationshipService]] - Handles relationship operations
- [[TaggingService]] - Manages tagging operations

## Repositories

- [[MemoryRepository]] - Stores and retrieves memories
- [[RelationshipRepository]] - Manages relationship storage
- [[TagRepository]] - Manages tag storage
