# BIG-Codebase.ps1
# Implementation of the BIG BRAIN codebase management system
# Version 1.0.1
# Created: 2025-03-25
# Updated: 2025-04-01 - Added dynamic project root detection

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("analyze", "apply", "validate", "learn", "search")]
    [string]$Command,

    [Parameter(Mandatory = $false)]
    [string]$TargetPath = ".",

    [Parameter(Mandatory = $false)]
    [string]$RuleCategory,

    [Parameter(Mandatory = $false)]
    [string]$Language,

    [Parameter(Mandatory = $false)]
    [string]$Pattern,

    [Parameter(Mandatory = $false)]
    [switch]$Force,

    [Parameter(Mandatory = $false)]
    [switch]$TestMode,

    [Parameter(Mandatory = $false)]
    [switch]$Detailed
)

# Write startup information
Write-Host "BIG-Codebase running with command: $Command" -ForegroundColor Cyan
if ($TargetPath) { Write-Host "  Target Path: $TargetPath" -ForegroundColor Cyan }
if ($RuleCategory) { Write-Host "  Rule Category: $RuleCategory" -ForegroundColor Cyan }
if ($Language) { Write-Host "  Language: $Language" -ForegroundColor Cyan }
if ($TestMode) { Write-Host "  RUNNING IN TEST MODE - No changes will be made" -ForegroundColor Magenta }

#-----------------------------------------------------------
# Import logging utility and helper functions
#-----------------------------------------------------------
$utilityPath = Join-Path -Path $PSScriptRoot -ChildPath "../Utilities/Write-BIGLog.ps1"
if (Test-Path $utilityPath) {
    . $utilityPath
}
else {
    # Fallback logging function if utility not found
    function Write-BIGLog {
        param([string]$Message, [string]$Level, [string]$LogFile)
        Write-Host "[$Level] $Message" -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARNING") { "Yellow" } else { "White" })
    }

    function Start-BIGLogging { param([string]$ScriptName) return $null }
    function Stop-BIGLogging { param([string]$ScriptName, [string]$LogFile) }
}

# Start logging
$logFile = Start-BIGLogging -ScriptName $MyInvocation.MyCommand.Path

# Add the dynamic project directory finder function from BIG-Dynamic-Loader
function Find-ProjectDirectory {
    param (
        [string]$DirectoryMarker,
        [string]$StartPath = $PWD.Path,
        [int]$MaxDepth = 5
    )

    $currentPath = $StartPath
    $depth = 0

    while ($depth -lt $MaxDepth) {
        # Check if the marker exists in the current path
        if (Test-Path (Join-Path -Path $currentPath -ChildPath $DirectoryMarker)) {
            return $currentPath
        }

        # Move up one directory
        $parentPath = Split-Path -Path $currentPath -Parent

        # If we've reached the root, stop searching
        if ($parentPath -eq $currentPath) {
            break
        }

        $currentPath = $parentPath
        $depth++
    }

    # Return $null if directory marker not found
    return $null
}

#-----------------------------------------------------------
# Set up paths and create directories if needed
#-----------------------------------------------------------
# First try to find the project root by looking for memory-bank directory
$projectRoot = Find-ProjectDirectory -DirectoryMarker "memory-bank"

# If not found, try looking for .cursor directory
if (-not $projectRoot) {
    $projectRoot = Find-ProjectDirectory -DirectoryMarker ".cursor"
}

# If still not found, try common project names in common locations
if (-not $projectRoot) {
    $commonLocations = @(
        "D:\Coding\Python_Projects\the_aichemist_codex",
        "D:\Coding\Python_Projects\TheMemoryBank",
        "$env:USERPROFILE\Documents\the_aichemist_codex",
        "$env:USERPROFILE\Documents\TheMemoryBank"
    )

    foreach ($location in $commonLocations) {
        if (Test-Path $location) {
            $projectRoot = $location
            break
        }
    }
}

if (-not $projectRoot) {
    Write-BIGLog -Message "Could not find project root directory" -Level "ERROR" -LogFile $logFile
    Write-Host "Error: Could not locate project root directory. Please run from within the project directory." -ForegroundColor Red
    exit 1
}

Write-Host "  Project Root: $projectRoot" -ForegroundColor Cyan

