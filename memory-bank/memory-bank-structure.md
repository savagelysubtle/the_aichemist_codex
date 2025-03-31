---
created: '2025-03-28'
last_modified: '2025-03-28'
status: documented
type: note
---

# Memory Bank Structure

## Overview

The Memory Bank is an Obsidian vault that serves as the knowledge repository for the AIchemist Codex project. It follows a structured organization to categorize and maintain different types of information, making it easily accessible and navigable.

## Folder Structure

The Memory Bank uses a numeric prefix system for categorization:

- **00-Core/**: Foundational elements including guides, templates, and maps of content (MOCs)
  - **Guides/**: Instructions and tutorials
  - **Templates/**: Reusable document templates
  - **MOCS/**: Maps of Content for navigation

- **01-Domain/**: Domain model components and design
  - **Entities/**: Core domain entity definitions
  - Domain-related documentation

- **01-Domain-Layer/**: Implementation-specific domain components
  - Domain models and interfaces

- **02-Architecture/**: System architecture documentation
  - Architectural patterns and decisions
  - Component diagrams

- **03-Implementation/**: Implementation details and code documentation
  - Implementation strategies and patterns
  - Code-specific documentation

## Core Files

Several important files exist at the root of the Memory Bank:

- **activeContext.md**: Current project context, focus areas, and next steps
- **progress.md**: Project progress tracking and milestone documentation
- **codebase-review.md**: Comprehensive review of the codebase structure and status
- **mcp-integration.md**: Documentation of MCP integration with tools
- **systemPatterns.md**: System-wide patterns and conventions
- **productContext.md**: Product development context
- **techContext.md**: Technical environment context
- **projectbrief.md**: Project overview and goals

## Using the Memory Bank with MCP Tools

The AIchemist MCP Hub now provides specialized tools for working with the Memory Bank structure:

### 1. `list_memory_structure`

Get a complete overview of the Memory Bank structure including categorized folders and core files.

```json
{
  "tool": "list_memory_structure"
}
```

### 2. `get_category_notes`

Retrieve notes from a specific category by prefix or name.

```json
{
  "tool": "get_category_notes",
  "parameters": {
    "category": "01"  // Can use "01" or "Domain"
  }
}
```

### 3. `analyze_memory_bank_structure`

Get statistics and insights about the Memory Bank structure, including link relationships.

```json
{
  "tool": "analyze_memory_bank_structure"
}
```

### 4. `get_current_context`

Extract structured information from the activeContext.md file to understand the current project status.

```json
{
  "tool": "get_current_context"
}
```

### 5. `search_obsidian_notes`

Search across all Memory Bank notes for specific content.

```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "clean architecture"
  }
}
```

### 6. `get_linked_notes`

Analyze the connections between notes in the knowledge graph.

```json
{
  "tool": "get_linked_notes",
  "parameters": {
    "note_path": "systemPatterns.md"
  }
}
```

## Best Practices

1. **Maintain Structure**: Follow the numeric prefix convention for new folders
2. **Link Related Content**: Use Obsidian's `[[]]` links to connect related notes
3. **Update Context**: Keep the `activeContext.md` file updated with current focus areas
4. **Use Templates**: Leverage templates from `00-Core/Templates/` for consistency
5. **Navigate with MOCs**: Use Maps of Content in `00-Core/MOCS/` for easier navigation

## Memory Bank Maintenance

Regular maintenance of the Memory Bank ensures its continued usefulness:

1. Review and update the `activeContext.md` file weekly
2. Clean up orphaned notes (those without incoming links)
3. Check for and resolve broken links
4. Ensure new notes are properly categorized and linked
5. Use the `analyze_memory_bank_structure` tool to identify potential improvements

## Backlinks
- [[backlinks-analysis]]
