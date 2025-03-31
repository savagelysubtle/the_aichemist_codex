# update-profile.ps1
# Script to update PowerShell profile to use dynamic BIG loader
# Version 1.0.0
# Created: 2023-04-01

# Get the full path to the dynamic loader script
$scriptPath = Join-Path -Path $PSScriptRoot -ChildPath "BIG-Dynamic-Loader.ps1"
$scriptPath = (Resolve-Path $scriptPath).Path

# Get the path to the PowerShell profile
$profilePath = $PROFILE.CurrentUserAllHosts
$profileDir = Split-Path -Parent $profilePath

# Create profile directory if it doesn't exist
if (-not (Test-Path -Path $profileDir)) {
    Write-Host "Creating profile directory: $profileDir" -ForegroundColor Yellow
    New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
}

# Back up existing profile if it exists
if (Test-Path -Path $profilePath) {
    $backupPath = "$profilePath.bak"
    Write-Host "Backing up existing profile to: $backupPath" -ForegroundColor Yellow
    Copy-Item -Path $profilePath -Destination $backupPath -Force

    # Read the existing profile
    $profileContent = Get-Content -Path $profilePath -Raw

    # Check if the profile already contains a reference to our script
    if ($profileContent -match 'BIG-Dynamic-Loader\.ps1') {
        Write-Host "Profile already contains reference to BIG-Dynamic-Loader. Updating..." -ForegroundColor Yellow

        # Regular expression to match the existing loader line
        $pattern = '# BIG Memory Bank System.*?\.\\s+".*?BIG-Dynamic-Loader\.ps1"'
        $replacement = "# BIG Memory Bank System - Dynamic Loader`n. `"$scriptPath`""

        # Replace existing loader line
        $profileContent = $profileContent -replace $pattern, $replacement
    }
    elseif ($profileContent -match 'BIG Memory Bank System') {
        Write-Host "Profile contains reference to BIG Memory Bank System. Updating..." -ForegroundColor Yellow

        # Regular expression to match the existing BIG loader line
        $pattern = '# BIG Memory Bank System.*?\..*?".*?BIG-Profile\.ps1"'
        $replacement = "# BIG Memory Bank System - Dynamic Loader`n. `"$scriptPath`""

        # Replace existing BIG loader line
        $profileContent = $profileContent -replace $pattern, $replacement
    }
    else {
        Write-Host "Adding BIG-Dynamic-Loader to profile..." -ForegroundColor Yellow

        # Add our loader to the end of the profile
        $profileContent += "`n`n# BIG Memory Bank System - Dynamic Loader`n. `"$scriptPath`""
    }

    # Write the updated profile
    Set-Content -Path $profilePath -Value $profileContent -Force
}
else {
    Write-Host "Creating new profile..." -ForegroundColor Yellow

    # Create basic profile with our loader
    $profileContent = @"
# PowerShell Profile

# BIG Memory Bank System - Dynamic Loader
. "$scriptPath"
"@
    Set-Content -Path $profilePath -Value $profileContent -Force
}

Write-Host "`nProfile updated successfully!" -ForegroundColor Green
Write-Host "The dynamic loader will find your BIG BRAIN environment automatically." -ForegroundColor Cyan
Write-Host "Please restart your PowerShell session to apply the changes." -ForegroundColor Yellow
