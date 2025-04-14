CLI Development
==============

This guide provides information on extending and customizing the Command Line Interface (CLI) for The AIchemist Codex.

Overview
--------

The AIchemist Codex CLI is built using the Click library and follows a modular architecture. The CLI is organized into command groups that correspond to different functionality areas of the application.

Architecture
-----------

The CLI follows the clean architecture principles of the main application:

* **Interfaces Layer**: CLI commands and groups (in ``interfaces/cli/``)
* **Application Layer**: Command handlers and use cases
* **Domain Layer**: Core business logic
* **Infrastructure Layer**: Implementation details

Adding New Commands
------------------

To add a new command to the CLI:

1. Identify the appropriate command group for your command
2. Create a new command function in the appropriate module
3. Use the Click decorators to define the command and its options
4. Implement the command logic
5. Register the command with its parent group

Example
~~~~~~~

.. code-block:: python

    import click
    from the_aichemist_codex.interfaces.cli.groups import file_group

    @file_group.command('analyze')
    @click.argument('file_path', type=click.Path(exists=True))
    @click.option('--depth', '-d', default=1, help='Analysis depth level')
    def analyze_file(file_path, depth):
        """Analyze a file and extract metadata."""
        # Command implementation here
        click.echo(f"Analyzing {file_path} with depth {depth}")

Testing CLI Commands
-------------------

CLI commands should be tested using the Click test runner:

.. code-block:: python

    from click.testing import CliRunner
    from the_aichemist_codex.interfaces.cli.commands import analyze_file

    def test_analyze_file():
        runner = CliRunner()
        result = runner.invoke(analyze_file, ['path/to/test/file', '--depth', '2'])
        assert result.exit_code == 0
        assert "Analyzing path/to/test/file with depth 2" in result.output

Best Practices
-------------

1. **Command Names**: Use clear, descriptive names for commands
2. **Documentation**: Provide detailed docstrings for all commands
3. **Error Handling**: Use appropriate error handling and exit codes
4. **Testing**: Write comprehensive tests for all CLI commands
5. **User Experience**: Consider the user experience when designing command interfaces

Advanced Topics
--------------

Custom Parameter Types
~~~~~~~~~~~~~~~~~~~~~

You can create custom parameter types for complex inputs:

.. code-block:: python

    class FileFormat(click.ParamType):
        name = 'format'

        def convert(self, value, param, ctx):
            valid_formats = ['json', 'yaml', 'xml']
            if value.lower() not in valid_formats:
                self.fail(f"Format must be one of: {', '.join(valid_formats)}")
            return value.lower()

    FORMAT_TYPE = FileFormat()

    @file_group.command('export')
    @click.argument('file_path', type=click.Path(exists=True))
    @click.option('--format', type=FORMAT_TYPE, default='json')
    def export_file(file_path, format):
        """Export a file in the specified format."""
        click.echo(f"Exporting {file_path} as {format}")

Command Groups
~~~~~~~~~~~~~

Organize related commands into groups:

.. code-block:: python

    @click.group()
    def metadata():
        """Metadata management commands."""
        pass

    @metadata.command('extract')
    @click.argument('file_path', type=click.Path(exists=True))
    def extract_metadata(file_path):
        """Extract metadata from a file."""
        click.echo(f"Extracting metadata from {file_path}")

    @metadata.command('apply')
    @click.argument('file_path', type=click.Path(exists=True))
    @click.argument('metadata_file', type=click.Path(exists=True))
    def apply_metadata(file_path, metadata_file):
        """Apply metadata to a file."""
        click.echo(f"Applying metadata from {metadata_file} to {file_path}")

    # Register the group with the main CLI
    from the_aichemist_codex.interfaces.cli.main import cli
    cli.add_command(metadata)
