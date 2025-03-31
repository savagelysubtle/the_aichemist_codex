# reset-big-session.ps1
# Script to reset the current session's references to "big" commands and reload the profile
# Version 1.0.0
# Created: 2025-04-01

Write-Host "BIG Session Reset" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor Cyan
Write-Host ""

# Get the current directory of this script
$scriptDir = $PSScriptRoot
Write-Host "Current script directory: $scriptDir" -ForegroundColor Cyan

# Check if the big alias exists and remove it
if (Get-Alias -Name "big" -ErrorAction SilentlyContinue) {
    Write-Host "Removing existing 'big' alias..." -ForegroundColor Yellow
    Remove-Alias -Name "big" -Force -ErrorAction SilentlyContinue
    Write-Host "Removed alias 'big'" -ForegroundColor Green
}

if (Get-Alias -Name "mb" -ErrorAction SilentlyContinue) {
    Write-Host "Removing existing 'mb' alias..." -ForegroundColor Yellow
    Remove-Alias -Name "mb" -Force -ErrorAction SilentlyContinue
    Write-Host "Removed alias 'mb'" -ForegroundColor Green
}

# Clear any functions named Invoke-BIG
if (Get-Command -Name "Invoke-BIG" -ErrorAction SilentlyContinue) {
    Write-Host "Found existing 'Invoke-BIG' function. Removing from current session..." -ForegroundColor Yellow
    # Can't actually remove functions, so we'll redefine it to do nothing
    function Invoke-BIG {
        Write-Host "Invoke-BIG function has been reset. Please reload your profile." -ForegroundColor Yellow
    }
    Write-Host "Reset Invoke-BIG function" -ForegroundColor Green
}

# Get the path to our dynamic loader
$dynamicLoaderPath = Join-Path -Path $scriptDir -ChildPath "BIG-Dynamic-Loader.ps1"
Write-Host "Dynamic loader path: $dynamicLoaderPath" -ForegroundColor Cyan

# Source the dynamic loader to create a fresh session
if (Test-Path $dynamicLoaderPath) {
    Write-Host "Reloading dynamic loader from: $dynamicLoaderPath" -ForegroundColor Green
    try {
        # Re-import the dynamic loader
        . $dynamicLoaderPath
    }
    catch {
        Write-Host "Error reloading dynamic loader: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "Dynamic loader not found at: $dynamicLoaderPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "Session reset complete!" -ForegroundColor Cyan
Write-Host "Try running 'big codebase analyze -TargetPath ./src -TestMode' again" -ForegroundColor Yellow
