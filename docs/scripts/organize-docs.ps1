# Documentation Organization Script

# Ensure all target directories exist
$directories = @(
    "docs\markdown\user_guide",
    "docs\markdown\development",
    "docs\markdown\tutorials",
    "docs\markdown\api",
    "docs\markdown\reference"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir"
        New-Item -ItemType Directory -Path $dir -Force
    }
}

# Development related files
$developmentFiles = @(
    "docs\development.md",
    "docs\development_guide.md",
    "docs\code_maintenance.md",
    "docs\code_review.md",
    "docs\implementation_plan.md",
    "docs\improvement_tracker.md"
)

# User guide related files
$userGuideFiles = @(
    "docs\README.md",
    "docs\project_summary.md",
    "docs\data_directory_config.md"
)

# Reference files
$referenceFiles = @(
    "docs\root_docs_readme.md",
    "docs\Data_Directory_Investigation.md"
)

# Helper function to move files and handle errors
function Move-DocumentFile {
    param (
        [string]$sourceFile,
        [string]$destinationFolder
    )

    if (Test-Path $sourceFile) {
        $fileName = Split-Path $sourceFile -Leaf
        $destinationPath = Join-Path -Path $destinationFolder -ChildPath $fileName

        try {
            Write-Host "Moving $sourceFile to $destinationPath"
            Move-Item -Path $sourceFile -Destination $destinationPath -Force
        }
        catch {
            Write-Host "Error moving $sourceFile to $destinationPath" -ForegroundColor Red
        }
    }
    else {
        Write-Host "Source file not found: $sourceFile" -ForegroundColor Yellow
    }
}

# Move development files
foreach ($file in $developmentFiles) {
    Move-DocumentFile -sourceFile $file -destinationFolder "docs\markdown\development"
}

# Move user guide files
foreach ($file in $userGuideFiles) {
    Move-DocumentFile -sourceFile $file -destinationFolder "docs\markdown\user_guide"
}

# Move reference files
foreach ($file in $referenceFiles) {
    Move-DocumentFile -sourceFile $file -destinationFolder "docs\markdown\reference"
}

# Handle organized_markdown directory
Write-Host "Processing organized_markdown files..."
$organizedMarkdownFiles = Get-ChildItem -Path "docs\organized_markdown" -Filter "*.md"

foreach ($file in $organizedMarkdownFiles) {
    $fileName = $file.Name

    # Determine appropriate target directory based on filename patterns
    $targetDir = "docs\markdown\api"  # Default to API

    if ($fileName -like "*config*" -or $fileName -like "*directory*") {
        $targetDir = "docs\markdown\user_guide"
    }
    elseif ($fileName -like "*utils*" -or $fileName -like "*version*") {
        $targetDir = "docs\markdown\development"
    }

    # Copy instead of move to preserve the original structure
    $destinationPath = Join-Path -Path $targetDir -ChildPath $fileName
    Copy-Item -Path $file.FullName -Destination $destinationPath
    Write-Host "Copied $($file.FullName) to $destinationPath"
}

# Process the nested docs directory if it exists
if (Test-Path "docs\docs\tutorials") {
    Write-Host "Processing nested tutorials directory..."

    # First copy the directory structure
    $nestedDirectories = Get-ChildItem -Path "docs\docs\tutorials" -Directory

    foreach ($dir in $nestedDirectories) {
        $targetDir = Join-Path -Path "docs\tutorials" -ChildPath $dir.Name

        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force
            Write-Host "Created directory: $targetDir"
        }

        # Copy files from nested directory to main tutorials
        $nestedFiles = Get-ChildItem -Path $dir.FullName -File

        foreach ($file in $nestedFiles) {
            $destPath = Join-Path -Path $targetDir -ChildPath $file.Name
            Copy-Item -Path $file.FullName -Destination $destPath
            Write-Host "Copied $($file.FullName) to $destPath"
        }
    }
}

Write-Host "Documentation organization complete!"