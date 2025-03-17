# The Aichemist Codex - Phase 1 Detailed Implementation Plan

## Phase 1: Foundation Restructuring

This document provides a detailed implementation plan for the immediate focus
areas in Phase 1 of the project restructuring. The goal is to establish a solid
foundation for future development by addressing fundamental structural elements.

---

## 1. Adopt `src` Layout

### Overview

Converting to a src-layout is a significant architectural change that will
impact imports throughout the codebase. This structure provides better
packaging, isolation, and ensures the code works the same way in development and
after installation.

### Detailed Implementation Steps

#### 1.1. Analysis and Planning (Week 1, Days 1-2)

- [x] **Map current project structure**:
  - Create a visual dependency graph using `pydeps` or similar tools
  - Document all top-level modules and their relationships
  - Identify which modules are part of the public API
- [x] **Identify potential breaking changes**:
  - List all absolute imports that will need updating
  - Find usages of `__file__` or relative paths that might break
  - Note any tests that might be affected by structural changes

#### 1.2. Create New Directory Structure (Week 1, Day 3)

- [x] **Set up the skeleton structure**:
  ```
  the_aichemist_codex/
  ├── src/
  │   └── the_aichemist_codex/
  │       ├── __init__.py
  │       ├── backend/
  │       ├── middleware/
  │       └── cli/
  ├── tests/
  ├── docs/
  ├── pyproject.toml
  └── README.md
  ```
- [x] **Create empty `__init__.py` files** in all directories to mark them as
      packages
- [ ] **Add version information** to the root `__init__.py`

#### 1.3. Incremental Module Migration (Week 1, Day 4 - Week 2, Day 3)

- [x] **Migrate independent modules first**:

  - Start with modules that have few dependencies (utils, constants, etc.)
  - Move each file to its corresponding location in the new structure
  - Update imports in the moved files to use absolute paths
  - Run unit tests after each module migration

- [x] **Define migration order based on dependencies**:

  1. Core utilities and helpers
  2. Data models and domain entities
  3. Services and business logic
  4. CLI components and user interfaces

