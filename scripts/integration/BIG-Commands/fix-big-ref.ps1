# fix-big-ref.ps1
# Script to fix the PowerShell profile references to use the correct BIG scripts
# Version 1.0.0
# Created: 2025-04-01

Write-Host "BIG Reference Fixer" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host ""

# Get the current directory of this script
$scriptDir = $PSScriptRoot
Write-Host "Script directory: $scriptDir" -ForegroundColor Cyan

# Get the path to our new dynamic loader
$dynamicLoaderPath = Join-Path -Path $scriptDir -ChildPath "BIG-Dynamic-Loader.ps1"

# Get user's PowerShell profile path
$profilePath = $PROFILE.CurrentUserAllHosts
Write-Host "PowerShell profile path: $profilePath" -ForegroundColor Cyan

# Make sure profile directory exists
$profileDir = Split-Path -Parent $profilePath
if (-not (Test-Path -Path $profileDir)) {
    try {
        New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
        Write-Host "Created PowerShell profile directory: $profileDir" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to create PowerShell profile directory: $profileDir" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        exit 1
    }
}

# Create backup of existing profile if it exists
if (Test-Path -Path $profilePath) {
    $backupPath = "$profilePath.bak"
    try {
        Copy-Item -Path $profilePath -Destination $backupPath -Force
        Write-Host "Created backup of existing profile at: $backupPath" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to create backup of profile: $_" -ForegroundColor Red
        exit 1
    }

    # Read current profile content
    $profileContent = Get-Content -Path $profilePath -Raw -ErrorAction SilentlyContinue

    # Check if it contains any references to TheMemoryBank or BIG-Profile.ps1
    $oldPatterns = @(
        'TheMemoryBank\\scripts\\profiles\\BIG-Profile\.ps1',
        'TheMemoryBank\\scripts\\BIG-Commands\\BIG\.ps1',
        'BIG-Profile\.ps1'
    )

    $needsUpdate = $false
    foreach ($pattern in $oldPatterns) {
        if ($profileContent -match $pattern) {
            $needsUpdate = $true
            Write-Host "Found old reference: $pattern" -ForegroundColor Yellow
            break
        }
    }

    if ($needsUpdate) {
        Write-Host "Updating PowerShell profile to use the dynamic loader..." -ForegroundColor Cyan

        # Create the new loader reference
        $newLoaderRef = ". `"$dynamicLoaderPath`""

        # Replace old BIG-Profile or BIG script references with our new dynamic loader
        $updatedContent = $profileContent -replace '\.[\s]*["\'].*?(BIG-Profile\.ps1 | BIG\.ps1 | BIG-Dynamic-Loader\.ps1)["\']', $newLoaderRef

        # If no replacement was made, append the loader reference
        if ($updatedContent -eq $profileContent) {
            if ($profileContent.EndsWith("`n")) {
                $updatedContent = $profileContent + $newLoaderRef
            }
            else {
                $updatedContent = $profileContent + "`n" + $newLoaderRef
            }
        }

        # Write the updated content back to the profile
        try {
            Set-Content -Path $profilePath -Value $updatedContent -Force
            Write-Host "Successfully updated PowerShell profile!" -ForegroundColor Green
            Write-Host "The profile now references: $dynamicLoaderPath" -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to update PowerShell profile: $_" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "No old references found in the profile. Adding dynamic loader..." -ForegroundColor Cyan

        # Append the dynamic loader to the profile
        $newLoaderRef = ". `"$dynamicLoaderPath`""
        if ($profileContent.EndsWith("`n")) {
            $updatedContent = $profileContent + $newLoaderRef
        }
        else {
            $updatedContent = $profileContent + "`n" + $newLoaderRef
        }

        # Write the updated content back to the profile
        try {
            Set-Content -Path $profilePath -Value $updatedContent -Force
            Write-Host "Successfully added dynamic loader to PowerShell profile!" -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to update PowerShell profile: $_" -ForegroundColor Red
            exit 1
        }
    }
}
else {
    # Create a new profile with the dynamic loader
    Write-Host "Creating new PowerShell profile with dynamic loader..." -ForegroundColor Cyan

    $newLoaderRef = "# PowerShell profile created by BIG fix-big-ref.ps1`n. `"$dynamicLoaderPath`""

    try {
        Set-Content -Path $profilePath -Value $newLoaderRef -Force
        Write-Host "Successfully created PowerShell profile with dynamic loader!" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to create PowerShell profile: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Profile update complete!" -ForegroundColor Cyan
Write-Host "Please restart your PowerShell session or reload your profile with the command:" -ForegroundColor Cyan
Write-Host ". `$PROFILE.CurrentUserAllHosts" -ForegroundColor Yellow
Write-Host ""
Write-Host "After restarting, the 'big' command will use the current project's BIG-Codebase.ps1 script." -ForegroundColor Cyan
