# Documentation for The Aichemist Codex

All project documentation has been moved to the `docs/` directory.

## Key Documentation Files

- **User Guide**: See `docs/getting_started.rst` and `docs/usage.rst`
- **Development Guide**: See `docs/development_guide.md`
- **Implementation Plan**: See `docs/implementation_plan.md`
- **Project Structure**: See `docs/directory_structure.rst`
- **API Reference**: See `docs/api/` directory
- **Tutorials**: See `docs/tutorials/` directory

## Building Documentation

To build the full documentation:

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

## Documentation Structure

The documentation is organized into the following categories:

1. **User Guide** - Information for end users of the application
2. **Developer Guide** - Information for developers working on the codebase
3. **API Reference** - Technical documentation of the code modules and classes
4. **Tutorials** - Step-by-step guides for common tasks
5. **Project Information** - Roadmap, changelog, and project overview

## Contributing to Documentation

If you'd like to contribute to the documentation, please see
`docs/contributing.rst` for guidelines.
