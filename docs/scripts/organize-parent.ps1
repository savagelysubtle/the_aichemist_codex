# Parent Docs Folder Organization Script

# Define target directories to ensure they exist
$directories = @(
    "docs\api",
    "docs\tutorials",
    "docs\user_guides",
    "docs\reference",
    "docs\scripts",
    "docs\tools"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir"
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Files to move to the scripts directory
$scriptFiles = @(
    "docs\build_docs.py",
    "docs\generate_api_docs.py",
    "docs\organize-docs.ps1",
    "docs\find-duplicates.ps1",
    "docs\organize-parent.ps1"
)

# Files to move to the reference directory
$referenceFiles = @(
    "docs\directory_structure.rst",
    "docs\data_management.rst",
    "docs\environment.rst",
    "docs\code_style.rst"
)

# Files to explicitly keep at root
$rootFiles = @(
    "docs\index.rst",  # Main index file
    "docs\conf.py",
    "docs\Makefile",
    "docs\make.bat",
    "docs\README_ORGANIZATION.md",
    "docs\README.md",
    "docs\architecture.rst",
    "docs\development.rst",
    "docs\contributing.rst",
    "docs\changelog.rst",
    "docs\roadmap.rst"
)

# User guide files
$userGuideFiles = @(
    "docs\getting_started.rst",
    "docs\installation.rst",
    "docs\usage.rst",
    "docs\configuration.rst",
    "docs\cli_reference.rst"
)

# Helper function to move files
function Move-DocFile {
    param (
        [string]$sourceFile,
        [string]$destinationFolder
    )

    if (Test-Path $sourceFile) {
        $fileName = Split-Path $sourceFile -Leaf
        $destinationPath = Join-Path -Path $destinationFolder -ChildPath $fileName

        # Don't move if already in correct location
        if ((Split-Path $sourceFile -Parent) -eq $destinationFolder) {
            Write-Host "File already in correct location: $sourceFile" -ForegroundColor Green
            return
        }

        try {
            Write-Host "Moving $sourceFile to $destinationPath"
            # Use Copy-Item and then verify before deleting the original
            Copy-Item -Path $sourceFile -Destination $destinationPath -Force
            if (Test-Path $destinationPath) {
                Remove-Item -Path $sourceFile -Force
            }
        }
        catch {
            Write-Host "Error moving $sourceFile to $destinationPath" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Source file not found: $sourceFile" -ForegroundColor Yellow
    }
}

# Move script files
foreach ($file in $scriptFiles) {
    if ($file -ne "docs\organize-parent.ps1") {  # Don't move the current script while it's running
        Move-DocFile -sourceFile $file -destinationFolder "docs\scripts"
    }
}

# Move reference files
foreach ($file in $referenceFiles) {
    Move-DocFile -sourceFile $file -destinationFolder "docs\reference"
}

# Move user guide files
foreach ($file in $userGuideFiles) {
    Move-DocFile -sourceFile $file -destinationFolder "docs\user_guides"
}

# If the main index.rst is missing, try to find and restore it
if (-not (Test-Path "docs\index.rst")) {
    $possibleLocations = @(
        "docs\tutorials\index.rst",
        "docs\api\index.rst",
        "docs\user_guides\index.rst",
        "docs\reference\index.rst"
    )

    foreach ($location in $possibleLocations) {
        if (Test-Path $location) {
            Write-Host "Found index.rst at $location, restoring to root" -ForegroundColor Yellow
            Copy-Item -Path $location -Destination "docs\index.rst" -Force
            Remove-Item -Path $location -Force
            break
        }
    }

    # If still not found, create a basic one
    if (-not (Test-Path "docs\index.rst")) {
        Write-Host "Creating new index.rst file in root directory" -ForegroundColor Yellow
        $newIndexContent = @"
The AIchemist Codex
==================

Documentation
------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guides/getting_started
   user_guides/installation
   user_guides/usage
   user_guides/configuration
   user_guides/data_management
   user_guides/cli_reference

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/index

.. toctree::
   :maxdepth: 1
   :caption: Development

   development
   reference/environment
   reference/directory_structure
   contributing
   reference/code_style
   roadmap
   changelog

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture

Indices and tables
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"@
        $newIndexContent | Out-File -FilePath "docs\index.rst" -Force
    }
}

# Create a README.md that points to the organizational README
$readmeContent = @"
# The AIchemist Codex Documentation

The documentation for The AIchemist Codex has been organized into a structured directory system.

For details on the documentation organization, please see [README_ORGANIZATION.md](README_ORGANIZATION.md).

## Quick Links

- [Main Documentation Index](index.rst)
- [User Guides](user_guides/)
- [API Reference](api/)
- [Tutorials](tutorials/)
- [Markdown Documentation](markdown/)

## Building Documentation

To build the documentation:

```bash
# Navigate to the docs directory
cd docs

# Build the documentation
make html

# View the documentation (on Windows)
start _build/html/index.html
```
"@

# Only update README if it doesn't exist
if (-not (Test-Path "docs\README.md")) {
    $readmeFile = "docs\README.md"
    $readmeContent | Out-File -FilePath $readmeFile -Force
    Write-Host "Created updated README.md"
}

# Create index.rst files for subdirectories if needed
$indexDirectories = @("docs\api", "docs\tutorials", "docs\user_guides", "docs\reference")
foreach ($dir in $indexDirectories) {
    $indexPath = Join-Path -Path $dir -ChildPath "index.rst"

    if (-not (Test-Path $indexPath)) {
        $dirName = Split-Path $dir -Leaf
        $title = (Get-Culture).TextInfo.ToTitleCase($dirName) -replace '_', ' '

        $indexContent = @"
$title
$('=' * $title.Length)

This directory contains $dirName documentation.

Contents:

.. toctree::
   :maxdepth: 2
   :caption: $title

"@

        # Add references to files in this directory
        $files = Get-ChildItem -Path $dir -Filter "*.rst" | Where-Object { $_.Name -ne "index.rst" }
        foreach ($file in $files) {
            $baseName = $file.BaseName
            $indexContent += "   $baseName`n"
        }

        $indexContent | Out-File -FilePath $indexPath -Force
        Write-Host "Created index for $dir"
    }
}

# Move this script to scripts directory on next run
if (Test-Path "docs\organize-parent.ps1") {
    Write-Host "When you're satisfied with the organization, run this script once more to move it to the scripts directory" -ForegroundColor Yellow
}

Write-Host "Parent docs folder organization complete!" -ForegroundColor Green