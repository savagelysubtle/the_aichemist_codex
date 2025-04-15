# The AIChemist Codex - Infrastructure Layer

This directory (`src/the_aichemist_codex/infrastructure`) contains the infrastructure layer for The Aichemist Codex application, following Clean Architecture principles.

## Purpose

The infrastructure layer is responsible for implementing the technical details and handling interactions with external systems and frameworks. It provides concrete implementations for interfaces defined in higher layers (Application, Domain) and encapsulates dependencies on specific technologies.

**Key Responsibilities:**

*   **Configuration Management:** Loading settings from files (`settings.yaml`), handling secure configuration (`secure_config.enc`), and providing unified access (`config` object). See `infrastructure.config`.
*   **Asynchronous I/O:** Providing utilities for non-blocking file system operations (`AsyncFileIO`) and database interactions (e.g., `AsyncSQL` for SQLite). See `infrastructure.utils.io`.
*   **Caching:** Implementing caching strategies (in-memory LRU, disk-based TTL). See `infrastructure.utils.cache`.
*   **Concurrency:** Offering tools for managing threads, tasks, rate limiting, and batch processing. See `infrastructure.utils.concurrency`.
*   **Platform-Specific Implementations:** Housing code tailored to specific operating systems or environments. See `infrastructure.platforms`.
*   **Code Analysis:** Providing services or utilities related to analyzing source code artifacts. See `infrastructure.analysis`.
*   **Error Handling:** Defining base infrastructure-related exceptions. See `infrastructure.utils.errors`.
*   **Common Utilities:** Including cross-cutting infrastructure concerns like safety checks and pattern matching. See `infrastructure.utils.common`.

## Structure

*   `config/`: Handles loading, security, and access to configuration.
*   `utils/`: Contains various low-level utility modules (IO, concurrency, cache, etc.).
    *   *Note:* Contains some code duplication with files directly under `utils/` vs. subdirectories. Prefer implementations within subdirectories (`cache/`, `concurrency/`, `io/` etc.). Cleanup is planned.
*   `platforms/`: Holds platform-specific code (e.g., Windows integrations).
*   `analysis/`: Contains code analysis related infrastructure components.
*   `.cursor/`: Contains AI assistant configuration and rules specific to this layer.

## Key Dependencies

This layer relies on several external libraries for its functionality. Key dependencies include:

*   `aiofiles`: Asynchronous file operations.
*   `aiosqlite`: Asynchronous SQLite access.
*   `platformdirs`: Cross-platform directory determination (for config/data).
*   `PyYAML`: Loading YAML configuration files.
*   `cryptography`: Handling encryption for secure configuration.
*   `pywin32` (Optional, Windows only): For specific file permissions.

See `pyproject.toml` for the full list and version specifications.

## Working in this Layer (Context for Humans & AI)

*   **Dependency Rule:** Code within this layer **must not** import directly from the `domain` or `application` layers. The only exception is implementing an interface explicitly defined in those higher layers. Dependencies flow inwards.
*   **Focus:** Concentrate on the *how* – the concrete technical implementation details using specific libraries and tools. Avoid implementing business logic or application-specific workflows here.
*   **Configuration:** Access all configuration via the singleton `infrastructure.config.config` object. Understand that it merges default, user, and secure settings.
*   **Entry Point:** This layer does not have its own `main.py` entry point. It provides components used by the main application entry point, likely located elsewhere.
*   **AI Assistance:** Use the rules defined in `.cursor/rules/` to guide AI interactions, ensuring focus remains on infrastructure concerns.

## Usage

Components from this layer are typically imported and used by the Application layer or directly by the main application entry point to bootstrap services and configurations.
