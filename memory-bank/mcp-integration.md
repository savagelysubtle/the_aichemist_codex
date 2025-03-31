---
created: '2025-03-28'
last_modified: '2025-03-28'
status: documented
type: note
---

# AIchemist MCP Hub Integration

## Overview

The AIchemist MCP Hub now integrates directly with the memory-bank Obsidian vault through the Model Context Protocol (MCP). This integration allows for seamless interaction between AI agents, the AIchemist codebase, and your structured knowledge base in Obsidian.

## Available MCP Tools

The following Obsidian-related tools are available through the MCP Hub:

### Memory Bank Structure Tools

#### `list_memory_structure`

Get a complete overview of the Memory Bank structure including categorized folders and core files.

**Parameters:**
- None

**Returns:**
- Core files list
- Directory structure
- Categorized folders
- File count statistics

#### `get_category_notes`

Retrieve notes from a specific category by prefix or name.

**Parameters:**
- `category` (string): Category prefix (like "01") or name (like "Domain")

**Returns:**
- List of directories matching the category
- Notes in each directory with titles and paths
- Total note count

#### `analyze_memory_bank_structure`

Get statistics and insights about the Memory Bank structure, including link relationships.

**Parameters:**
- None

**Returns:**
- File and directory counts
- Categorized structure
- Link statistics
- Most linked files
- Top-level files list

#### `get_current_context`

Extract structured information from the activeContext.md file to understand the current project status.

**Parameters:**
- None

**Returns:**
- Parsed sections from activeContext.md
- Current focus areas
- Next steps

### Obsidian Note Tools

#### `search_obsidian_notes`

Search across all notes in the memory-bank vault for specific content.

**Parameters:**
- `query` (string): The search query
- `vault_path` (optional string): Custom path to the Obsidian vault (defaults to memory-bank)

**Returns:**
- File matches with line numbers and context

#### `get_linked_notes`

Analyze a specific note to find both outgoing links (notes it links to) and incoming links (notes that link to it).

**Parameters:**
- `note_path` (string): Path to the note relative to vault root
- `vault_path` (optional string): Custom path to the Obsidian vault (defaults to memory-bank)

**Returns:**
- Outgoing links (both internal wiki-links and markdown links)
- Incoming links (notes that reference this note)

## Integration with BIG BRAIN

The MCP Hub integration enhances BIG BRAIN's capabilities by:

1. **Memory Bank Access**: Provides direct access to all knowledge stored in memory-bank
2. **Structure Navigation**: Allows exploration of the memory-bank folder structure
3. **Context Awareness**: Provides tools to understand current project context and focus
4. **Knowledge Graph Navigation**: Enables traversal of the knowledge graph through linked notes
5. **Information Retrieval**: Allows targeted search for specific information across the vault

## Example Usage

To get an overview of the memory-bank structure:

```json
{
  "tool": "list_memory_structure"
}
```

To get notes from a specific category:

```json
{
  "tool": "get_category_notes",
  "parameters": {
    "category": "01"  // Can use "01" or "Domain"
  }
}
```

To analyze the memory-bank structure and links:

```json
{
  "tool": "analyze_memory_bank_structure"
}
```

To get the current project context:

```json
{
  "tool": "get_current_context"
}
```

To search for specific content across all memory-bank notes:

```json
{
  "tool": "search_obsidian_notes",
  "parameters": {
    "query": "clean architecture"
  }
}
```

To analyze a note's connections in the knowledge graph:

```json
{
  "tool": "get_linked_notes",
  "parameters": {
    "note_path": "systemPatterns.md"
  }
}
```

## Configuration

The MCP Hub is configured through `.cursor/mcp.json` to provide these tools to AI agents. The default configuration points to the memory-bank directory in your project root.

## Additional MCP Tools

Beyond Obsidian integration, the MCP Hub provides additional tools:

- `get_git_status`: Repository status information
- `list_branches`: Git branch management
- `search_codebase`: Code search capabilities
- `analyze_file`: File structure and content analysis
- `list_directory`: Directory exploration
- `read_file`: File content access
- `write_file`: Content writing capabilities
- `sequential_thinking`: Complex problem breakdown

## Relationship Management Tools

The MCP Hub now provides advanced tools for managing relationships between files in the codebase:

### `create_relationship`

Create a new relationship between two files.

**Parameters:**
- `source_path` (string): Path to the source file
- `target_path` (string): Path to the target file
- `relationship_type` (string): Type of relationship (e.g., imports, extends, uses)
- `strength` (float, optional): Relationship strength (0.0-1.0, default: 1.0)
- `bidirectional` (boolean, optional): Create relationship in both directions (default: false)
- `metadata` (object, optional): Additional metadata for the relationship

**Returns:**
- Relationship ID
- Source and target paths
- Relationship type information
- Bidirectional status

### `list_relationships`

List relationships for a file or all relationships in the system.

