#############################################################
# BIG-Help.ps1
# Helper script for BIG Commands and Patterns
# Created: $(Get-Date -Format "yyyy-MM-dd")
#############################################################

# Script Parameters
param(
    [Parameter(Mandatory = $false)]
    [switch]$DryRun = $true, # Default to dry run mode for safety

    [Parameter(Mandatory = $false)]
    [string]$WorkFolder = "$PSScriptRoot\workspace",

    [Parameter(Mandatory = $false)]
    [string]$Command = "",

    [Parameter(Mandatory = $false)]
    [string]$Pattern = "",

    [Parameter(Mandatory = $false)]
    [switch]$ListCommands,

    [Parameter(Mandatory = $false)]
    [switch]$ListPatterns,

    [Parameter(Mandatory = $false)]
    [switch]$FixMdcGlobs
)

#############################################################
# Configuration and Paths
#############################################################

$ErrorActionPreference = "Stop"
$CommandsPath = "$PSScriptRoot\.."
$PatternsPath = "$PSScriptRoot\..\..\..\..\.cursor\rules\codebase\Patterns"
$RulesPath = "$PSScriptRoot\..\..\..\..\.cursor\rules"

# Ensure the work folder exists
if (-not (Test-Path -Path $WorkFolder)) {
    New-Item -ItemType Directory -Path $WorkFolder -Force | Out-Null
    Write-Host "Created work folder at: $WorkFolder" -ForegroundColor Green
}

#############################################################
# Helper Functions
#############################################################

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO",
        [string]$Color = "White"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $Color
}

function Test-DryRun {
    param(
        [string]$Action,
        [scriptblock]$ScriptBlock
    )

    if ($DryRun) {
        Write-Status "DRY RUN: Would $Action" -Status "DRY" -Color "Yellow"
        return $true
    }
    else {
        try {
            & $ScriptBlock
            return $true
        }
        catch {
            Write-Status "Error during $Action`: $_" -Status "ERROR" -Color "Red"
            return $false
        }
    }
}

function Get-MdcFiles {
    param(
        [string]$Path
    )

    Get-ChildItem -Path $Path -Recurse -Filter "*.mdc" -File
}

#############################################################
# MDC Glob Pattern Fix Functions
#############################################################

function Fix-MdcGlobPattern {
    param(
        [string]$FilePath,
        [switch]$BackupFile = $true
    )

    if (-not (Test-Path $FilePath)) {
        Write-Status "File not found: $FilePath" -Status "ERROR" -Color "Red"
        return $false
    }

    $content = Get-Content -Path $FilePath -Raw
    $needsUpdate = $false

    # Fix glob patterns with quotes and brackets
    if ($content -match 'globs:\s*\[(.*?)\]') {
        $newContent = $content -replace 'globs:\s*\[(.*?)\]', 'globs: $1'
        $newContent = $newContent -replace '["'']', ''  # Remove any quotes
        $needsUpdate = $true
    }

    if ($needsUpdate) {
        if ($BackupFile) {
            $backupPath = "$FilePath.backup"
            Test-DryRun "create backup at $backupPath" {
                Copy-Item -Path $FilePath -Destination $backupPath
            }
        }

        Test-DryRun "update file $FilePath" {
            $newContent | Set-Content -Path $FilePath -NoNewline
        }

        Write-Status "Fixed glob pattern in $FilePath" -Status "FIXED" -Color "Green"
        return $true
    }
    else {
        Write-Status "No glob pattern issues found in $FilePath" -Status "OK" -Color "Green"
        return $false
    }
}

function Fix-AllMdcGlobPatterns {
    $mdcFiles = Get-MdcFiles -Path $RulesPath

    Write-Status "Found $($mdcFiles.Count) MDC files to check" -Status "INFO" -Color "Cyan"

    $fixedCount = 0
    foreach ($file in $mdcFiles) {
        $fixed = Fix-MdcGlobPattern -FilePath $file.FullName
        if ($fixed) { $fixedCount++ }
    }

    Write-Status "Fixed glob patterns in $fixedCount files" -Status "COMPLETE" -Color "Green"
}

#############################################################
# Commands Help Functions
#############################################################

function Get-BigCommands {
    $commands = @()

    Get-ChildItem -Path $CommandsPath -Filter "BIG-*.ps1" -File | ForEach-Object {
        $name = $_.BaseName
        $content = Get-Content -Path $_.FullName -Raw -ErrorAction SilentlyContinue

        # Extract description from comments
        $description = ""
        if ($content -and $content -match '# .*?\n# (.*?)(?:\n#|\n|\z)') {
            $description = $matches[1].Trim()
        }

        # Extract parameters
        $parameters = [System.Collections.ArrayList]::new()
        if ($content -and $content -match 'param\s*\((.*?)\)' -and $matches[1]) {
            $paramSection = $matches[1]
            $paramMatches = [regex]::Matches($paramSection, '\[Parameter.*?\]\s*\[.*?\]\$(\w+)(?:\s*=\s*([^,\s\)]+))?')

            foreach ($match in $paramMatches) {
                $paramName = $match.Groups[1].Value
                $defaultValue = if ($match.Groups[2].Success) { $match.Groups[2].Value } else { "None" }

                [void]$parameters.Add(@{
                        Name         = $paramName
                        DefaultValue = $defaultValue
                    })
            }
        }

        $commands += [PSCustomObject]@{
            Name        = $name
            Description = $description
            Parameters  = $parameters
            Path        = $_.FullName
        }
    }

    return $commands
}

