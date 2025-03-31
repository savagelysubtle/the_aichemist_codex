# BIG-Profile.ps1
# PowerShell profile with BIG command aliases
# Version 1.0.1
# Created: 2025-03-29
# Updated: 2025-04-01 - Fixed Export-ModuleMember issue and added dynamic path detection

# This file should be sourced from your PowerShell profile or added to:
# $PROFILE.CurrentUserAllHosts

# First try to find the project root
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

# Try to find the project root
$projectRoot = Find-ProjectDirectory -DirectoryMarker "memory-bank"
if (-not $projectRoot) {
    $projectRoot = Find-ProjectDirectory -DirectoryMarker ".cursor"
}

# Define the path to the BIG script directory
$bigWrapperPath = $null

# Look for BIG-Wrapper.ps1 in common locations
$wrapperLocations = @(
    (Join-Path -Path $PSScriptRoot -ChildPath "..\BIG-Commands\BIG-Wrapper.ps1"),
    (Join-Path -Path $projectRoot -ChildPath "memory-bank\integration\BIG-Commands\BIG-Wrapper.ps1"),
    (Join-Path -Path $projectRoot -ChildPath "scripts\BIG-Commands\BIG-Wrapper.ps1")
)

foreach ($location in $wrapperLocations) {
    if (Test-Path $location) {
        $bigWrapperPath = $location
        break
    }
}

if (-not $bigWrapperPath) {
    Write-Host "Warning: Could not find BIG-Wrapper.ps1. BIG commands may not work properly." -ForegroundColor Yellow
    return
}

# Create a function to run BIG commands
function Invoke-BIG {
    param (
        [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $bigWrapperPath @Arguments
}

# Add aliases for common BIG operations
Set-Alias -Name big -Value Invoke-BIG
Set-Alias -Name mb -Value Invoke-BIG
Set-Alias -Name brain -Value Invoke-BIG

# Create shortcuts for common commands
function Start-BIGDay { & $bigWrapperPath start @args }
function Get-BIGHealth { & $bigWrapperPath health @args }
function Get-BIGStats { & $bigWrapperPath stats @args }
function Start-BIGBedtime { & $bigWrapperPath bedtime @args }
function Complete-BIGBedtime { & $bigWrapperPath sleep @args }
function Start-BIGUpdate { & $bigWrapperPath update @args }

# Remove Export-ModuleMember calls - these only work in modules
# Export-ModuleMember -Function Invoke-BIG, Start-BIGDay, Get-BIGHealth, Get-BIGStats, Start-BIGBedtime, Complete-BIGBedtime, Start-BIGUpdate
# Export-ModuleMember -Alias big, mb, brain

# Add tab completion for BIG commands
Register-ArgumentCompleter -CommandName Invoke-BIG, big, mb, brain -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    # Define the list of valid commands
    $validCommands = @(
        "start", "today", "daily",
        "status", "health", "stats", "report",
        "organize", "cleanup", "categorize",
        "bedtime", "sleep", "summary",
        "rules", "add-rule", "apply-rules",
        "update", "refresh",
        "weekly", "monthly", "full",
        "help", "?",
        "codebase", "analyze", "validate", "apply", "learn", "search"
    )

    # Return matching commands
    $validCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
}

# Display a welcome message when the profile is loaded
Write-Host "BIG Memory Bank System commands loaded. Type 'big help' for available commands." -ForegroundColor Cyan
