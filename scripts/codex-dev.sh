#!/bin/bash
# AIchemist Codex Development Helper Script
# This script provides shortcuts for common UV commands used in development

set -e

# Detect platform for proper command syntax
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
else
    PLATFORM="unix"
fi

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "Error: UV is not installed. Please install it with 'pip install uv'"
    exit 1
fi

# Check if we're in the project root (look for pyproject.toml)
if [ ! -f "pyproject.toml" ]; then
    echo "Error: You must run this script from the project root directory (where pyproject.toml is located)"
    exit 1
fi

# Function to display help
function show_help {
    echo "AIchemist Codex Development Helper"
    echo ""
    echo "Usage: ./scripts/codex-dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup         - Create venv and install all dependencies"
    echo "  sync          - Sync dependencies from lockfile"
    echo "  test          - Run all tests"
    echo "  test-unit     - Run unit tests only"
    echo "  test-file     - Run tests for a specific file (requires FILE=path)"
    echo "  lint          - Run linting checks"
    echo "  format        - Format code with ruff and black"
    echo "  codex         - Run the codex CLI"
    echo "  search        - Run the search tool"
    echo "  docs          - Build documentation"
    echo "  clean         - Clean temporary files and caches"
    echo "  update-deps   - Update dependencies and rebuild lockfile"
    echo "  help          - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/codex-dev.sh setup"
    echo "  ./scripts/codex-dev.sh test"
    echo "  FILE=tests/domain/entities/test_code_artifact.py ./scripts/codex-dev.sh test-file"
    echo "  ./scripts/codex-dev.sh codex analyze path/to/file"
    echo ""
}

# Command functions
function setup {
    echo "Setting up development environment..."
    uv venv
    if [ "$PLATFORM" == "windows" ]; then
        echo "Activate with: .venv\\Scripts\\activate"
    else
        echo "Activate with: source .venv/bin/activate"
    fi
    uv sync
    uv pip install -e .
    echo "Setup complete!"
}

function sync_deps {
    echo "Syncing dependencies..."
    uv sync
    echo "Dependencies synced!"
}

function run_tests {
    echo "Running tests..."
    uv run pytest -xvs
}

function run_unit_tests {
    echo "Running unit tests only..."
    uv run pytest -xvs -m "unit"
}

function run_test_file {
    if [ -z "$FILE" ]; then
        echo "Error: Please specify a file with FILE=path/to/test.py"
        exit 1
    fi
    echo "Running tests for $FILE..."
    uv run pytest -xvs "$FILE"
}

function run_lint {
    echo "Running linters..."
    uv run ruff check .
    uv run mypy src
}

function run_format {
    echo "Formatting code..."
    uv run ruff format .
    uv run isort .
}

function run_codex {
    echo "Running codex CLI..."
    uv run codex "${@:1}"
}

function run_search {
    echo "Running search tool..."
    uv run search-tool "${@:1}"
}

function build_docs {
    echo "Building documentation..."
    uv run docs build
}

function clean {
    echo "Cleaning temporary files and caches..."
    rm -rf .ruff_cache
    rm -rf .mypy_cache
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf dist
    rm -rf build
    rm -rf *.egg-info
    find . -name "__pycache__" -exec rm -rf {} +
    find . -name "*.pyc" -delete
    echo "Clean complete!"
}

function update_deps {
    echo "Updating dependencies..."
    uv lock
    uv sync
    echo "Dependencies updated!"
}

# Main command execution
case "$1" in
    setup)
        setup
        ;;
    sync)
        sync_deps
        ;;
    test)
        run_tests
        ;;
    test-unit)
        run_unit_tests
        ;;
    test-file)
        run_test_file
        ;;
    lint)
        run_lint
        ;;
    format)
        run_format
        ;;
    codex)
        run_codex "${@:2}"
        ;;
    search)
        run_search "${@:2}"
        ;;
    docs)
        build_docs
        ;;
    clean)
        clean
        ;;
    update-deps)
        update_deps
        ;;
    help|*)
        show_help
        ;;
esac