function Show-BigCommands {
    $commands = Get-BigCommands

    Write-Host "`nAvailable BIG Commands:" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan

    foreach ($cmd in $commands) {
        Write-Host "`n$($cmd.Name)" -ForegroundColor Yellow
        Write-Host "  Description: $($cmd.Description)" -ForegroundColor White

        if ($cmd.Parameters.Count -gt 0) {
            Write-Host "  Parameters:" -ForegroundColor White
            foreach ($param in $cmd.Parameters) {
                Write-Host "    -$($param.Name)" -ForegroundColor Gray -NoNewline
                if ($param.DefaultValue -ne "None") {
                    Write-Host " (default: $($param.DefaultValue))" -ForegroundColor DarkGray
                }
                else {
                    Write-Host ""
                }
            }
        }
    }
}

function Show-CommandHelp {
    param(
        [string]$CommandName
    )

    $commands = Get-BigCommands
    $command = $commands | Where-Object { $_.Name -eq $CommandName }

    if (-not $command) {
        Write-Status "Command not found: $CommandName" -Status "ERROR" -Color "Red"
        Write-Host "Available commands: $($commands.Name -join ', ')" -ForegroundColor Yellow
        return
    }

    # Get the README file for more detailed help if it exists
    $readmeFile = "$CommandsPath\README-$($CommandName.Replace('BIG-', '')).md"
    $readmeContent = if (Test-Path $readmeFile) {
        Get-Content -Path $readmeFile -Raw -ErrorAction SilentlyContinue
    }
    else {
        $null
    }

    # Display help
    Write-Host "`n$($command.Name) Command Help" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host "Description: $($command.Description)" -ForegroundColor White

    if ($command.Parameters.Count -gt 0) {
        Write-Host "`nParameters:" -ForegroundColor White
        foreach ($param in $command.Parameters) {
            Write-Host "  -$($param.Name)" -ForegroundColor Yellow -NoNewline
            if ($param.DefaultValue -ne "None") {
                Write-Host " (default: $($param.DefaultValue))" -ForegroundColor DarkGray
            }
            else {
                Write-Host ""
            }
        }
    }

    Write-Host "`nExamples:" -ForegroundColor White
    Write-Host "  ./$($command.Name).ps1" -ForegroundColor Gray

    if ($command.Parameters.Count -gt 0) {
        $exampleParams = $command.Parameters | ForEach-Object { "-$($_.Name)" } | Select-Object -First 2
        Write-Host "  ./$($command.Name).ps1 $($exampleParams -join ' ')" -ForegroundColor Gray
    }

    if ($readmeContent) {
        Write-Host "`nDetailed Documentation:" -ForegroundColor White
        $summaryMatch = [regex]::Match($readmeContent, '# .*?\n\n(.*?)(?=\n## |\z)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
        if ($summaryMatch.Success) {
            Write-Host $summaryMatch.Groups[1].Value.Trim() -ForegroundColor Gray
        }

        Write-Host "`nSee full documentation in: $readmeFile" -ForegroundColor DarkGray
    }
}

#############################################################
# Patterns Help Functions
#############################################################

function Get-Patterns {
    $patterns = @()
    $patternFolders = Get-ChildItem -Path $PatternsPath -Directory -ErrorAction SilentlyContinue

    if (-not $patternFolders) {
        Write-Status "No pattern folders found at: $PatternsPath" -Status "WARNING" -Color "Yellow"
        return $patterns
    }

    foreach ($folder in $patternFolders) {
        $readmeFile = "$($folder.FullName)\README.md"
        $description = "No description available"

        if (Test-Path $readmeFile) {
            $content = Get-Content -Path $readmeFile -Raw -ErrorAction SilentlyContinue
            if ($content -and $content -match '# .*?\n\n(.*?)(?=\n## |\z)') {
                $description = $matches[1].Trim()
            }
        }

        $patternFiles = @(Get-ChildItem -Path $folder.FullName -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -ne ".md" })

        $patterns += [PSCustomObject]@{
            Name        = $folder.Name
            Description = $description
            Path        = $folder.FullName
            FileCount   = $patternFiles.Count
        }
    }

    return $patterns
}

