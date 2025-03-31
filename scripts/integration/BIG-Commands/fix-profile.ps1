# fix-profile.ps1
# Script to update the PowerShell profile to use the updated BIG-Profile.ps1
# Version 1.0.0
# Created: 2025-04-01

Write-Host "BIG Profile Updater" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host ""

# Get the current directory of this script
$scriptDir = $PSScriptRoot
Write-Host "Script directory: $scriptDir" -ForegroundColor Cyan

# Get the path to our updated BIG-Profile.ps1
$bigProfilePath = Join-Path -Path $scriptDir -ChildPath "..\..\..\scripts\profiles\BIG-Profile.ps1"
$bigProfilePath = [System.IO.Path]::GetFullPath($bigProfilePath)

Write-Host "BIG-Profile path: $bigProfilePath" -ForegroundColor Cyan

# Check if the profile exists
if (-not (Test-Path -Path $bigProfilePath)) {
    Write-Host "Error: BIG-Profile.ps1 not found at $bigProfilePath" -ForegroundColor Red
    exit 1
}

# Create a new PowerShell profile that just loads the BIG-Profile.ps1 file
$profilePath = $PROFILE.CurrentUserAllHosts
Write-Host "PowerShell profile path: $profilePath" -ForegroundColor Cyan

# Make sure profile directory exists
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path -Path $profileDir)) {
    New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
    Write-Host "Created PowerShell profile directory: $profileDir" -ForegroundColor Green
}

# Create a backup of the existing profile if it exists
if (Test-Path -Path $profilePath) {
    $backupPath = "$profilePath.bak"
    Copy-Item -Path $profilePath -Destination $backupPath -Force
    Write-Host "Created backup of existing profile at: $backupPath" -ForegroundColor Green
}

# Update the profile to source the BIG-Profile.ps1 file
$newProfileContent = @"
# PowerShell profile updated by BIG fix-profile.ps1
# Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Load the BIG-Profile.ps1 file
. "$bigProfilePath"
"@

Set-Content -Path $profilePath -Value $newProfileContent -Force
Write-Host "Updated PowerShell profile to use the BIG-Profile.ps1 file!" -ForegroundColor Green

# Also reload the profile in the current session
try {
    . $PROFILE.CurrentUserAllHosts
    Write-Host "Reloaded PowerShell profile in current session!" -ForegroundColor Green
}
catch {
    Write-Host "Failed to reload PowerShell profile in current session: $_" -ForegroundColor Yellow
    Write-Host "Please restart your PowerShell session." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Profile update complete!" -ForegroundColor Cyan
Write-Host "Please restart your PowerShell session to apply all changes." -ForegroundColor Yellow
Write-Host ""
Write-Host "After restarting, the 'big' command will use the updated BIG-Profile.ps1 script." -ForegroundColor Cyan
