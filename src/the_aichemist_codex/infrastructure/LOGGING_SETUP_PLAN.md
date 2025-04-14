# Plan: Centralized Logging Configuration in Infrastructure

This document outlines the plan to implement a centralized mechanism for configuring the application's logging system within the infrastructure layer.

## 1. Define Configuration Schema

-   **Goal:** Specify how logging settings will be defined in `settings.yaml`.
-   **Location:** Define structure under a top-level `logging:` key in `settings.yaml`.
-   **Schema:**
    ```yaml
    logging:
      level: "INFO"  # Default overall level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      date_format: "%Y-%m-%d %H:%M:%S" # Optional: Define date format

      file:
        enable: true
        # Path relative to data_dir or absolute. Use DirectoryManager.
        path: "logs/app.log"
        level: "DEBUG" # Optional: Override level for file handler
        rotation:
          enable: true
          max_bytes: 10485760 # 10 MB
          backup_count: 5

      console:
        enable: true
        level: "INFO" # Optional: Override level for console handler
    ```
-   **Action:** Document this schema (e.g., in `README.md` or dedicated config docs).

## 2. Create Logging Setup Module

-   **Goal:** Create a dedicated Python module for the setup logic.
-   **Action:** Create the file `src/the_aichemist_codex/infrastructure/logging_setup.py`.

## 3. Implement Setup Function

-   **Goal:** Write the Python code to configure the `logging` standard library.
-   **Location:** Inside `logging_setup.py`.
-   **Function Signature:** `def setup_logging(config_obj) -> None:`
-   **Logic:**
    -   Accept the loaded `infrastructure.config.config` object.
    -   Retrieve settings using `config_obj.get('logging', {})`, providing defaults.
    -   Use `logging.config.dictConfig` or manual configuration via `logging` module functions.
    -   Configure the root logger level.
    -   Create and configure handlers (`FileHandler`, `RotatingFileHandler`, `StreamHandler`) based on settings.
    -   Ensure log directory exists (potentially using `infrastructure.fs.directory.DirectoryManager`).
    -   Create and apply `logging.Formatter`.
    -   Add handlers to the root logger.
    -   Include basic error handling for configuration issues.

## 4. Integrate with Application Entry Point

-   **Goal:** Call the setup function when the application starts.
-   **Location:** In the main application entry point (e.g., `main.py`, `app.py` - *outside* the infrastructure layer).
-   **Timing:** Call *after* configuration is loaded but *before* significant application logic runs.
-   **Example:**
    ```python
    # In main application setup
    from the_aichemist_codex.infrastructure.config import load_config # Assuming this exists
    from the_aichemist_codex.infrastructure.logging_setup import setup_logging

    config = load_config()
    setup_logging(config) # Initialize logging

    # ... rest of application startup
    ```

## 5. Usage within the Codebase

-   **Goal:** Ensure all parts of the application use the configured logging consistently.
-   **Method:** Continue using the standard `logging.getLogger(__name__)` pattern in all modules (domain, application, infrastructure).
-   **Benefit:** Modules get logger instances configured by the central setup without needing direct knowledge of the configuration details.

This approach centralizes logging *configuration* in the infrastructure layer while allowing the application's composition root to control the *initialization*, adhering to Clean Architecture principles.