# Define possible rule directory locations in order of preference
$possibleRuleDirs = @(
    (Join-Path -Path $projectRoot -ChildPath ".cursor/rules/codebase"),
    (Join-Path -Path $projectRoot -ChildPath "memory-bank/rules/codebase"),
    (Join-Path -Path $projectRoot -ChildPath "rules/codebase"),
    (Join-Path -Path $projectRoot -ChildPath ".memory-bank/rules/codebase")
)

$codebaseRulesDir = $null
foreach ($dir in $possibleRuleDirs) {
    if (Test-Path -Path $dir) {
        $codebaseRulesDir = $dir
        Write-Host "  Found rules directory: $codebaseRulesDir" -ForegroundColor Cyan
        break
    }
}

# If no rules directory found, create one
if (-not $codebaseRulesDir) {
    Write-BIGLog -Message "Codebase rules directory not found in any standard location" -Level "WARNING" -LogFile $logFile
    Write-Host "Warning: Codebase rules directory not found in any standard location" -ForegroundColor Yellow
    Write-Host "Creating example rules directory..." -ForegroundColor Yellow

    # Create example rules directory structure in the memory-bank folder
    $exampleRulesDir = Join-Path -Path $projectRoot -ChildPath "memory-bank/rules/codebase"
    $languagesDir = Join-Path -Path $exampleRulesDir -ChildPath "Languages/PowerShell"

    try {
        New-Item -Path $languagesDir -ItemType Directory -Force | Out-Null

        # Create example rule file
        $exampleRulePath = Join-Path -Path $languagesDir -ChildPath "NamingConventions.ps1"
        @"
# Rule: PowerShell Naming Conventions
# Description: Standards for naming variables, functions, and parameters
# Author: BIG BRAIN
# Version: 1.0.0
# Created: 2025-04-01

# This is an example rule file created by BIG-Codebase.ps1
# In the future, these rules will be used to validate and improve your code.

function Analyze-NamingConventions {
    param (
        [string]$FilePath
    )

    # Example rule logic would go here
    return @{
        Passed = $true
        Findings = @()
    }
}

# Export the analysis function
Export-ModuleMember -Function Analyze-NamingConventions
"@ | Out-File -FilePath $exampleRulePath -Encoding utf8

        $codebaseRulesDir = $exampleRulesDir
        Write-Host "  Created example rule at: $exampleRulePath" -ForegroundColor Green
    }
    catch {
        Write-Host "Could not create example rules: $_" -ForegroundColor Red
        exit 1
    }
}

$userCodebasePath = if ($TargetPath -eq ".") { $projectRoot } else {
    if ([System.IO.Path]::IsPathRooted($TargetPath)) {
        $TargetPath
    }
    else {
        Join-Path -Path $projectRoot -ChildPath $TargetPath
    }
}

#-----------------------------------------------------------
# Helper functions
#-----------------------------------------------------------

# Create a nice header for the command output
function Write-BIGCodebaseHeader {
    param([string]$Title)

    $width = 60
    $padding = [math]::Max(0, ($width - $Title.Length - 10) / 2)
    $leftPad = [math]::Floor($padding)
    $rightPad = [math]::Ceiling($padding)

    Write-Host ""
    Write-Host ("=" * $width) -ForegroundColor Cyan
    Write-Host ("#" * $leftPad) -ForegroundColor Cyan -NoNewline
    Write-Host "  $Title  " -ForegroundColor Yellow -NoNewline
    Write-Host ("#" * $rightPad) -ForegroundColor Cyan
    Write-Host ("=" * $width) -ForegroundColor Cyan
    Write-Host ""
}

# Get all codebase rules based on filters
function Get-CodebaseRules {
    param (
        [string]$Category,
        [string]$Language
    )

    $rulesPattern = if ($Category -and $Language) {
        Join-Path -Path $codebaseRulesDir -ChildPath "$Category/$Language/*.ps1"
    }
    elseif ($Category) {
        Join-Path -Path $codebaseRulesDir -ChildPath "$Category/*/*.ps1"
    }
    elseif ($Language) {
        Join-Path -Path $codebaseRulesDir -ChildPath "Languages/$Language/*.ps1"
    }
    else {
        Join-Path -Path $codebaseRulesDir -ChildPath "*/*/*.ps1"
    }

    $rules = Get-ChildItem -Path $rulesPattern -ErrorAction SilentlyContinue
    return $rules
}

