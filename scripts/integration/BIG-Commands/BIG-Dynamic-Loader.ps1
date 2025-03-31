# BIG-Dynamic-Loader.ps1
# Dynamic loader for BIG BRAIN commands that automatically finds the correct paths
# Version 1.0.0
# Created: 2023-04-01

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

function Initialize-BIGEnvironment {
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

    # If we found a project root, look for the BIG-Profile.ps1
    if ($projectRoot) {
        Write-Host "Found project root: $projectRoot" -ForegroundColor Cyan

        # Try to find BIG-Profile.ps1 in common locations
        $profileLocations = @(
            (Join-Path -Path $projectRoot -ChildPath "scripts\profiles\BIG-Profile.ps1"),
            (Join-Path -Path $projectRoot -ChildPath "memory-bank\integration\profiles\BIG-Profile.ps1"),
            (Join-Path -Path $projectRoot -ChildPath "memory-bank\integration\BIG-Commands\profiles\BIG-Profile.ps1")
        )

        $profilePath = $null
        foreach ($location in $profileLocations) {
            if (Test-Path $location) {
                $profilePath = $location
                break
            }
        }

        if ($profilePath) {
            Write-Host "Found BIG-Profile: $profilePath" -ForegroundColor Green

            # Source the profile
            try {
                . $profilePath

                # Find and display the welcome banner
                $welcomeScriptPath = Join-Path -Path $projectRoot -ChildPath "memory-bank\integration\BIG-Commands\BIG-Welcome.ps1"
                if (Test-Path $welcomeScriptPath) {
                    # Show welcome banner
                    . $welcomeScriptPath
                }
                else {
                    Write-Host "BIG Memory Bank System commands loaded. Type 'big help' for available commands." -ForegroundColor Cyan
                }

                Write-Host "Successfully loaded BIG-Profile" -ForegroundColor Green
                return $true
            }
            catch {
                Write-Host "Error loading BIG-Profile: $_" -ForegroundColor Red
            }
        }
        else {
            Write-Host "Could not find BIG-Profile.ps1" -ForegroundColor Yellow

            # Try to find BIG.ps1 directly
            $bigScriptLocations = @(
                (Join-Path -Path $projectRoot -ChildPath "memory-bank\integration\BIG-Commands\BIG.ps1"),
                (Join-Path -Path $projectRoot -ChildPath "scripts\BIG-Commands\BIG.ps1"),
                (Join-Path -Path $projectRoot -ChildPath "BIG-Commands\BIG.ps1")
            )

            $bigScriptPath = $null
            foreach ($location in $bigScriptLocations) {
                if (Test-Path $location) {
                    $bigScriptPath = $location
                    break
                }
            }

            if ($bigScriptPath) {
                Write-Host "Found BIG script: $bigScriptPath" -ForegroundColor Green

                # Create a simple alias function
                function Invoke-BIG {
                    param (
                        [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
                        [string[]]$Arguments
                    )

                    & $bigScriptPath @Arguments
                }

                # Create aliases
                Set-Alias -Name big -Value Invoke-BIG -Scope Global
                Set-Alias -Name mb -Value Invoke-BIG -Scope Global

                # Find and display the welcome banner
                $welcomeScriptPath = Join-Path -Path $projectRoot -ChildPath "memory-bank\integration\BIG-Commands\BIG-Welcome.ps1"
                if (Test-Path $welcomeScriptPath) {
                    # Show welcome banner
                    . $welcomeScriptPath
                }
                else {
                    Write-Host "BIG Memory Bank System commands loaded. Type 'big help' for available commands." -ForegroundColor Cyan
                }

                Write-Host "Created BIG aliases" -ForegroundColor Green
                return $true
            }
        }
    }

    Write-Host "Could not find BIG BRAIN environment" -ForegroundColor Red
    return $false
}

# Initialize the BIG environment
$success = Initialize-BIGEnvironment

# Add user notification
if (-not $success) {
    Write-Host "To use BIG commands, please navigate to your project directory" -ForegroundColor Yellow
}
