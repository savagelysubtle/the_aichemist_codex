---
created: '2025-03-28'
last_modified: '2025-03-28'
layer: core
status: documented
type: note
---

# Tags and Metadata System

## YAML Frontmatter
Use YAML frontmatter at the top of each note for structured metadata:

```yaml
---
type: [entity|component|pattern|decision|reference]
status: [draft|implemented|documented|deprecated]
layer: [domain|application|infrastructure|interface]
created: 2023-03-28
---
```

## Tags
Use these tag formats:
- #entity
- #component
- #pattern
- #decision
- #bug
- #enhancement
- #inprogress
- #completed