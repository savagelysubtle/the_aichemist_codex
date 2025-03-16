Configuration
=============

This guide covers the configuration options for The Aichemist Codex.

Configuration File
-----------------

The Aichemist Codex uses a YAML configuration file located at `~/.aichemist/config.yaml` by default. You can specify a different configuration file using the `--config` command-line option.

Basic Configuration Example
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Basic configuration
   data_directory: ~/.aichemist/data
   cache_directory: ~/.aichemist/cache
   log_level: INFO

   # Database configuration
   database:
     type: sqlite
     path: ~/.aichemist/db/aichemist.db

   # Processing settings
   processing:
     max_threads: 4
     max_file_size_mb: 100
     timeout_seconds: 60

Tagging Configuration
--------------------

The tagging system can be configured with various options to customize its behavior:

.. code-block:: yaml

   # Tagging configuration
   tagging:
     # Database path for tag storage
     db_path: ~/.aichemist/db/tags.db

     # Tag suggestion settings
     suggestion:
       min_confidence: 0.6
       max_suggestions: 10
       enable_ml_classifier: true
       enable_collaborative: true
       enable_content_based: true

     # Classifier settings
     classifier:
       model_directory: ~/.aichemist/models
       training_data_limit: 1000
       retrain_threshold: 100

     # Auto-tagging settings
     auto_tagging:
       enabled: true
       min_confidence: 0.8
       max_tags_per_file: 10

Environment Variables
--------------------

You can also configure The Aichemist Codex using environment variables. Environment variables take precedence over configuration file settings.

.. code-block:: bash

   # Set data directory
   export AICHEMIST_DATA_DIR=/path/to/data

   # Configure tagging
   export AICHEMIST_TAGGING_DB_PATH=/path/to/tags.db
   export AICHEMIST_TAGGING_MIN_CONFIDENCE=0.7
   export AICHEMIST_TAGGING_ENABLE_ML=true

Programmatic Configuration
-------------------------

When using The Aichemist Codex as a library, you can pass configuration options directly:

.. code-block:: python

   from backend.src.tagging import TagManager, TagSuggester
   from pathlib import Path

   # Configure tag manager
   tag_manager = TagManager(
       db_path=Path("/custom/path/to/tags.db")
   )

   # Configure suggester with custom settings
   suggester = TagSuggester(
       tag_manager=tag_manager,
       model_dir=Path("/custom/path/to/models")
   )

   # Use with custom confidence threshold
   suggestions = await suggester.suggest_tags(
       file_metadata=metadata,
       min_confidence=0.75,
       max_suggestions=15
   )