# AIchemist Codex Tagging and Relationships Guide

This guide explains how to use the tagging and relationship commands in the AIchemist Codex CLI. These commands allow you to organize your codebase by adding tags to files and defining relationships between them.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Tagging Commands](#tagging-commands)
  - [Adding Tags](#adding-tags)
  - [Removing Tags](#removing-tags)
  - [Listing Tags](#listing-tags)
  - [Suggesting Tags](#suggesting-tags)
- [Relationship Commands](#relationship-commands)
  - [Creating Relationships](#creating-relationships)
  - [Listing Relationships](#listing-relationships)
  - [Removing Relationships](#removing-relationships)
  - [Detecting Relationships](#detecting-relationships)
  - [Visualizing Relationships](#visualizing-relationships)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before using these commands, ensure you have installed the AIchemist Codex with all its dependencies:

```bash
pip install -e .
```

## Tagging Commands

Tags help you organize and categorize your files based on their content, purpose, or any other criteria.

### Adding Tags

Add tags to files or directories:

```bash
aichemist tag add <path> <tag1> <tag2> ...
```

Options:
- `--recursive` / `-r`: Apply tags to all files in directory recursively

Examples:
```bash
# Add tags to a single file
aichemist tag add src/utils.py utility helper

# Add tags to all files in a directory recursively
aichemist tag add src/components -r frontend react
```

### Removing Tags

Remove tags from files or directories:

```bash
aichemist tag remove <path> <tag1> <tag2> ...
```

Options:
- `--recursive` / `-r`: Apply to all files in directory recursively
- `--all` / `-a`: Remove all tags from the specified files

Examples:
```bash
# Remove specific tags from a file
aichemist tag remove src/utils.py helper

# Remove all tags from files in a directory
aichemist tag remove src/components -r --all
```

### Listing Tags

List tags for files or all tags in the system:

```bash
aichemist tag list [path]
```

Options:
- `--recursive` / `-r`: Include files in directory recursively
- `--all` / `-a`: List all tags in the system

Examples:
```bash
# List all tags in the system
aichemist tag list --all

# List tags for a specific file
aichemist tag list src/utils.py

# List tags for all files in a directory
aichemist tag list src/components -r
```

### Suggesting Tags

Suggest tags for files based on content analysis:

```bash
aichemist tag suggest <path>
```

Options:
- `--recursive` / `-r`: Process directory recursively
- `--threshold` / `-t`: Confidence threshold (0.0-1.0), default: 0.7
- `--apply` / `-a`: Apply suggested tags automatically

Examples:
```bash
# Suggest tags for a file
aichemist tag suggest src/utils.py

# Suggest and apply tags for files in a directory
aichemist tag suggest src/components -r --apply

# Adjust confidence threshold for suggestions
aichemist tag suggest src/models -r --threshold 0.6
```

## Relationship Commands

Relationships define connections between files, such as imports, extensions, or references.

### Creating Relationships

Create a relationship between two files:

```bash
aichemist rel create <source> <target> <type>
```

Options:
- `--strength` / `-s`: Relationship strength (0.0-1.0), default: 1.0
- `--bidirectional` / `-b`: Create relationship in both directions
- `--metadata` / `-m`: Additional metadata in key=value format

Examples:
```bash
# Create a simple relationship
aichemist rel create src/module.py src/utils.py imports

# Create a bidirectional relationship
aichemist rel create src/component.tsx src/styles.css uses --bidirectional

# Create a relationship with metadata
aichemist rel create src/app.py src/config.py depends --metadata author=john reason=configuration
```

### Listing Relationships

List relationships for a file or all relationships in the system:

```bash
aichemist rel list [path]
```

Options:
- `--outgoing/--no-outgoing`: Show/hide outgoing relationships
- `--incoming/--no-incoming`: Show/hide incoming relationships
- `--type` / `-t`: Filter by relationship type
- `--all` / `-a`: List all relationships in the system

Examples:
```bash
# List all relationships in the system
aichemist rel list --all

# List outgoing and incoming relationships for a file
aichemist rel list src/module.py

# List only incoming relationships
aichemist rel list src/utils.py --no-outgoing

# Filter relationships by type
aichemist rel list src/component.tsx --type uses
```

### Removing Relationships

Remove relationships between files:

```bash
aichemist rel remove <source> <target>
```

Options:
- `--type` / `-t`: Type of relationship to remove (removes all types if not specified)
- `--bidirectional` / `-b`: Remove relationship in both directions

Examples:
```bash
# Remove all relationships between two files
aichemist rel remove src/module.py src/utils.py

# Remove a specific relationship type
aichemist rel remove src/component.tsx src/styles.css --type uses

# Remove bidirectional relationships
aichemist rel remove src/app.py src/config.py --bidirectional
```

### Detecting Relationships

Automatically detect relationships between files:

```bash
aichemist rel detect <path>
```

Options:
- `--recursive` / `-r`: Process directory recursively
- `--types` / `-t`: Relationship types to detect (default: imports, includes, references)
- `--apply` / `-a`: Apply detected relationships

Examples:
```bash
# Detect relationships for a file
aichemist rel detect src/module.py

# Detect relationships for all files in a directory
aichemist rel detect src/components --recursive

# Detect specific relationship types and apply them
aichemist rel detect src/utils.py --types imports references --apply
```

### Visualizing Relationships

Visualize relationships between files:

```bash
aichemist rel visualize <path>
```

Options:
- `--recursive` / `-r`: Include files in directory recursively
- `--depth` / `-d`: Relationship depth to visualize (default: 1)
- `--output` / `-o`: Output file path (if not provided, display in console)
- `--format` / `-f`: Output format: tree, dot, or json (default: tree)

Examples:
```bash
# Visualize relationships for a file in the console
aichemist rel visualize src/module.py

# Visualize relationships with depth 2 for files in a directory
aichemist rel visualize src/components --recursive --depth 2

# Generate a DOT file for use with GraphViz
aichemist rel visualize src/app.py --output graph.dot --format dot
```

## Advanced Usage

### Using Tags and Relationships Together

Tags and relationships can be combined for powerful codebase navigation:

```bash
# Find all files with a specific tag
aichemist tag list --all | grep model

# Visualize relationships for all files with a specific tag
for file in $(aichemist tag list --all | grep model | awk '{print $1}'); do
  aichemist rel visualize "$file"
done
```

### Custom Relationship Types

While the system provides common relationship types (imports, extends, uses, etc.), you can create custom types:

```bash
aichemist rel create src/frontend.js src/backend.py communicates-with
```

### Database Locations

Tags and relationships are stored in SQLite databases in the following locations:

- Tags: `~/.aichemist/tags.db`
- Relationships: `~/.aichemist/relationships.db`

You can change these locations by updating your AIchemist Codex configuration.

## Troubleshooting

### Missing Dependencies

If you encounter errors related to missing dependencies, ensure you have installed all required packages:

```bash
pip install aiosqlite sentence-transformers
```

### Performance Issues

For large codebases:

- Use the `--recursive` flag judiciously to avoid processing too many files at once
- Use a higher threshold (e.g., 0.8) when suggesting tags to get more precise results
- Limit relationship visualization depth for complex codebases
