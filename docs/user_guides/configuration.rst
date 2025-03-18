Configuration Guide
=================

This guide explains how to configure The AIchemist Codex to suit your specific requirements.

Configuration File
-----------------

The AIchemist Codex uses a YAML configuration file located at:

* **Windows**: `%APPDATA%\AIchemist\config.yaml`
* **macOS**: `~/Library/Application Support/AIchemist/config.yaml`
* **Linux**: `~/.config/aichemist/config.yaml`

You can also specify a custom configuration file using the `--config` flag:

.. code-block:: bash

   aichemist --config /path/to/custom/config.yaml

Configuration Options
-------------------

General Settings
~~~~~~~~~~~~~~

.. code-block:: yaml

   general:
     log_level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
     temp_dir: /path/to/temp/directory
     cache_enabled: true
     cache_dir: /path/to/cache/directory
     max_cache_size_mb: 1024

Storage Settings
~~~~~~~~~~~~~~

.. code-block:: yaml

   storage:
     type: local  # local, s3, azure, gcp
     local:
       root_dir: /path/to/storage/directory
     s3:
       bucket: my-aichemist-bucket
       region: us-west-2
       access_key: YOUR_ACCESS_KEY
       secret_key: YOUR_SECRET_KEY

Search Settings
~~~~~~~~~~~~~

.. code-block:: yaml

   search:
     default_provider: vector  # vector, text, regex
     vector:
       model: sentence-transformers/all-mpnet-base-v2
       similarity_threshold: 0.75
       max_results: 20
     text:
       case_sensitive: false
       whole_words_only: true
     regex:
       ignore_case: true
       multiline: true

AI Settings
~~~~~~~~~

.. code-block:: yaml

   ai:
     embedding_model: sentence-transformers/all-mpnet-base-v2
     clustering_algorithm: hdbscan
     tag_suggestion_threshold: 0.85
     relationship_confidence_threshold: 0.7

Notification Settings
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   notifications:
     enabled: true
     channels:
       - type: email
         server: smtp.example.com
         port: 587
         username: user@example.com
         password: YOUR_PASSWORD
         recipients:
           - admin@example.com
       - type: webhook
         url: https://hooks.slack.com/services/YOUR_WEBHOOK_URL
         format: json

Environment Variables
-------------------

You can also use environment variables to override configuration settings. Environment variables should be prefixed with `AICHEMIST_`:

.. code-block:: bash

   # Example environment variables
   AICHEMIST_LOG_LEVEL=DEBUG
   AICHEMIST_STORAGE_TYPE=s3
   AICHEMIST_S3_BUCKET=my-bucket
   AICHEMIST_EMBEDDING_MODEL=openai/text-embedding-ada-002

Configuration Profiles
--------------------

You can define multiple configuration profiles for different use cases:

.. code-block:: yaml

   profiles:
     default:
       # Default settings here
     dev:
       # Development settings here
     production:
       # Production settings here

To use a specific profile:

.. code-block:: bash

   aichemist --profile production

Configuration Validation
----------------------

To validate your configuration without running the application:

.. code-block:: bash

   aichemist config validate

This will check your configuration for errors and provide helpful messages for any issues found.