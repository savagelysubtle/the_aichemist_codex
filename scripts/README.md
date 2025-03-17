# The Aichemist Codex: Utility Scripts

This directory contains utility scripts for The Aichemist Codex project that
help with development, maintenance, and code quality tasks.

## Available Scripts

### Code Quality Tools

- **[code_quality.py](./code_quality.py)**: Automates code formatting, linting,
  and type checking

  ```bash
  # Run all checks without fixing
  python scripts/code_quality.py --all

  # Format code and fix issues
  python scripts/code_quality.py --format --fix

  # Run linting with automatic fixes
  python scripts/code_quality.py --lint --fix

  # Check types
  python scripts/code_quality.py --typecheck

  # Specify a different path
  python scripts/code_quality.py --all --path tests/
  ```

## Adding New Scripts

When adding new scripts to this directory:

1. Make sure to add proper documentation with examples
2. Include shebang line for executable scripts: `#!/usr/bin/env python3`
3. Add proper docstrings explaining the script's purpose
4. Document the script in this README
5. Ensure the script has appropriate error handling

## Making Scripts Executable

For Unix-like systems, make scripts executable:

```bash
chmod +x scripts/code_quality.py
```

Then you can run them directly:

```bash
./scripts/code_quality.py --all
```

## Best Practices

- Keep scripts focused on a single responsibility
- Implement proper argument parsing and help text
- Include error handling and meaningful exit codes
- Document expected inputs and outputs
- Add verbose/quiet modes when appropriate
- Make scripts cross-platform when possible

## Related Documentation

- [Development Guide](../DEVELOPMENT.md) - General development workflow
- [Code Review](../docs/code_review.md) - Code review findings and
  recommendations
- [Improvement Tracker](../docs/improvement_tracker.md) - Tracking improvement
  tasks