**Parameters:**
- `path` (string, optional): Path to file to get relationships for
- `show_outgoing` (boolean, optional): Show outgoing relationships (default: true)
- `show_incoming` (boolean, optional): Show incoming relationships (default: true)
- `relationship_type` (string, optional): Filter by relationship type
- `show_all` (boolean, optional): List all relationships in the system (default: false)
- `limit` (integer, optional): Maximum number of relationships to return (default: 100)

**Returns:**
- List of relationships with source, target, type, strength, and direction
- Total count of relationships
- File path (if specified)

### `delete_relationship`

Delete relationships between files.

**Parameters:**
- `relationship_id` (integer, optional): ID of the relationship to delete
- `source_path` (string, optional): Source file path
- `target_path` (string, optional): Target file path
- `relationship_type` (string, optional): Type of relationship to delete
- `delete_all` (boolean, optional): Delete all relationships for the specified files

**Returns:**
- Number of relationships deleted
- Operation status

### `get_relationship_types`

Get available relationship types.

**Parameters:**
- None

**Returns:**
- List of available relationship types
- Common examples with descriptions

### `visualize_relationships`

Visualize relationships for a file or a group of files.

**Parameters:**
- `path` (string): Path to the file to visualize relationships for
- `include_incoming` (boolean, optional): Include incoming relationships (default: true)
- `include_outgoing` (boolean, optional): Include outgoing relationships (default: true)
- `max_depth` (integer, optional): Maximum depth for relationship traversal (default: 1)
- `format` (string, optional): Output format (text, mermaid, dot) (default: mermaid)

**Returns:**
- Visualization output in the specified format
- Node and edge count
- Format used

## Example Usage

Creating a relationship between files:

```json
{
  "tool": "create_relationship",
  "parameters": {
    "source_path": "src/module.py",
    "target_path": "src/utils.py",
    "relationship_type": "imports",
    "bidirectional": false
  }
}
```

Listing relationships for a file:

```json
{
  "tool": "list_relationships",
  "parameters": {
    "path": "src/module.py",
    "show_outgoing": true,
    "show_incoming": true
  }
}
```

Visualizing a relationship network:

```json
{
  "tool": "visualize_relationships",
  "parameters": {
    "path": "src/module.py",
    "max_depth": 2,
    "format": "mermaid"
  }
}
```

## Future Enhancements

Potential enhancements to the MCP-Obsidian integration:

1. **Note Creation Templates**: Ability to create new notes with proper templates based on category
2. **Tag Analytics**: Advanced tag usage analysis and relationship mapping
3. **Metadata Extraction**: Enhanced YAML frontmatter parsing for structured data access
4. **Visualization**: Generate knowledge graph visualizations
5. **Link Suggestions**: AI-powered suggestions for linking related notes

## Maintenance

The MCP-Obsidian integration is managed through the `aichemist_mcp_hub_new.py` file. The memory-bank structure is documented in `memory-bank/memory-bank-structure.md`.

## Sequential Thinking Tools Integration

The AIchemist Codex now integrates with the Sequential Thinking Tools server, which provides enhanced capabilities for breaking down complex problems and recommending appropriate tools for each step in the problem-solving process.

### Overview

The [mcp-sequentialthinking-tools](https://github.com/spences10/mcp-sequentialthinking-tools) server provides:

- Dynamic and reflective problem-solving through sequential thoughts
- Intelligent tool recommendations for each step, with confidence scores
- Detailed rationale for why specific tools are appropriate
- Support for branching and revision of thought processes
- Progress tracking with expected outcomes

### Configuration

The Sequential Thinking Tools server is configured in `.cursor/mcp.json` alongside the existing MCP Hub and Sequential Thinking Server. This provides complementary capabilities to the existing tools.

### Using Sequential Thinking Tools

To break down a complex problem and get tool recommendations:

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Initial step to analyze the memory bank structure",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 4
  }
}
```

The response will include:
- A structured breakdown of the current step
- Recommended tools with confidence scores
- Rationale for each recommendation
- Expected outcomes
- Conditions for the next step

### Benefits for AIchemist Codex

This integration enhances the system by:

1. Providing structured approaches to complex problems
2. Offering context-aware tool recommendations
3. Supporting step-by-step problem-solving processes
4. Improving decision-making through confidence scores
5. Enabling branching and revision of thoughts when needed

### Use Cases

Sequential Thinking Tools are particularly valuable for:

- Architecture design and analysis
- Codebase refactoring planning
- Memory bank organization and optimization
- Implementation strategy development
- Debugging complex issues

This integration complements the existing MCP Hub capabilities by adding a layer of strategic planning and tool recommendation, making it easier to tackle complex tasks in the AIchemist Codex project.

## Integrating Sequential Thinking Tools with Obsidian

The Sequential Thinking Tools can be combined with the Obsidian integration tools to create a powerful knowledge management workflow. This integration ensures that your knowledge web continues to grow organically as you work with the codebase.

### Combined Workflow Examples

#### Analyzing Memory Bank Structure

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to understand and analyze the current memory bank structure",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 3
  }
}
```

