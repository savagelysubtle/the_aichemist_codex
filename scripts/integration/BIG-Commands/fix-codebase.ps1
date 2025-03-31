# fix-codebase.ps1
# A helper script to run the updated BIG-Codebase.ps1 script directly
# Version 1.0.0
# Created: 2025-04-01

# Get the full path to the updated codebase script
$codebaseScript = Join-Path -Path $PSScriptRoot -ChildPath "BIG-Codebase.ps1"

if (-not (Test-Path -Path $codebaseScript)) {
    Write-Host "ERROR: Could not find BIG-Codebase.ps1 at $codebaseScript" -ForegroundColor Red
    exit 1
}

# Display current directory and script path
Write-Host "Current Directory: $PWD" -ForegroundColor Cyan
Write-Host "Using Codebase Script: $codebaseScript" -ForegroundColor Cyan

# Execute the command directly with parameters
Write-Host "Executing: $codebaseScript -Command 'analyze' -TargetPath './src' -TestMode" -ForegroundColor Cyan
& $codebaseScript -Command "analyze" -TargetPath "./src" -TestMode

# Check the result
if ($LASTEXITCODE -eq 0) {
    Write-Host "Command executed successfully!" -ForegroundColor Green
}
else {
    Write-Host "Command failed with exit code $LASTEXITCODE" -ForegroundColor Red
}
