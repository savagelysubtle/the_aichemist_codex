# simple-fix.ps1
# Script to update PowerShell profile to use the dynamic loader
# Version 1.0.0
# Created: 2025-04-01

Write-Host "BIG Profile Updater" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host ""

# Get the current directory of this script
$scriptDir = $PSScriptRoot
Write-Host "Script directory: $scriptDir" -ForegroundColor Cyan

# Get the path to our dynamic loader
$dynamicLoaderPath = Join-Path -Path $scriptDir -ChildPath "BIG-Dynamic-Loader.ps1"
Write-Host "Dynamic loader path: $dynamicLoaderPath" -ForegroundColor Cyan

if (-not (Test-Path -Path $dynamicLoaderPath)) {
    Write-Host "Error: Dynamic loader not found at $dynamicLoaderPath" -ForegroundColor Red
    exit 1
}

# Get user's PowerShell profile path
$profilePath = $PROFILE.CurrentUserAllHosts
Write-Host "PowerShell profile path: $profilePath" -ForegroundColor Cyan

# Make sure profile directory exists
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path -Path $profileDir)) {
    New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
    Write-Host "Created PowerShell profile directory: $profileDir" -ForegroundColor Green
}

# Create a new loader reference
$newLoaderRef = ". `"$dynamicLoaderPath`""

# Check if profile exists
if (Test-Path -Path $profilePath) {
    # Create backup of existing profile
    $backupPath = "$profilePath.bak"
    Copy-Item -Path $profilePath -Destination $backupPath -Force
    Write-Host "Created backup of existing profile at: $backupPath" -ForegroundColor Green

    # Read current profile content
    $profileContent = Get-Content -Path $profilePath -Raw -ErrorAction SilentlyContinue

    # Simple approach: check if the dynamic loader path is already in the profile
    if ($profileContent -match [regex]::Escape($dynamicLoaderPath)) {
        Write-Host "Dynamic loader already found in profile. No changes needed." -ForegroundColor Green
    }
    else {
        # Append the loader to the profile
        if ($profileContent.EndsWith("`n")) {
            $updatedContent = $profileContent + $newLoaderRef
        }
        else {
            $updatedContent = $profileContent + "`n" + $newLoaderRef
        }

        # Write the updated content back to the profile
        Set-Content -Path $profilePath -Value $updatedContent -Force
        Write-Host "Successfully updated PowerShell profile!" -ForegroundColor Green
    }
}
else {
    # Create a new profile with the dynamic loader
    $newProfile = "# PowerShell profile created by BIG simple-fix.ps1`n$newLoaderRef"
    Set-Content -Path $profilePath -Value $newProfile -Force
    Write-Host "Successfully created PowerShell profile with dynamic loader!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Profile update complete!" -ForegroundColor Cyan
Write-Host "Please restart your PowerShell session or reload your profile with the command:" -ForegroundColor Cyan
Write-Host ". `$PROFILE.CurrentUserAllHosts" -ForegroundColor Yellow
Write-Host ""
Write-Host "After restarting, the 'big' command will use the dynamic loader to find the correct scripts." -ForegroundColor Cyan