# Get user code files based on language
function Get-UserCodeFiles {
    param (
        [string]$Language
    )

    $extension = switch ($Language.ToLower()) {
        "powershell" { "*.ps1" }
        "python" { "*.py" }
        "javascript" { "*.js" }
        "typescript" { "*.ts" }
        default { "*.*" }
    }

    $files = Get-ChildItem -Path $userCodebasePath -Recurse -File -Include $extension
    return $files
}

# Read rule details from comments
function Get-RuleDetails {
    param (
        [string]$RuleFile
    )

    $content = Get-Content -Path $RuleFile -Raw
    $details = [PSCustomObject]@{
        Name        = ""
        Description = ""
        Author      = ""
        Version     = ""
        Created     = ""
    }

    # Extract metadata from comments
    if ($content -match "# Rule: (.*?)[\r\n]") {
        $details.Name = $Matches[1].Trim()
    }

    if ($content -match "# Description: (.*?)[\r\n]") {
        $details.Description = $Matches[1].Trim()
    }

    if ($content -match "# Author: (.*?)[\r\n]") {
        $details.Author = $Matches[1].Trim()
    }

    if ($content -match "# Version: (.*?)[\r\n]") {
        $details.Version = $Matches[1].Trim()
    }

    if ($content -match "# Created: (.*?)[\r\n]") {
        $details.Created = $Matches[1].Trim()
    }

    return $details
}

#-----------------------------------------------------------
# Command implementations
#-----------------------------------------------------------

# Command: analyze - Analyze codebase against coding standards
function Invoke-AnalyzeCommand {
    Write-BIGCodebaseHeader "CODEBASE ANALYSIS"

    # Get rules based on filters
    $rules = Get-CodebaseRules -Category $RuleCategory -Language $Language

    if ($rules.Count -eq 0) {
        Write-BIGLog -Message "No matching rules found" -Level "WARNING" -LogFile $logFile
        Write-Host "No matching rules found for the specified criteria." -ForegroundColor Yellow
        return
    }

    Write-Host "Found $($rules.Count) rule template(s)" -ForegroundColor Cyan

    # Get user code files based on language
    $language = if ($Language) { $Language } else { "all languages" }
    Write-Host "Analyzing codebase for $language" -ForegroundColor Cyan

    $files = if ($Language) {
        Get-UserCodeFiles -Language $Language
    }
    else {
        @(
            (Get-UserCodeFiles -Language "PowerShell"),
            (Get-UserCodeFiles -Language "Python"),
            (Get-UserCodeFiles -Language "JavaScript"),
            (Get-UserCodeFiles -Language "TypeScript")
        )
    }

    Write-Host "Found $($files.Count) file(s) to analyze" -ForegroundColor Cyan

    # Display rule details
    foreach ($rule in $rules) {
        $ruleDetails = Get-RuleDetails -RuleFile $rule.FullName
        Write-Host ""
        Write-Host "Rule: " -NoNewline -ForegroundColor White
        Write-Host $ruleDetails.Name -ForegroundColor Cyan
        Write-Host "Description: " -NoNewline -ForegroundColor White
        Write-Host $ruleDetails.Description -ForegroundColor Cyan
        Write-Host "Version: " -NoNewline -ForegroundColor White
        Write-Host "$($ruleDetails.Version) (Created: $($ruleDetails.Created))" -ForegroundColor Cyan

        if ($Detailed) {
            Write-Host "File: " -NoNewline -ForegroundColor White
            Write-Host $rule.FullName -ForegroundColor Cyan
        }
    }

    # For now, this is just informational
    Write-Host ""
    Write-Host "Analysis complete" -ForegroundColor Green
    Write-Host "The BIG-Codebase system is still learning your code patterns..." -ForegroundColor Yellow
}