- [x] **For each module**:
  - Copy to new location (don't delete originals yet)
  - Update imports to use the new structure
  - Run tests to verify functionality
  - Update documentation references if needed

#### 1.4. Update Import Strategy (Throughout migration)

- [x] **Implement the following import pattern across the codebase**:

  ```python
  # Before
  from file_manager.io_utils import read_file

  # After
  from the_aichemist_codex.backend.file_manager.io_utils import read_file
  ```

- [ ] **Create backwards compatibility imports if needed**:
  ```python
  # In old location, to maintain compatibility during transition
  from the_aichemist_codex.backend.file_manager.io_utils import read_file
  ```

#### 1.5. Update Package Configuration (Week 2, Day 4)

- [x] **Create or update `pyproject.toml` for src layout**:

  ```toml
  [build-system]
  requires = ["setuptools>=61.0", "wheel"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "the_aichemist_codex"
  version = "0.1.0"
  description = "The Aichemist Codex - Intelligent file management system"
  requires-python = ">=3.10"
  # Add more metadata here

  [tool.setuptools]
  package-dir = {"" = "src"}
  ```

#### 1.6. Test and Verify (Week 2, Day 5)

- [ ] **Develop comprehensive tests for core functionality**
- [ ] **Run full test suite against new structure**
- [ ] **Test installation and import mechanics**:
  - Install the package in development mode: `pip install -e .`
  - Verify imports work both in and outside of the project directory
- [ ] **Fix any remaining issues** discovered during testing

#### 1.7. Remove Legacy Code (After successful testing)

- [ ] **Once the new structure is verified, incrementally remove original
      files**
- [ ] **Update documentation to reflect the new structure**

### Potential Challenges

- **Circular imports** may become more apparent or problematic
- **IDE support** might need reconfiguration (update `.vscode` settings, etc.)
- **Third-party tool configurations** may need updating
- **Package resources access** may break if using `__file__` for path resolution

### Success Criteria

- All tests pass with the new directory structure
- Code can be developed, tested, and installed from the new structure
- Clear import paths that follow a consistent pattern
- Documentation updated to reflect new structure

---

## 2. Modernize Package Management

### Overview

Transitioning from `requirements.txt` to modern Python packaging tools will
improve dependency management, make installation more reliable, and better
separate development from production dependencies.

### Detailed Implementation Steps

#### 2.1. Evaluate and Select Tools (Week 3, Day 1)

- [x] **Assess package management tools**:

  - Compare Poetry, PDM, and pip-tools based on project needs
  - Consider factors like lock file support, virtual environment management, and
    publishing workflow
  - Document findings and make a decision

  | Tool      | Lock Files | venv Management | Build Support | User-Friendliness |
  | --------- | ---------- | --------------- | ------------- | ----------------- |
  | Poetry    | Yes        | Integrated      | Yes           | High              |
  | PDM       | Yes        | Integrated      | Yes           | Medium            |
  | pip-tools | Yes        | Manual          | No            | Low               |

#### 2.2. Setup Initial Configuration (Week 3, Day 2)

- [x] **Create a comprehensive `pyproject.toml`**:

  ```toml
  [build-system]
  requires = ["setuptools>=61.0", "wheel"]
  build-backend = "setuptools.build_meta"

  [project]
  name = "the_aichemist_codex"
  version = "0.1.0"
  description = "The Aichemist Codex - Intelligent file management system"
  readme = "README.md"
  requires-python = ">=3.10"
  license = {text = "MIT"}
  authors = [
      {name = "Your Name", email = "your.email@example.com"},
  ]
  dependencies = [
      # Core dependencies
      "click>=8.1.3",
      "pyyaml>=6.0",
      "rich>=13.0.0",
      # Add other dependencies
  ]

  [project.optional-dependencies]
  dev = [
      "pytest>=7.0.0",
      "mypy>=1.0.0",
      "ruff>=0.0.230",
  ]
  docs = [
      "sphinx>=6.0.0",
      "sphinx-rtd-theme>=1.0.0",
  ]

  [project.scripts]
  aichemist = "the_aichemist_codex.cli:main"

  [tool.ruff]
  line-length = 88
  target-version = "py310"
  select = ["E", "F", "I"]

  [tool.mypy]
  python_version = "3.10"
  warn_return_any = true
  disallow_untyped_defs = true
  ```

#### 2.3. Migrate Dependencies (Week 3, Day 3)

- [x] **Analyze current requirements**:

  - Extract dependencies from existing `requirements.txt`
  - Categorize dependencies (core, dev, optional)
  - Identify version constraints and compatibility issues

- [ ] **Generate lock files**:
  - If using Poetry: `poetry lock`
  - If using PDM: `pdm lock`
  - If using pip-tools: `pip-compile pyproject.toml`

#### 2.4. Update Development Workflow (Week 3, Day 4)

- [ ] **Create documentation** on new workflow for developers:

  - Installation instructions using the new tool
  - How to add new dependencies
  - How to update dependencies
  - How to work with different dependency groups

- [ ] **Create helper scripts** for common tasks:
  ```
  scripts/
  ├── setup-dev.ps1      # Setup development environment
  ├── update-deps.ps1    # Update dependencies
  └── build-package.ps1  # Build distributable package
  ```

#### 2.5. CI/CD Integration (Week 3, Day 5)

- [ ] **Update CI/CD pipelines** to use the new dependency management:
  - Update build scripts
  - Configure caching for dependencies
  - Setup automatic dependency validation
  - Add dependency security scanning

#### 2.6. Test Installation Methods (Week 4, Day 1)

- [ ] **Verify installation works through multiple methods**:
  - Direct from repository: `pip install -e .`
  - From wheel package
  - With specific extras: `pip install ".[dev]"`

### Potential Challenges

- **Learning curve** for developers not familiar with modern packaging
- **Dependency conflicts** might arise when specifying version ranges
- **Transition period** where both old and new systems might be used
- **Integration with existing tools** that expect traditional requirements files

### Success Criteria

- Clear separation of core, development, and optional dependencies
- Reproducible builds through lock files
- Installation works reliably across different environments
- Development workflow is well-documented and streamlined

---

## 3. Standardize Data Directory

### Overview

Implementing a consistent approach to data directory management will resolve the
current confusion about storage locations and provide a solid foundation for
file-related operations.

### Detailed Implementation Steps

#### 3.1. Design Data Directory Structure (Week 4, Day 2)

- [x] **Define the standard data directory hierarchy**:

  ```
  data/
  ├── cache/          # Temporary cached data
  ├── logs/           # Application logs
  ├── versions/       # Version history data
  ├── exports/        # Exported files
  ├── backup/         # Backup data
  ├── trash/          # Recently deleted files
  ├── rollback.json   # Rollback information
  └── version_metadata.json  # Version tracking metadata
  ```

- [x] **Document the purpose and lifecycle** of each subdirectory
- [x] **Define access patterns** for different components of the system

#### 3.2. Implement Directory Resolver (Week 4, Day 3)

- [x] **Create a central `DirectoryManager` class**:

  ```python
  from pathlib import Path
  from typing import Optional
  import os

  class DirectoryManager:
      """Central manager for data directory access."""

      def __init__(self, base_dir: Optional[Path] = None):
          """Initialize with optional base directory override."""
          self.base_dir = base_dir or self._get_default_data_dir()
          self._ensure_directories_exist()

      def _get_default_data_dir(self) -> Path:
          """Get the default data directory based on env vars or system location."""
          # Check for environment variable override
          if env_dir := os.environ.get("AICHEMIST_DATA_DIR"):
              return Path(env_dir)

          # Use standard OS-specific data directories
          if os.name == "nt":  # Windows
              return Path(os.environ["APPDATA"]) / "AichemistCodex"
          else:  # Linux/Mac
              return Path.home() / ".aichemist"

      def _ensure_directories_exist(self) -> None:
          """Create all required directories if they don't exist."""
          for subdir in ["cache", "logs", "versions", "exports", "backup", "trash"]:
              (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

      def get_dir(self, dir_type: str) -> Path:
          """Get a specific subdirectory path."""
          if dir_type not in ["cache", "logs", "versions", "exports", "backup", "trash"]:
              raise ValueError(f"Unknown directory type: {dir_type}")
          return self.base_dir / dir_type

      def get_file_path(self, filename: str) -> Path:
          """Get path for a file in the base data directory."""
          return self.base_dir / filename
  ```

#### 3.3. Update Settings Module (Week 4, Day 4)

- [x] **Integrate DirectoryManager with settings**:

  ```python
  # settings.py
  from pathlib import Path
  from typing import Optional

  from .directory_manager import DirectoryManager

  class Settings:
      """Global application settings."""

      def __init__(self, data_dir: Optional[Path] = None):
          self.dirs = DirectoryManager(data_dir)
          # Other settings initialization

      @classmethod
      def from_config_file(cls, config_path: Path) -> "Settings":
          """Initialize settings from a configuration file."""
          # Load config
          # Extract data_dir if specified
          # Return new Settings instance

  # Global instance - can be overridden in tests
  settings = Settings()
  ```

#### 3.4. Update File Operations (Week 4, Day 5 - Week 5, Day 2)

- [x] **Identify all file-related operations in the codebase**:

  - Create a comprehensive list of modules that perform file I/O
  - Categorize operations by functionality (read, write, search, etc.)
  - Note any hard-coded paths or directory assumptions

- [x] **Refactor file operations to use the DirectoryManager**:

  ```python
  # Before
  data_file = Path("data/rollback.json")

  # After
  from the_aichemist_codex.settings import settings

  data_file = settings.dirs.get_file_path("rollback.json")
  ```

- [x] **Create utility functions for common operations**:

  ```python
  def get_log_file(name: str) -> Path:
      """Get a path to a log file with the given name."""
      return settings.dirs.get_dir("logs") / f"{name}.log"

  def get_cached_item(key: str) -> Optional[Path]:
      """Get a cached item if it exists."""
      path = settings.dirs.get_dir("cache") / key
      return path if path.exists() else None
  ```

#### 3.5. Add Environment Variable Support (Week 5, Day 3)

- [x] **Document environment variables** that control data location:

  - `AICHEMIST_DATA_DIR` - Override base data directory
  - `AICHEMIST_CACHE_DIR` - Override cache directory only
  - `AICHEMIST_LOG_LEVEL` - Set logging verbosity

- [x] **Implement environment variable parsing** in settings initialization
- [ ] **Create a default `.env` template** for development use

#### 3.6. Update CLI with Directory Management (Week 5, Day 4)

- [x] **Add CLI commands for directory management**:

  ```python
  @cli.command()
  def data_info():
      """Show information about data directories."""
      click.echo(f"Base data directory: {settings.dirs.base_dir}")
      # Show subdirectories and their sizes
      for subdir in ["cache", "logs", "versions", "exports", "backup", "trash"]:
          dir_path = settings.dirs.get_dir(subdir)
          click.echo(f"  {subdir}: {dir_path} ({get_dir_size(dir_path)} bytes)")

  @cli.command()
  @click.option("--force", is_flag=True, help="Force cleaning without confirmation")
  def clean_cache(force):
      """Clean the cache directory."""
      cache_dir = settings.dirs.get_dir("cache")
      # Implement cache cleaning logic
  ```

#### 3.7. Documentation (Week 5, Day 5)

- [ ] **Create comprehensive documentation** for the data directory system:
  - Directory structure and purpose
  - Configuration options
  - Environment variables
  - Best practices for accessing data files
  - Migration guide for developers

### Potential Challenges

- **Backward compatibility** with existing data storage
- **Migration of existing data** to the new structure
- **Cross-platform issues** with path handling
- **Permission issues** in different environments

### Success Criteria

- All file operations use the central directory manager
- Data storage locations are configurable via settings and environment variables
- Clear documentation of the data directory structure
- No hard-coded paths remaining in the codebase

---

## Implementation Timeline

### Weeks 1-2: Src Layout Migration

- **Week 1**: Analysis, planning, and initial structure creation
- **Week 2**: Module migration, import updates, and testing

### Week 3: Package Management Modernization

- **Days 1-2**: Tool selection and configuration setup
- **Days 3-5**: Dependency migration and workflow updates

### Weeks 4-5: Data Directory Standardization

- **Week 4**: Design, directory resolver, and settings integration
- **Week 5**: File operation updates, environment variable support, and
  documentation

### Week 6: Integration and Final Testing

- **Days 1-3**: Comprehensive testing of all Phase 1 components together
- **Days 4-5**: Address any remaining issues and prepare for Phase 2

## Risk Mitigation Strategies

1. **Create backups** before major structural changes
2. **Implement changes incrementally** with regular testing
3. **Maintain a parallel structure** during transition for critical components
4. **Document all changes** thoroughly to help team members adapt
5. **Develop comprehensive tests** before implementing changes
6. **Create rollback plans** for each major step

## Dependencies Between Tasks

- The `src` layout migration should be completed before comprehensive
  refactoring of imports in other tasks
- Package management modernization partially depends on the new directory
  structure
- Data directory standardization can proceed in parallel but will eventually
  need to integrate with the new import structure

## Success Metrics

- **Test pass rate**: All tests should continue to pass after changes
- **Import cleanliness**: No remaining relative imports or hard-coded paths
- **Documentation completeness**: All new systems are well-documented
- **Developer feedback**: Team members find the new structure intuitive and
  helpful
