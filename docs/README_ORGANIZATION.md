# Documentation Organization for The AIchemist Codex

This document explains the organization of documentation for The AIchemist Codex
project.

## Directory Structure

The documentation is organized as follows:

```
docs/
├── api/                   # API reference documentation (RST)
├── markdown/              # All Markdown format documentation
│   ├── api/               # API documentation in Markdown
│   ├── development/       # Development guides and notes in Markdown
│   ├── reference/         # Reference documentation in Markdown
│   ├── tutorials/         # Tutorials in Markdown
│   ├── user_guide/        # User guides in Markdown
│   ├── index.md           # Index of all Markdown documentation
│   └── README.md          # Information about the Markdown documentation
├── organized_markdown/    # Original component-specific documentation in Markdown
├── tutorials/             # Tutorials (RST)
├── user_guides/           # User guides (RST)
├── _build/                # Generated documentation output
├── _static/               # Static assets for documentation
├── _templates/            # Sphinx templates
├── images/                # Images used in documentation
├── conf.py                # Sphinx configuration
├── index.rst              # Main documentation index
└── *.rst                  # RST documentation files
```

## Documentation Formats

The documentation uses two primary formats:

1. **reStructuredText (.rst)** - Used for the main Sphinx documentation
2. **Markdown (.md)** - Used for GitHub-friendly documentation and developer
   notes

## Organization Principles

1. **Format Separation:**

   - RST files are in the root and topic-specific directories
   - Markdown files are organized in the `markdown/` directory

2. **Topic Organization:**

   - Both RST and Markdown follow the same topic organization
   - Similar topics are in similarly named directories

3. **Relationship Between Formats:**
   - Some content is duplicated between formats for different audiences
   - Cross-references should be maintained between related files

## Finding Documentation

- For user documentation, start with `index.rst` or the `user_guides/` directory
- For developer documentation, start with `markdown/development/` or
  `development.rst`
- For API documentation, check `api/` directory or `markdown/api/`
- For tutorials, look in the `tutorials/` directory

## Duplicate Content

A duplicate content analysis has been performed to identify similar content
between RST and MD files. The results are available in
`duplicate_content_report.md`.

## Documentation Build

To build the documentation:

```bash
# Navigate to the docs directory
cd docs

# Build the documentation
make html

# View the documentation
# On Windows:
start _build/html/index.html
# On Linux:
# xdg-open _build/html/index.html
# On macOS:
# open _build/html/index.html
```

## Maintaining Documentation

When updating documentation:

1. Determine which format(s) need to be updated based on the audience
2. For user-facing content, prefer updating RST files
3. For developer-focused content, prefer updating Markdown files
4. If both formats cover the same topic, consider updating both
5. Use the scripts in this directory to help maintain organization:
   - `organize-docs.ps1` - Organizes documentation files
   - `find-duplicates.ps1` - Identifies potential duplicate content