function Show-Patterns {
    $patterns = Get-Patterns

    Write-Host "`nAvailable Code Patterns:" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan

    foreach ($pattern in $patterns) {
        Write-Host "`n$($pattern.Name)" -ForegroundColor Yellow
        Write-Host "  Description: $($pattern.Description)" -ForegroundColor White
        Write-Host "  Files: $($pattern.FileCount)" -ForegroundColor Gray
        Write-Host "  Path: $($pattern.Path)" -ForegroundColor DarkGray
    }
}

function Show-PatternHelp {
    param(
        [string]$PatternName
    )

    $patterns = Get-Patterns
    $pattern = $patterns | Where-Object { $_.Name -eq $PatternName }

    if (-not $pattern) {
        Write-Status "Pattern not found: $PatternName" -Status "ERROR" -Color "Red"
        Write-Host "Available patterns: $($patterns.Name -join ', ')" -ForegroundColor Yellow
        return
    }

    # Get the README file
    $readmeFile = "$($pattern.Path)\README.md"
    $readmeContent = if (Test-Path $readmeFile) {
        Get-Content -Path $readmeFile -Raw -ErrorAction SilentlyContinue
    }
    else {
        $null
    }

    # Display help
    Write-Host "`n$($pattern.Name) Pattern Help" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host "Description: $($pattern.Description)" -ForegroundColor White

    if ($readmeContent) {
        # Extract sections from README
        $sections = [regex]::Matches($readmeContent, '## (.*?)\n\n(.*?)(?=\n## |\z)', [System.Text.RegularExpressions.RegexOptions]::Singleline)

        foreach ($section in $sections) {
            $sectionTitle = $section.Groups[1].Value.Trim()
            $sectionContent = $section.Groups[2].Value.Trim()

            Write-Host "`n$sectionTitle" -ForegroundColor Yellow -NoNewline
            Write-Host ":" -ForegroundColor Yellow
            Write-Host $sectionContent -ForegroundColor Gray
        }
    }

    # List pattern files
    $patternFiles = @(Get-ChildItem -Path $pattern.Path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -ne ".md" })

    Write-Host "`nPattern Files:" -ForegroundColor White
    foreach ($file in $patternFiles) {
        $relativePath = $file.FullName.Replace($pattern.Path, "").TrimStart("\")
        Write-Host "  $relativePath" -ForegroundColor Gray
    }
}

#############################################################
# Main Script Logic
#############################################################

# Display script banner
Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "BIG-Help.ps1 - Helper for BIG Commands and Patterns" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Mode: $(if ($DryRun) { 'DRY RUN (safe mode)' } else { 'LIVE RUN' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Green' })
Write-Host "Work Folder: $(Resolve-Path $WorkFolder -ErrorAction SilentlyContinue)" -ForegroundColor White
Write-Host "Commands Path: $(Resolve-Path $CommandsPath -ErrorAction SilentlyContinue)" -ForegroundColor White
Write-Host "Patterns Path: $(if (Test-Path $PatternsPath) { Resolve-Path $PatternsPath } else { $PatternsPath })" -ForegroundColor White
Write-Host "Rules Path: $(if (Test-Path $RulesPath) { Resolve-Path $RulesPath } else { $RulesPath })" -ForegroundColor White
Write-Host "=========================================================`n" -ForegroundColor Cyan

# Handle command actions based on parameters
if ($FixMdcGlobs) {
    Write-Status "Checking MDC files for glob pattern issues..." -Status "START" -Color "Cyan"
    Fix-AllMdcGlobPatterns
}

if ($ListCommands) {
    Show-BigCommands
}

if ($ListPatterns) {
    Show-Patterns
}

if ($Command) {
    Show-CommandHelp -CommandName $Command
}

if ($Pattern) {
    Show-PatternHelp -PatternName $Pattern
}

# If no specific action parameter was provided, show usage information
if (-not ($ListCommands -or $ListPatterns -or $Command -or $Pattern -or $FixMdcGlobs)) {
    Write-Host "`nUsage Information:" -ForegroundColor Cyan
    Write-Host "-----------------" -ForegroundColor Cyan
    Write-Host ".\BIG-Help.ps1 -ListCommands           # List all BIG Commands" -ForegroundColor White
    Write-Host ".\BIG-Help.ps1 -ListPatterns           # List all code Patterns" -ForegroundColor White
    Write-Host ".\BIG-Help.ps1 -Command BIG-Rules      # Show help for specific command" -ForegroundColor White
    Write-Host ".\BIG-Help.ps1 -Pattern ModularCode    # Show help for specific pattern" -ForegroundColor White
    Write-Host ".\BIG-Help.ps1 -FixMdcGlobs            # Fix MDC glob patterns format" -ForegroundColor White
    Write-Host ".\BIG-Help.ps1 -DryRun 0               # Run in live mode (not dry run)" -ForegroundColor White
    Write-Host ".\BIG-Help.ps1 -WorkFolder 'C:\Temp'   # Set custom work folder" -ForegroundColor White
}

Write-Host "`n"
