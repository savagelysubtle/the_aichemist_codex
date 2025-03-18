Command Line Usage
=================

The AIchemist Codex provides a powerful command-line interface (CLI) that allows you to interact with all aspects of the system.

Basic Command Structure
---------------------

All commands follow this general structure:

.. code-block:: bash

   aichemist [command] [subcommand] [options] [arguments]

To get help on any command:

.. code-block:: bash

   # General help
   aichemist --help

   # Help for a specific command
   aichemist [command] --help

   # Help for a subcommand
   aichemist [command] [subcommand] --help

Global Options
------------

These options can be used with any command:

.. code-block:: bash

   # Specify config file
   aichemist --config /path/to/config.yaml [command]

   # Use a specific profile
   aichemist --profile development [command]

   # Set log level
   aichemist --log-level debug [command]

   # Set project directory
   aichemist --project-dir /path/to/project [command]

   # Output format (text, json, yaml)
   aichemist --output json [command]

Core Commands
-----------

Project Management
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Initialize a new project
   aichemist init [project_directory]

   # Initialize with a template
   aichemist init [project_directory] --template research

   # List available templates
   aichemist templates list

   # Set active project
   aichemist project set /path/to/project

   # List configured projects
   aichemist project list

File Operations
~~~~~~~~~~~~

.. code-block:: bash

   # Add files to the system
   aichemist add /path/to/file.txt

   # Add a directory recursively
   aichemist add /path/to/directory --recursive

   # Add with custom metadata
   aichemist add /path/to/file.txt --metadata "author=John Doe,status=draft"

   # Update files in the system
   aichemist update /path/to/file.txt

   # Remove files from the system
   aichemist remove /path/to/file.txt

Searching
~~~~~~~

.. code-block:: bash

   # Basic search
   aichemist search "quantum computing"

   # Specify search provider
   aichemist search "quantum computing" --provider vector

   # Limit results
   aichemist search "quantum computing" --limit 5

   # Filter by file type
   aichemist search "quantum computing" --file-type pdf,docx

   # Search in specific directory
   aichemist search "quantum computing" --directory /path/to/documents

   # Search with metadata
   aichemist search "quantum computing" --metadata "status=published,author=John Doe"

   # Format search results
   aichemist search "quantum computing" --format markdown

Tagging Commands
~~~~~~~~~~~~~

.. code-block:: bash

   # Add tags to files
   aichemist tag add --file /path/to/file.txt --tags "ai,research,draft"

   # Remove tags
   aichemist tag remove --file /path/to/file.txt --tags "draft"

   # List tags for a file
   aichemist tag list --file /path/to/file.txt

   # Find files with specific tags
   aichemist tag find --tags "ai,research"

   # Get tag suggestions
   aichemist tag suggest --file /path/to/file.txt

   # Apply suggested tags
   aichemist tag suggest --file /path/to/file.txt --apply

Metadata Commands
~~~~~~~~~~~~~~

.. code-block:: bash

   # View metadata
   aichemist metadata show --file /path/to/file.txt

   # Add/update metadata
   aichemist metadata set --file /path/to/file.txt --field "author" --value "John Doe"

   # Remove metadata field
   aichemist metadata remove --file /path/to/file.txt --field "draft_version"

   # Extract metadata automatically
   aichemist metadata extract --file /path/to/file.pdf

   # Apply metadata template
   aichemist metadata-template apply --template "document" --file /path/to/file.txt

Analysis Commands
~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate summary
   aichemist analyze summary --file /path/to/file.txt

   # Extract keywords
   aichemist analyze keywords --file /path/to/file.txt

   # Identify entities
   aichemist analyze entities --file /path/to/file.txt

   # Generate topics
   aichemist analyze topics --file /path/to/file.txt

   # Sentiment analysis
   aichemist analyze sentiment --file /path/to/file.txt

   # Batch analysis
   aichemist analyze all --file /path/to/file.txt

Relationship Commands
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Find related files
   aichemist relationships find --file /path/to/file.txt

   # Add manual relationship
   aichemist relationships add --source /path/to/file1.txt --target /path/to/file2.txt --type "references" --strength 0.8

   # List relationships
   aichemist relationships list --file /path/to/file.txt

   # Remove relationship
   aichemist relationships remove --source /path/to/file1.txt --target /path/to/file2.txt

