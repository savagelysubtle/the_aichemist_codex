# Intelligent Auto-Tagging

The Aichemist Codex provides a powerful tagging system for organizing and categorizing files based on their content and relationships. The system combines machine learning, hierarchical organization, and collaborative filtering to offer a comprehensive approach to file organization.

## Features

### 1. Automatic Tag Suggestion

The system automatically suggests relevant tags for files based on:

- **Content Analysis**: Extracts keywords, topics, and entities from file content
- **Metadata Analysis**: Uses file type, extension, and other metadata
- **Machine Learning**: Learns from previously tagged files to improve suggestions
- **Collaborative Filtering**: Suggests tags based on similar files

### 2. Hierarchical Tag Organization

Tags can be organized in a hierarchical structure, allowing for more sophisticated organization:

- **Parent-Child Relationships**: Tags can have parent and child relationships
- **Taxonomy Management**: Import/export tag hierarchies
- **Inheritance**: Files tagged with a child tag automatically inherit parent tags
- **Path Navigation**: Navigate through tag hierarchies to find related files

### 3. Advanced Tag-Based Search

Find files using powerful tag-based queries:

- **AND/OR Queries**: Find files with all specified tags or any of them
- **Confidence Thresholds**: Filter by tag confidence level
- **Hierarchical Queries**: Search including parent/child tags
- **Related Files**: Find files with related tags

### 4. Batch Operations

Process multiple files efficiently:

- **Batch Tagging**: Apply tags to multiple files at once
- **Directory Processing**: Process entire directories with recursive options
- **Automatic Application**: Optionally apply suggested tags automatically

## Usage

### Command Line Interface

The tagging system is accessible through the command line interface:

#### Basic Tag Management

```bash
# Add tags to a file
python -m backend.cli tags add path/to/file.txt "tag1" "tag2" "tag3"

# Remove tags from a file
python -m backend.cli tags remove path/to/file.txt "tag1" "tag2"

# List tags for a file
python -m backend.cli tags list --file path/to/file.txt

# List all tags with usage counts
python -m backend.cli tags list
```

#### Tag Suggestions

```bash
# Get tag suggestions for a file
python -m backend.cli tags suggest path/to/file.txt

# Get suggestions with custom confidence threshold
python -m backend.cli tags suggest path/to/file.txt --threshold 0.7

# Apply suggested tags automatically
python -m backend.cli tags suggest path/to/file.txt --apply

# Save suggestions to a file
python -m backend.cli tags suggest path/to/file.txt --output suggestions.json
```

#### Batch Processing

```bash
# Process a directory
python -m backend.cli tags batch path/to/directory/

# Process recursively with a pattern
python -m backend.cli tags batch path/to/directory/ --recursive --pattern "*.py"

# Apply suggested tags automatically
python -m backend.cli tags batch path/to/directory/ --apply
```

#### Finding Files by Tags

```bash
# Find files with any of the specified tags (OR)
python -m backend.cli tags find "python" "code"

# Find files with all specified tags (AND)
python -m backend.cli tags find "python" "code" --all

# Find with minimum confidence threshold
python -m backend.cli tags find "python" "code" --threshold 0.8

# Save results to a file
python -m backend.cli tags find "python" "code" --output results.json
```

#### Tag Hierarchy Management

```bash
# Add a parent-child relationship
python -m backend.cli tags hierarchy add "parent_tag" "child_tag"

# Remove a relationship
python -m backend.cli tags hierarchy remove "parent_tag" "child_tag"

# Show the tag hierarchy
python -m backend.cli tags hierarchy show

# Show hierarchy for a specific tag
python -m backend.cli tags hierarchy show --tag "code"

# Export the hierarchy to a file
python -m backend.cli tags hierarchy export hierarchy.json

# Import a hierarchy from a file
python -m backend.cli tags hierarchy import hierarchy.json
```

#### Classifier Management

```bash
# Train the tag classifier
python -m backend.cli tags classifier train path/to/training/directory/

# Get classifier information
python -m backend.cli tags classifier info
```

## Implementation Details

### Architecture

The tagging system consists of the following components:

1. **TagManager**: Core component for managing tag operations
2. **TagHierarchy**: Manages hierarchical relationships between tags
3. **TagClassifier**: Machine learning classifier for automatic tag suggestion
4. **TagSuggester**: Combines multiple suggestion strategies

### Database Schema

Tags and their relationships are stored in an SQLite database with the following tables:

- **tags**: Stores tag names, descriptions, and metadata
- **tag_hierarchy**: Stores parent-child relationships between tags
- **file_tags**: Associates files with tags, including confidence scores and sources

### Machine Learning

The system uses machine learning to suggest tags:

- **Feature Extraction**: Extracts features from file content and metadata
- **Classification**: Uses a trained model to predict appropriate tags
- **Confidence Scoring**: Provides confidence scores for suggestions
- **Training**: Can be trained on existing tagged files to improve accuracy

### Performance Considerations

- **Asynchronous Processing**: All operations are asynchronous for better performance
- **Batch Operations**: Efficient batch processing for multiple files
- **Caching**: Key operations are cached for better performance
- **Selective Processing**: Processes only files that match specified patterns

## Example Use Cases

### Document Organization

Automatically categorize documents based on their content, with tags like "report", "invoice", "contract", etc.

### Code Repository Management

Tag code files with language, framework, functionality, and component tags to make finding relevant code easier.

### Media Library Organization

Organize media files with tags for content type, subject, project, etc.

## Best Practices

1. **Start with Manual Tagging**: Initially tag files manually to train the classifier
2. **Create a Tag Hierarchy**: Organize tags hierarchically for better navigation
3. **Use Specific Tags**: More specific tags provide better organization
4. **Combine with Other Features**: Use tagging alongside search and other organization features
5. **Review Automatic Tags**: Periodically review automatically applied tags for accuracy