The response might recommend:
1. First using `list_memory_structure` to get an overview
2. Then using `analyze_memory_bank_structure` for deeper insights
3. Finally using `get_category_notes` to explore specific areas of interest

#### Adding New Knowledge

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to add new information about Sequential Thinking Tools and ensure it's properly linked in the knowledge graph",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 4
  }
}
```

The response might guide you through:
1. Using `search_obsidian_notes` to find related content
2. Getting context with `get_current_context`
3. Examining relationships with `get_linked_notes`
4. Creating backlinks to ensure knowledge connectivity

### Maintaining Knowledge Connectivity

This integration automatically ensures that:

1. **New Components Are Linked**: Sequential thinking leads to identifying necessary connections between knowledge components
2. **Context Is Preserved**: Each step builds on previous knowledge while maintaining context
3. **Relationships Are Tracked**: Connections between notes are systematically maintained
4. **Knowledge Discovery Is Enhanced**: The system helps identify gaps and opportunities in the knowledge base

### Implementation Benefits

By integrating Sequential Thinking Tools with Obsidian:

1. **Guided Knowledge Management**: Step-by-step guidance for knowledge capture and organization
2. **Enhanced Discovery**: Confidence-scored recommendations for which knowledge tools to use
3. **Systematic Connection Building**: Structured approach to creating and maintaining backlinks
4. **Adaptive Knowledge Organization**: Flexible thinking processes that evolve with your codebase
5. **Contextual Documentation**: Documentation that maintains awareness of the project's current state

These combined capabilities ensure that your knowledge web grows organically and remains connected as the codebase evolves.

## Enhanced Backlinks Integration

The AIchemist Codex now includes enhanced backlink generation capabilities that work seamlessly with both Sequential Thinking Tools and the MCP Hub. This integration provides advanced knowledge relationship management to maintain a well-connected knowledge web.

### Backlink Analysis Tools

#### `analyze_knowledge_connections`

Performs comprehensive analysis of knowledge connections in the Memory Bank to identify potential missing links and important knowledge nodes.

**Parameters:**
- `generate_report` (boolean, optional): Whether to generate a detailed Markdown report (default: true)
- `export_for_mcp` (boolean, optional): Whether to export data for MCP tools (default: true)

**Returns:**
- Analysis statistics including orphaned notes and potential connections
- Path to generated report if applicable
- Path to exported data if applicable

#### `update_all_backlinks`

Updates backlinks for all files in the memory bank to ensure knowledge connections are properly maintained.

**Parameters:**
- `vault_path` (string, optional): Custom path to the Obsidian vault (defaults to memory-bank)

**Returns:**
- Number of files updated
- Total backlinks added
- Statistics on knowledge connectivity

### Integration with Sequential Thinking

This backlinks system is deeply integrated with Sequential Thinking Tools, enabling guided knowledge management:

1. The Sequential Thinking Tools can recommend using backlink analysis when it would benefit knowledge organization
2. Backlink analysis results can suggest specific sequential thinking paths to explore
3. Potential connections identified by backlink analysis can be explored using sequential thinking workflows

### Example Integration Workflow

This combined workflow demonstrates the power of integrating Sequential Thinking with backlink analysis:

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "I need to identify and resolve disconnected knowledge in my Memory Bank",
    "next_thought_needed": true,
    "thought_number": 1,
    "total_thoughts": 5
  }
}
```

Followed by:

```json
{
  "tool": "analyze_knowledge_connections",
  "parameters": {
    "generate_report": true,
    "export_for_mcp": true
  }
}
```

Then continuing with:

```json
{
  "tool": "sequentialthinking_tools",
  "parameters": {
    "thought": "Based on the backlink analysis, I need to create connections between related domains that are currently disconnected",
    "next_thought_needed": true,
    "thought_number": 2,
    "total_thoughts": 5
  }
}
```

### Benefits for Knowledge Management

This integration enhances the AIchemist Codex knowledge management capabilities by:

1. **Automatic Relationship Discovery**: Identifies potential connections that might be missed manually
2. **Knowledge Graph Analysis**: Provides insights into the structure and health of your knowledge base
3. **Systematic Link Maintenance**: Ensures all backlinks are properly maintained as knowledge evolves
4. **Guided Connection Building**: Uses Sequential Thinking to guide the process of building new connections
5. **Knowledge Gap Identification**: Highlights orphaned notes and knowledge islands that need integration

### Implementation Details

The enhanced backlinks system is implemented in `create_backlinks.py` with these key components:

- YAML frontmatter metadata extraction
- Knowledge relationship analysis
- Confidence scoring for potential connections
- Integration with Sequential Thinking workflows
- Exportable data for MCP tools

This implementation ensures that your knowledge web continues to grow with you and the codebase in a structured, connected manner.

## Backlinks
- [[backlinks-analysis]]
- [[sequential-thinking-obsidian-workflow]]
