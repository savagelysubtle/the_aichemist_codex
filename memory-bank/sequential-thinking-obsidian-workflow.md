---
created: '2025-03-28'
last_modified: '2025-03-28'
status: documented
type: guide
---

# Sequential Thinking Tools with Obsidian Workflow

This guide demonstrates practical workflows for using Sequential Thinking Tools with Obsidian integration to maintain a connected and growing knowledge web.

## Workflow 1: Exploring and Understanding Memory Bank Structure

### Step 1: Begin Sequential Thinking

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to understand the current structure of the memory bank to identify areas for improvement",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 4
  }
}
```

### Step 2: Follow Tool Recommendations

Based on the confidence-scored tool recommendations, you might:

1. Use `list_memory_structure` to get an overview:
```json
{
  "tool": "list_memory_structure"
}
```

2. Analyze the structure for insights:
```json
{
  "tool": "analyze_memory_bank_structure"
}
```

3. Explore areas that need improvement:
```json
{
  "tool": "get_category_notes",
  "parameters": {
    "category": "01-Domain"
  }
}
```

4. Continue sequential thinking with what you've learned:
```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Based on the analysis, I notice the Domain layer documentation could be better organized and connected",
    "next_thought_needed": true,
    "thought_number": 2,
    "total_thoughts": 4
  }
}
```

## Workflow 2: Adding New Documentation and Maintaining Connections

### Step 1: Begin Sequential Thinking

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to add documentation about the new Sequential Thinking Tools integration and ensure it connects properly to existing knowledge",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 5
  }
}
```

### Step 2: Follow the Guided Process

Based on recommendations:

1. Search for related content:
```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "MCP integration"
  }
}
```

2. Get current context:
```json
{
  "tool": "get_current_context"
}
```

3. Analyze connections of related documents:
```json
{
  "tool": "get_linked_notes",
  "parameters": {
    "note_path": "mcp-integration.md"
  }
}
```

4. Continue with guidance for creating documentation with proper links:
```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Now I understand the existing documentation structure, I'll create new documentation for Sequential Thinking Tools with appropriate backlinks",
    "next_thought_needed": true,
    "thought_number": 2,
    "total_thoughts": 5
  }
}
```

## Workflow 3: Discovering Knowledge Gaps

### Step 1: Begin Sequential Thinking with a Question

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to identify gaps in our documentation about the CLI architecture",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 4
  }
}
```

### Step 2: Follow the Discovery Process

Based on recommendations:

1. Search for CLI architecture documentation:
```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "CLI architecture"
  }
}
```

2. Analyze relationship patterns:
```json
{
  "tool": "get_linked_notes",
  "parameters": {
    "note_path": "CLI-Architecture.md"
  }
}
```

3. Continue with identifying gaps:
```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Based on the search results and link analysis, I've identified that we're missing documentation on the service management pattern",
    "next_thought_needed": true,
    "thought_number": 2,
    "total_thoughts": 4
  }
}
```

## Workflow 4: Updating Knowledge Based on Code Changes

### Step 1: Begin Sequential Thinking

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I've made changes to the MCP implementation and need to update related documentation while maintaining knowledge connections",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 5
  }
}
```

### Step 2: Follow the Knowledge Update Process

Based on recommendations:

1. Find affected documentation:
```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "MCP implementation"
  }
}
```

2. Analyze document relationships:
```json
{
  "tool": "get_linked_notes",
  "parameters": {
    "note_path": "mcp-integration.md"
  }
}
```

3. Get current context:
```json
{
  "tool": "get_current_context"
}
```

4. Continue with a structured update plan:
```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Now I understand all the documentation that needs to be updated. I need to modify mcp-integration.md first, then update activeContext.md and finally ensure progress.md reflects these changes",
    "next_thought_needed": true,
    "thought_number": 2,
    "total_thoughts": 5
  }
}
```

## Workflow 5: Analyzing Knowledge Graph with Enhanced Backlinks

### Step 1: Begin Sequential Thinking for Knowledge Analysis

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to analyze the health of my knowledge graph and identify areas that need better connections",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 5
  }
}
```

### Step 2: Follow the Knowledge Analysis Process

Based on recommendations:

1. Run backlink analysis to get a comprehensive view:
```json
{
  "tool": "analyze_knowledge_connections",
  "parameters": {
    "generate_report": true,
    "export_for_mcp": true
  }
}
```

2. Review most referenced notes to understand knowledge hubs:
```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "backlinks-analysis.md \"Most Referenced Notes\""
  }
}
```

3. Examine orphaned notes that need integration:
```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "backlinks-analysis.md \"Orphaned Notes\""
  }
}
```

4. Continue with analyzing potential missing connections:
```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Based on the backlink analysis, I've identified several orphaned notes and high-confidence connection opportunities. I need a plan to integrate these into the knowledge web.",
    "next_thought_needed": true,
    "thought_number": 2,
    "total_thoughts": 5
  }
}
```

5. Update backlinks across all files:
```json
{
  "tool": "update_all_backlinks",
  "parameters": {
    "vault_path": "memory-bank"
  }
}
```

6. Continue with creating new connections based on recommendations:
```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Now I need to create specific content connections based on the highest confidence connection recommendations",
    "next_thought_needed": true,
    "thought_number": 3,
    "total_thoughts": 5
  }
}
```

## Best Practices

1. **Start with Sequential Thinking**: Begin complex tasks with the Sequential Thinking Tools to break down the problem
2. **Follow Confidence Scores**: Prioritize using tools with higher confidence scores in the recommendations
3. **Create Proper Backlinks**: Always use `[[document-name]]` wiki-link syntax when referencing other documents
4. **Check Existing Relationships**: Use `get_linked_notes` before modifying documents to understand connections
5. **Update Context Documents**: Always update `activeContext.md` when making significant changes
6. **Document Progress**: Track all significant changes in `progress.md`
7. **Use Branch Thinking**: For complex problems, use the branching capability to explore different approaches
8. **Revise Previous Thoughts**: Use the thought revision feature when new information requires changing direction

## Backlinks
- [[backlinks-analysis]]