Content Processing
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Index content
   aichemist index /path/to/directory

   # Process content
   aichemist process /path/to/file.txt

   # Reindex all content
   aichemist reindex

   # Check index status
   aichemist index status

Output Commands
~~~~~~~~~~~~

.. code-block:: bash

   # Generate formatted output
   aichemist output --files /path/to/file1.txt,/path/to/file2.txt --format markdown

   # Generate with template
   aichemist output --files /path/to/file1.txt --template report

   # Export to file
   aichemist output --files /path/to/file1.txt --format html --output report.html

   # List available templates
   aichemist output templates

Data Management
~~~~~~~~~~~~

.. code-block:: bash

   # Export data
   aichemist export --directory /path/to/export

   # Import data
   aichemist import --file /path/to/import.zip

   # Backup system
   aichemist backup --directory /path/to/backup

   # Restore from backup
   aichemist restore --file /path/to/backup.zip

Advanced Command Line Features
----------------------------

Chaining Commands
~~~~~~~~~~~~~~

The AIchemist Codex supports command chaining with pipes:

.. code-block:: bash

   # Search and tag results
   aichemist search "quantum computing" | aichemist tag add --tags "physics,research"

   # Search, analyze and output
   aichemist search "quantum computing" | aichemist analyze summary | aichemist output --format markdown

Batch Processing
~~~~~~~~~~~~~

Process multiple files using glob patterns:

.. code-block:: bash

   # Add all PDF files
   aichemist add "/path/to/documents/*.pdf"

   # Tag all documents in a directory
   aichemist tag add --files "/path/to/documents/*" --tags "archived"

   # Extract metadata from all PDFs
   aichemist metadata extract --files "/path/to/documents/*.pdf"

Using Config Files for Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Save complex commands as configuration profiles:

.. code-block:: bash

   # Save current command as profile
   aichemist search "quantum computing" --provider vector --metadata "status=published" --save-profile quantum-search

   # Use saved profile
   aichemist run-profile quantum-search

   # List saved profiles
   aichemist profiles list

Scripting and Automation
---------------------

Shell Scripting
~~~~~~~~~~~~

Example shell script for batch processing:

.. code-block:: bash

   #!/bin/bash

   # Process new documents
   for file in /path/to/new/documents/*; do
     aichemist add "$file" --extract-metadata --suggest-tags --apply
   done

   # Generate reports
   aichemist search "quarterly report" --metadata "department=Finance" | aichemist output --format pdf --output quarterly-finance.pdf

Scheduled Tasks
~~~~~~~~~~~~

Example crontab entries:

.. code-block:: bash

   # Daily indexing at midnight
   0 0 * * * /usr/local/bin/aichemist index /path/to/documents

   # Weekly backup on Sunday at 1 AM
   0 1 * * 0 /usr/local/bin/aichemist backup --directory /path/to/backups

   # Monthly report generation on the 1st at 2 AM
   0 2 1 * * /usr/local/bin/aichemist search "monthly report" | /usr/local/bin/aichemist output --format pdf --output /path/to/reports/monthly-$(date +\%Y-\%m).pdf

Command Line Tips and Tricks
--------------------------

Using Shell Aliases
~~~~~~~~~~~~~~~

Add these to your `.bashrc` or `.zshrc`:

.. code-block:: bash

   # Alias for quick search
   alias ais='aichemist search'

   # Alias for tagging
   alias ait='aichemist tag add --tags'

   # Alias for metadata viewing
   alias aim='aichemist metadata show --file'

Tab Completion
~~~~~~~~~~~

Enable tab completion:

.. code-block:: bash

   # For Bash
   aichemist completion bash > ~/.aichemist-completion.bash
   echo "source ~/.aichemist-completion.bash" >> ~/.bashrc

   # For Zsh
   aichemist completion zsh > ~/.aichemist-completion.zsh
   echo "source ~/.aichemist-completion.zsh" >> ~/.zshrc

Debugging Commands
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Debug mode
   aichemist --debug search "quantum computing"

   # Trace mode for detailed logging
   aichemist --trace search "quantum computing"

   # Dry run (doesn't execute, just shows what would happen)
   aichemist --dry-run add /path/to/files/*.pdf