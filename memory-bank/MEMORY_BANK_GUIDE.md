# Memory Bank Guide

## Quick Navigation

### Core Files
- `activeContext.md` - Current project context and focus areas
- `progress.md` - Project progress tracking
- `codebase-review.md` - Codebase structure review
- `mcp-integration.md` - MCP tool integration docs
- `systemPatterns.md` - System-wide patterns
- `productContext.md` - Product development context
- `techContext.md` - Technical environment context
- `projectbrief.md` - Project overview and goals

### Directory Structure
```
memory-bank/
├── 00-Core/              # Foundational elements
│   ├── Guides/          # Instructions and tutorials
│   ├── Templates/       # Reusable document templates
│   └── MOCS/           # Maps of Content for navigation
├── 01-Domain/           # Domain model components
│   └── Entities/       # Core domain entity definitions
├── 01-Domain-Layer/     # Implementation domain components
├── 02-Architecture/     # System architecture docs
└── 03-Implementation/   # Implementation details
```

## Category Types

| Category | Description |
|----------|-------------|
| Core | Core system files essential for operation |
| Active | Currently active and in-use files |
| Short-term | Files relevant for current work session |
| Long-term | Archived knowledge for reference |
| Episodic | Records of specific events or sessions |
| Semantic | Conceptual and domain knowledge |
| Procedural | Process and methodology documentation |
| Creative | Ideation and design concepts |
| Features | Feature specifications and documentation |
| Integration | Integration points and external systems |
| Plans | Planning and roadmap documentation |

## Best Practices

1. **File Organization**
   - Follow numeric prefix convention for new folders
   - Place files in appropriate category directories
   - Use descriptive, kebab-case filenames

2. **Content Structure**
   - Start files with YAML frontmatter
   - Use clear headings and subheadings
   - Include creation and modification dates
   - Tag content appropriately

3. **Linking**
   - Use Obsidian's `[[]]` syntax for internal links
   - Create bidirectional links when relevant
   - Use standard Markdown links for external resources
   - Maintain link consistency

4. **Maintenance**
   - Update `activeContext.md` regularly
   - Review and clean up unused files
   - Check for broken links
   - Keep documentation current

## Working with Memory Bank

### Creating New Notes
1. Choose appropriate category directory
2. Use template from `00-Core/Templates/` if available
3. Include required frontmatter:
   ```yaml
   ---
   created: 'YYYY-MM-DD'
   last_modified: 'YYYY-MM-DD'
   status: draft|active|archived
   type: note|doc|spec|design
   ---
   ```

### Organizing Content
1. Use consistent structure:
   ```markdown
   # Title

   ## Overview
   Brief description

   ## Details
   Main content sections

   ## Related
   - [[Link to related note]]
   - External [reference](url)

## Backlinks
- [[backlinks-analysis]]
