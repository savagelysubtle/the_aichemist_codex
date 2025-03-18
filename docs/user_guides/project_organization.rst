Project Organization
===================

This guide explains how to effectively organize your projects in The AIchemist Codex.

Project Structure
---------------

The AIchemist Codex uses a standardized project structure to organize files, metadata, and search indices. Understanding this structure helps you manage your projects more effectively.

Basic Project Structure
~~~~~~~~~~~~~~~~~~~~

When you initialize a project with `aichemist init`, the following directory structure is created:

.. code-block:: text

   my_project/
   ├── .aichemist/           # Configuration and metadata directory
   │   ├── config.yaml       # Project-specific configuration
   │   ├── indices/          # Search indices
   │   ├── metadata/         # Metadata for processed files
   │   ├── tags/             # Tag definitions and assignments
   │   └── relationships/    # File relationship data
   ├── content/              # Default content directory
   └── output/               # Default output directory

You can customize this structure in your configuration.

Setting Up a New Project
----------------------

Basic Project Setup
~~~~~~~~~~~~~~~~

To create a new project:

.. code-block:: bash

   # Create a directory for your project
   mkdir my_project
   cd my_project

   # Initialize the project
   aichemist init

   # Customize project configuration
   aichemist config edit

Custom Project Setup
~~~~~~~~~~~~~~~~~

You can customize your project during initialization:

.. code-block:: bash

   # Initialize with custom content and output directories
   aichemist init --content-dir ./documents --output-dir ./processed

   # Initialize with a specific configuration template
   aichemist init --template research

   # Initialize with specific features enabled
   aichemist init --features "search,tagging,relationships"

Project Configuration
-------------------

Each project has its own configuration file located at `.aichemist/config.yaml`. You can edit this directly or use the config commands:

.. code-block:: bash

   # Edit the configuration
   aichemist config edit

   # Update specific configuration values
   aichemist config set search.default_provider vector
   aichemist config set storage.type local

   # View current configuration
   aichemist config show

Key configuration sections:

* **General**: Basic project settings
* **Content**: Content directory and processing options
* **Search**: Search providers and settings
* **Tagging**: Tagging behavior and auto-tagging settings
* **Relationships**: Relationship detection settings
* **Output**: Output directories and formatting options

Managing Multiple Projects
-----------------------

You can work with multiple projects simultaneously:

.. code-block:: bash

   # Specify the project directory in commands
   aichemist --project-dir /path/to/project1 search "query"
   aichemist --project-dir /path/to/project2 process

   # Set a default project
   aichemist config --global set default_project /path/to/my_main_project

   # List configured projects
   aichemist projects list

   # Switch between projects
   aichemist projects switch project2

Project Templates
---------------

The AIchemist Codex includes several project templates for common use cases:

.. code-block:: bash

   # List available templates
   aichemist templates list

   # Create a project from a template
   aichemist init --template code_repository
   aichemist init --template documentation
   aichemist init --template research_papers

   # Create your own template
   aichemist templates create my_template --from-project /path/to/existing_project

Common templates include:

* **default**: Standard project with all features enabled
* **code_repository**: Optimized for source code analysis
* **documentation**: Focused on documentation management
* **research_papers**: Designed for academic paper analysis
* **data_analysis**: For data-heavy projects with dataset management

Best Practices for Project Organization
------------------------------------

Directory Structure
~~~~~~~~~~~~~~~~

* **Organize by Purpose**: Group files by their purpose or domain
* **Use Consistent Naming**: Adopt a consistent naming convention
* **Limit Directory Depth**: Avoid deeply nested directories
* **Separate Source and Generated Content**: Keep original and generated content separate

.. code-block:: text

   my_project/
   ├── content/
   │   ├── source_code/       # Original source code
   │   ├── documentation/     # Documentation files
   │   ├── datasets/          # Data files
   │   └── references/        # Reference materials
   └── output/
       ├── reports/           # Generated reports
       ├── visualizations/    # Generated visualizations
       └── exports/           # Exported data

Content Management
~~~~~~~~~~~~~~~

* **Batch Processing**: Process related files together
* **Use Meaningful Tags**: Tag files with descriptive, meaningful tags
* **Track Relationships**: Use relationship tracking for related files
* **Version Important Files**: Use the versioning features for critical files

Scaling to Larger Projects
------------------------

For larger projects:

1. **Use Selective Processing**: Only process the files you need
2. **Enable Caching**: Make sure caching is enabled for better performance
3. **Use Efficient Search Providers**: Configure the right search providers for your data
4. **Implement Batch Operations**: Use batch commands for bulk operations
5. **Consider Distributed Setup**: For very large projects, set up distributed processing

.. code-block:: bash

   # Enable selective processing
   aichemist config set processing.selective true

   # Configure caching
   aichemist config set cache.enabled true
   aichemist config set cache.max_size_mb 2048

   # Batch processing
   aichemist process --batch-size 100 --max-parallel 4

Collaboration on Projects
-----------------------

For team collaboration:

1. **Shared Configuration**: Use shared project templates
2. **Version Control Integration**: Store projects in version control
3. **Standardized Tags**: Establish team-wide tagging conventions
4. **Centralized Indices**: Set up shared search indices
5. **Export/Import Capabilities**: Use export/import for sharing analysis

.. code-block:: bash

   # Export project configuration
   aichemist export --config --output project_config.zip

   # Export tags and relationships
   aichemist export --tags --relationships --output project_metadata.zip

   # Import into another project
   aichemist import --input project_metadata.zip