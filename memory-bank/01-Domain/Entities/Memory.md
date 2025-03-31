---
type: entity
status: implemented
---

# Memory Entity

## Properties

- id: UUID
- content: string
- metadata: MetadataMap
- relationships: Relationship[]
- strength: float
- created_at: datetime
- updated_at: datetime

## Relationships

- **Has many**: [[Relationship]]
- **Tagged with**: [[Tag]]
- **Managed by**: [[MemoryRepository]]

## Usage Examples
