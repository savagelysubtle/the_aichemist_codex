# test-codebase-path.ps1
# Script to determine which BIG-Codebase.ps1 script is being used
# Version 1.0.0
# Created: 2025-04-01

Write-Host "BIG Codebase Path Test" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# First, get the current directory of this script
$scriptDir = $PSScriptRoot
Write-Host "Current script directory: $scriptDir" -ForegroundColor Cyan

# Define our BIG-Codebase.ps1 path
$codebasePath = Join-Path -Path $scriptDir -ChildPath "BIG-Codebase.ps1"
$codebsePath_new = $codebasePath
$codebasePath_old = "D:\Coding\Python_Projects\TheMemoryBank\scripts\BIG-Commands\BIG-Codebase.ps1"

# Check if our codebase script exists
if (Test-Path $codebasePath) {
    Write-Host "✅ BIG-Codebase.ps1 exists at: $codebasePath" -ForegroundColor Green
}
else {
    Write-Host "❌ BIG-Codebase.ps1 NOT found at: $codebasePath" -ForegroundColor Red
}

# Check if the old codebase script exists
if (Test-Path $codebasePath_old) {
    Write-Host "⚠️ Old BIG-Codebase.ps1 exists at: $codebasePath_old" -ForegroundColor Yellow
}
else {
    Write-Host "✅ Old BIG-Codebase.ps1 NOT found at: $codebasePath_old" -ForegroundColor Green
}

# Check what our command shell is set up to use
Write-Host ""
Write-Host "Checking command pipeline..." -ForegroundColor Cyan

# Create full command line for 'big' command, but just print what it would do
Write-Host ""
Write-Host "When you run 'big codebase analyze', the system will:" -ForegroundColor Yellow
Write-Host "1. Find the BIG.ps1 script via the dynamic loader"
Write-Host "2. The BIG.ps1 script will then locate and call BIG-Codebase.ps1"
Write-Host ""

# Get paths from $ENV for the dynamic loader
Write-Host "Environment variables that might affect path resolution:" -ForegroundColor Cyan
Write-Host "  PSModulePath: $($ENV:PSModulePath.Split(';')[0])" -ForegroundColor Gray

# Test direct execution
Write-Host ""
Write-Host "Testing direct execution of BIG-Codebase.ps1:" -ForegroundColor Cyan
& $codebasePath -Command "test" -TestMode
