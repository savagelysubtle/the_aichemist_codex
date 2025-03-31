---
created: '2025-03-28'
last_modified: '2025-03-28'
layer: core
status: documented
type: note
---

# Architecture Map

## System Design
- [[systemPatterns|System Patterns & Architecture]]
- [[Clean-Architecture|Clean Architecture Principles]]

## Layer Documentation
- [[Domain-Layer|Domain Layer Structure]]
- [[Application-Layer|Application Layer Design]]
- [[Infrastructure-Layer|Infrastructure Services]]
- [[Interface-Layer|Interface Adapters]]

## Integration
- [[Integration-Patterns|Integration Patterns & Approaches]]

# Domain Models

The AIchemist system defines these core [[entity]] types:

- [[File]] - Represents a file with metadata
- [[Memory]] - Knowledge unit with relationships
- [[Relationship]] - Connection between entities

These models are implemented in the [[Models]] module.