# Command: validate - Validate code against coding standards
function Invoke-ValidateCommand {
    Write-BIGCodebaseHeader "CODEBASE VALIDATION"

    # This would validate code files against rules
    Write-Host "This command will validate your codebase against established rules." -ForegroundColor Yellow
    Write-Host "Currently simulating validation - feature in development." -ForegroundColor Yellow

    # Simulate validation
    if ($TestMode) {
        Write-Host ""
        Write-Host "[TEST MODE] Simulating validation of $Language files..." -ForegroundColor Magenta
        Write-Host "- ✅ Parameter naming conventions: PASSED" -ForegroundColor Green
        Write-Host "- ✅ Error handling patterns: PASSED" -ForegroundColor Green
        Write-Host "- ❌ Commenting standards: FAILED - Missing header comments in 3 files" -ForegroundColor Red
        Write-Host "- ⚠️ Function naming conventions: WARNING - 2 functions not using approved verb-noun format" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Validation is a planned feature for future BIG-BRAIN versions." -ForegroundColor Cyan
}

# Command: apply - Apply coding standards to codebase
function Invoke-ApplyCommand {
    Write-BIGCodebaseHeader "APPLYING CODEBASE STANDARDS"

    # This would apply code standards to files
    Write-Host "This command will apply coding standards to your codebase." -ForegroundColor Yellow
    Write-Host "Currently simulating application - feature in development." -ForegroundColor Yellow

    # Simulate application
    if ($TestMode) {
        Write-Host ""
        Write-Host "[TEST MODE] Simulating application of coding standards..." -ForegroundColor Magenta
        Write-Host "- Would add header comments to 3 files" -ForegroundColor Magenta
        Write-Host "- Would rename 2 functions to match verb-noun convention" -ForegroundColor Magenta
        Write-Host "- Would add error handling to 5 code blocks" -ForegroundColor Magenta
    }

    Write-Host ""
    Write-Host "Standard application is a planned feature for future BIG-BRAIN versions." -ForegroundColor Cyan
}

# Command: learn - Learn from existing code
function Invoke-LearnCommand {
    Write-BIGCodebaseHeader "LEARNING FROM CODEBASE"

    # This would analyze existing code and learn patterns
    Write-Host "This command will learn from your existing codebase to improve BIG-BRAIN's understanding." -ForegroundColor Yellow
    Write-Host "Currently simulating learning - feature in development." -ForegroundColor Yellow

    # Simulate learning
    if ($TestMode) {
        Write-Host ""
        Write-Host "[TEST MODE] Simulating learning from codebase..." -ForegroundColor Magenta
        Write-Host "- Would identify 4 common coding patterns" -ForegroundColor Magenta
        Write-Host "- Would learn naming conventions from 12 files" -ForegroundColor Magenta
        Write-Host "- Would extract 8 reusable code snippets" -ForegroundColor Magenta
    }

    Write-Host ""
    Write-Host "Codebase learning is a planned feature for future BIG-BRAIN versions." -ForegroundColor Cyan
}

# Command: search - Search for patterns in codebase
function Invoke-SearchCommand {
    Write-BIGCodebaseHeader "SEARCHING CODEBASE"

    if (-not $Pattern) {
        Write-BIGLog -Message "Search pattern is required" -Level "ERROR" -LogFile $logFile
        Write-Host "Error: Search pattern is required" -ForegroundColor Red
        return
    }

    # Get files based on language
    $files = if ($Language) {
        Get-UserCodeFiles -Language $Language
    }
    else {
        Get-ChildItem -Path $userCodebasePath -Recurse -File
    }

    Write-Host "Searching for pattern '$Pattern' in $($files.Count) files..." -ForegroundColor Cyan

    $matches = @()
    foreach ($file in $files) {
        $content = Get-Content -Path $file.FullName -Raw
        if ($content -match $Pattern) {
            $matches += $file.FullName
        }
    }

    if ($matches.Count -eq 0) {
        Write-Host "No matches found for pattern '$Pattern'" -ForegroundColor Yellow
    }
    else {
        Write-Host "Found $($matches.Count) matches:" -ForegroundColor Green
        foreach ($match in $matches) {
            Write-Host "- $match" -ForegroundColor White
        }
    }
}

#-----------------------------------------------------------
# Execute the specified command
#-----------------------------------------------------------
try {
    switch ($Command) {
        "analyze" {
            Invoke-AnalyzeCommand
        }
        "validate" {
            Invoke-ValidateCommand
        }
        "apply" {
            Invoke-ApplyCommand
        }
        "learn" {
            Invoke-LearnCommand
        }
        "search" {
            Invoke-SearchCommand
        }
        default {
            Write-BIGLog -Message "Invalid command: $Command" -Level "ERROR" -LogFile $logFile
            Write-Host "Error: Invalid command: $Command" -ForegroundColor Red
        }
    }
}
catch {
    Write-BIGLog -Message "Error executing command: $_" -Level "ERROR" -LogFile $logFile
    Write-Host "Error executing command: $_" -ForegroundColor Red
}

# End logging
Stop-BIGLogging -ScriptName $MyInvocation.MyCommand.Path -LogFile $logFile
