# Installing The AIchemist Codex from GitHub

## Local Development Setup

The AIchemist Codex can be installed directly from GitHub for local development using uv. This approach allows you to use the library in your projects while maintaining the ability to easily update and modify the code.

### Prerequisites

1. Python 3.13.0 or higher
2. uv package manager
3. Git

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/the_aichemist_codex.git
   cd the_aichemist_codex
   ```

2. **Install with uv**

   ```bash
   # Create and activate a new virtual environment
   uv venv

   # Install the package in editable mode
   uv pip install -e .
   ```

### Using in Another Project

To use the AIchemist Codex in another project on your machine:

1. **Add to Project Dependencies**

   ```toml
   # In your project's pyproject.toml
   [project]
   dependencies = [
       "the_aichemist_codex @ git+file:///absolute/path/to/the_aichemist_codex"
   ]
   ```

2. **Install Dependencies**

   ```bash
   cd your-project
   uv pip install -e .
   ```

### Development Configuration

The project uses several development tools that can be installed with:

```bash
uv pip install -e ".[dev]"
```

This includes:

- pytest for testing
- black for code formatting
- ruff for linting
- mypy for type checking
- sphinx for documentation

## Project Structure

```
the_aichemist_codex/
├── src/the_aichemist_codex/    # Main package code
├── tests/                      # Test suite
├── docs/                       # Documentation
└── memory-bank/               # Project knowledge base
```

## Verification

After installation, verify the setup:

```python
from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from pathlib import Path

# Create a test artifact
artifact = CodeArtifact(
    path=Path("test.py"),
    name="test.py"
)

print(f"Created artifact: {artifact}")
```

## Updating

To update to the latest version:

```bash
cd the_aichemist_codex
git pull
uv pip install -e .
```

## Troubleshooting

1. **Python Version**
   - Ensure Python 3.13.0+ is installed
   - Check with `python --version`

2. **Dependencies**
   - Clear uv cache if needed: `uv cache clean`
   - Reinstall dependencies: `uv pip install -e .`

3. **Path Issues**
   - Use absolute paths in pyproject.toml
   - Verify Git repository path is correct

## Best Practices

1. **Version Control**
   - Create a branch for local modifications
   - Keep main branch in sync with upstream

2. **Development**
   - Use development tools (pytest, black, ruff)
   - Follow project coding standards
   - Update documentation as needed

3. **Integration**
   - Use version pinning for stability
   - Consider using Git submodules for tight integration
   - Maintain clear dependency documentation

## Backlinks

- [[codebase-review]]
- [[systemPatterns]]
- [[techContext]]
