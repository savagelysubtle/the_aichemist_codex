# AIchemist Codex Development Helper Script (PowerShell version)
# This script provides shortcuts for common UV commands used in development

# Check if UV is installed
try {
    $null = Get-Command uv -ErrorAction Stop
} catch {
    Write-Error "Error: UV is not installed. Please install it with 'pip install uv'"
    exit 1
}

# Check if we're in the project root (look for pyproject.toml)
if (-not (Test-Path "pyproject.toml")) {
    Write-Error "Error: You must run this script from the project root directory (where pyproject.toml is located)"
    exit 1
}

# Function to display help
function Show-Help {
    Write-Host "AIchemist Codex Development Helper"
    Write-Host ""
    Write-Host "Usage: .\scripts\codex-dev.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  setup         - Create venv and install all dependencies"
    Write-Host "  sync          - Sync dependencies from lockfile"
    Write-Host "  test          - Run all tests"
    Write-Host "  test-unit     - Run unit tests only"
    Write-Host "  test-file     - Run tests for a specific file (specify with -File parameter)"
    Write-Host "  lint          - Run linting checks"
    Write-Host "  format        - Format code with ruff and black"
    Write-Host "  codex         - Run the codex CLI"
    Write-Host "  search        - Run the search tool"
    Write-Host "  docs          - Build documentation"
    Write-Host "  clean         - Clean temporary files and caches"
    Write-Host "  update-deps   - Update dependencies and rebuild lockfile"
    Write-Host "  help          - Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\scripts\codex-dev.ps1 setup"
    Write-Host "  .\scripts\codex-dev.ps1 test"
    Write-Host "  .\scripts\codex-dev.ps1 test-file -File tests\domain\entities\test_code_artifact.py"
    Write-Host "  .\scripts\codex-dev.ps1 codex analyze path\to\file"
    Write-Host ""
}

# Command functions
function Setup-Environment {
    Write-Host "Setting up development environment..."
    uv venv
    Write-Host "Activate with: .venv\Scripts\activate"
    uv sync
    uv pip install -e .
    Write-Host "Setup complete!"
}

function Sync-Dependencies {
    Write-Host "Syncing dependencies..."
    uv sync
    Write-Host "Dependencies synced!"
}

function Run-Tests {
    Write-Host "Running tests..."
    uv run pytest -xvs
}

function Run-UnitTests {
    Write-Host "Running unit tests only..."
    uv run pytest -xvs -m "unit"
}

function Run-TestFile {
    param (
        [Parameter(Mandatory=$true)]
        [string]$File
    )

    Write-Host "Running tests for $File..."
    uv run pytest -xvs $File
}

function Run-Lint {
    Write-Host "Running linters..."
    uv run ruff check .
    uv run mypy src
}

function Format-Code {
    Write-Host "Formatting code..."
    uv run ruff format .
    uv run isort .
}

function Run-Codex {
    param (
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )

    Write-Host "Running codex CLI..."
    $cmd = "uv run codex $($Arguments -join ' ')"
    Invoke-Expression $cmd
}

function Run-Search {
    param (
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Arguments
    )

    Write-Host "Running search tool..."
    $cmd = "uv run search-tool $($Arguments -join ' ')"
    Invoke-Expression $cmd
}

function Build-Docs {
    Write-Host "Building documentation..."
    uv run docs build
}

function Clean-Project {
    Write-Host "Cleaning temporary files and caches..."
    if (Test-Path ".ruff_cache") { Remove-Item -Recurse -Force ".ruff_cache" }
    if (Test-Path ".mypy_cache") { Remove-Item -Recurse -Force ".mypy_cache" }
    if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }
    if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
    if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    Get-ChildItem -Path "." -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force
    Get-ChildItem -Path "." -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
    Get-ChildItem -Path "." -Filter "*.pyc" -Recurse | Remove-Item -Force
    Write-Host "Clean complete!"
}

function Update-Dependencies {
    Write-Host "Updating dependencies..."
    uv lock
    uv sync
    Write-Host "Dependencies updated!"
}

# Parse command line arguments
param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter()]
    [string]$File
)

# Main command execution
switch ($Command) {
    "setup" {
        Setup-Environment
    }
    "sync" {
        Sync-Dependencies
    }
    "test" {
        Run-Tests
    }
    "test-unit" {
        Run-UnitTests
    }
    "test-file" {
        if (-not $File) {
            Write-Error "Error: Please specify a file with -File parameter"
            exit 1
        }
        Run-TestFile -File $File
    }
    "lint" {
        Run-Lint
    }
    "format" {
        Format-Code
    }
    "codex" {
        $args = $MyInvocation.BoundParameters.Values | Where-Object { $_ -ne $Command }
        $args += $MyInvocation.UnboundArguments
        Run-Codex -Arguments $args
    }
    "search" {
        $args = $MyInvocation.BoundParameters.Values | Where-Object { $_ -ne $Command }
        $args += $MyInvocation.UnboundArguments
        Run-Search -Arguments $args
    }
    "docs" {
        Build-Docs
    }
    "clean" {
        Clean-Project
    }
    "update-deps" {
        Update-Dependencies
    }
    "help" {
        Show-Help
    }
    default {
        Show-Help
    }
}
