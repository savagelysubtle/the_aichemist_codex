# Rule File Standardization Script
# This script identifies rule files that need updating to match current standards:
# - XML aidecision tags with proper category attributes
# - Proper numeric prefixes in filenames
# - Flat structure with virtual nesting capabilities

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RulesDir = "D:\Coding\Python_Projects\the_aichemist_codex\.cursor\rules",

    [Parameter(Mandatory = $false)]
    [switch]$GenerateReport,

    [Parameter(Mandatory = $false)]
    [switch]$FixIssues
)

# Get script directory for reliable path resolution
$scriptDir = $PSScriptRoot
Write-Host "Script directory: $scriptDir" -ForegroundColor Cyan

# Check if the rules directory exists
if (-not (Test-Path $RulesDir)) {
    Write-Host "Error: Rules directory not found at $RulesDir" -ForegroundColor Red
    exit 1
}

Write-Host "Using rules directory: $RulesDir" -ForegroundColor Cyan

# Define the report file path (save in root directory)
$reportPath = "D:\Coding\Python_Projects\the_aichemist_codex\rule_standardization_report.md"
Write-Host "Report will be saved to: $reportPath" -ForegroundColor Cyan

# Valid categories mapping with their numeric prefix ranges
$categoryPrefixes = @{
    "BIG"           = @("0000", "00", "01", "02", "03", "04", "05", "06", "07", "08", "09")
    "MEMORY"        = @("000", "10", "11", "12", "13", "14", "15", "16", "17", "18")
    "VERIFICATION"  = @("20", "21")
    "COMMAND"       = @("42", "43")
    "RULES_STYLE"   = @("010", "020", "040", "500", "510", "520")
    "CREATIVE"      = @("021", "022")
    "EVALUATION"    = @("030", "031")
    "WORKFLOW"      = @("070", "080", "090")
    "DOCUMENTATION" = @("40", "41")
    "UTILITIES"     = @("530")
    "POWERSHELL"    = @("025")
    "TESTING"       = @("300")
    "PYTHON"        = @("100", "101", "102")
    "TEMPLATES"     = @("900")
}

# Function to check if a file contains double YAML frontmatter
function Test-YamlFrontmatter {
    param (
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )

    $content = Get-Content -Path $FilePath -Raw

    # Check for double YAML frontmatter pattern
    # First YAML block is expected as Cursor MDC header
    # We're looking for a second YAML block that needs to be converted to XML
    # Pattern: ---...(content)...--- followed by another ---...(content)...---

    # Count the number of YAML delimiters (---)
    $yamlDelimiters = [regex]::Matches($content, "^---\s*$|^---\s*\r?\n|\r?\n---\s*$|\r?\n---\s*\r?\n", [System.Text.RegularExpressions.RegexOptions]::Multiline)

    # If we have 4 or more delimiters, it indicates at least two YAML blocks
    # (each block has an opening and closing ---)
    if ($yamlDelimiters.Count -ge 4) {
        Write-Verbose "File $FilePath has multiple YAML blocks: $($yamlDelimiters.Count) delimiters found"
        return $true
    }

    # Alternative: Look for a pattern where a YAML block is followed by another
    $doubleYamlPattern = "(?:^|\r?\n)---\s*\r?\n.*?\r?\n---\s*(?:\r?\n|$).*?(?:^|\r?\n)---\s*\r?\n"
    if ($content -match $doubleYamlPattern) {
        Write-Verbose "File $FilePath has a second YAML block based on pattern matching"
        return $true
    }

    return $false
}

# Function to check if a file has the proper aidecision tag with category attribute
function Test-AidecisionFormat {
    param (
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )

    $content = Get-Content -Path $FilePath -Raw
    $hasAidecision = $content -match "<aidecision>"
    $hasCategory = $content -match "category\s*=\s*[""']([A-Z_]+)[""']"
    $proper = $hasAidecision -and $hasCategory

    $category = ""
    if ($hasCategory) {
        # Extract the category value
        if ($content -match "category\s*=\s*[""']([A-Z_]+)[""']") {
            $category = $matches[1]
        }
    }

    return @{
        HasAidecision  = $hasAidecision
        HasCategory    = $hasCategory
        Category       = $category
        IsProperFormat = $proper
    }
}

# Function to check if filename follows proper numbering convention
function Test-FileNameFormat {
    param (
        [Parameter(Mandatory = $true)]
        [string]$FileName,

        [Parameter(Mandatory = $false)]
        [string]$Category = ""
    )

    # Check if filename follows pattern: PREFIX-descriptive-name.mdc
    $prefixPattern = "^(\d{3,4})-([a-z0-9\-]+)\.mdc$"
    $isValidFormat = $FileName -match $prefixPattern

    $prefix = ""
    $isValidPrefix = $false
    $alignsWithCategory = $false

    if ($isValidFormat) {
        $prefix = $matches[1]

        # Check if the prefix belongs to any category
        $isValidPrefix = $false
        $matchingCategory = ""

        foreach ($cat in $categoryPrefixes.Keys) {
            foreach ($prefixRange in $categoryPrefixes[$cat]) {
                if ($prefix.StartsWith($prefixRange)) {
                    $isValidPrefix = $true
                    $matchingCategory = $cat
                    break
                }
            }
            if ($isValidPrefix) { break }
        }

        # Check if the prefix aligns with the category in metadata
        if ($Category -ne "" -and $isValidPrefix) {
            $alignsWithCategory = ($matchingCategory -eq $Category)
        }
    }

    return @{
        IsValidFormat      = $isValidFormat
        Prefix             = $prefix
        IsValidPrefix      = $isValidPrefix
        MatchingCategory   = $matchingCategory
        AlignsWithCategory = $alignsWithCategory
    }
}

# Get all .mdc files
$ruleFiles = Get-ChildItem -Path $RulesDir -Filter "*.mdc" -File | Where-Object { $_.Name -ne "README.mdc" -and $_.Name -ne "README-DEV.mdc" }

# Arrays to hold files with issues
$yamlFiles = @()
$missingCategory = @()
$missingAidecision = @()
$improperFileNames = @()
$categoryMismatch = @()
$properFiles = @()

foreach ($file in $ruleFiles) {
    $hasYaml = Test-YamlFrontmatter -FilePath $file.FullName
    $aidecisionTest = Test-AidecisionFormat -FilePath $file.FullName

    $fileNameTest = Test-FileNameFormat -FileName $file.Name
    if ($aidecisionTest.HasCategory) {
        $fileNameTest = Test-FileNameFormat -FileName $file.Name -Category $aidecisionTest.Category
    }

    # Categorize the file based on tests
    if ($hasYaml) {
        $yamlFiles += $file
    }

    if (-not $aidecisionTest.HasAidecision) {
        $missingAidecision += $file
    }
    elseif (-not $aidecisionTest.HasCategory) {
        $missingCategory += $file
    }

    if (-not $fileNameTest.IsValidFormat -or -not $fileNameTest.IsValidPrefix) {
        $improperFileNames += @{
            File = $file
            Test = $fileNameTest
        }
    }

    if ($aidecisionTest.HasCategory -and $fileNameTest.IsValidPrefix -and -not $fileNameTest.AlignsWithCategory) {
        $categoryMismatch += @{
            File             = $file
            ExpectedCategory = $fileNameTest.MatchingCategory
            ActualCategory   = $aidecisionTest.Category
        }
    }

    # Proper files have XML format, valid prefixes, and matching categories
    if (-not $hasYaml -and $aidecisionTest.IsProperFormat -and
        $fileNameTest.IsValidFormat -and $fileNameTest.IsValidPrefix -and
        ($fileNameTest.AlignsWithCategory -or -not $aidecisionTest.HasCategory)) {
        $properFiles += $file
    }
}

# Check VS Code settings file for nesting configuration
$vsCodeSettingsPath = ".vscode/settings.json"
$nestedPatternsConfigured = $false
if (Test-Path $vsCodeSettingsPath) {
    $settingsContent = Get-Content -Path $vsCodeSettingsPath -Raw
    $nestedPatternsConfigured = $settingsContent -match "explorer.fileNesting.patterns"
}

# Display results
Write-Host "Rules Standardization Report" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host "Total rule files: $($ruleFiles.Count)" -ForegroundColor White
Write-Host "Files with double YAML frontmatter: $($yamlFiles.Count)" -ForegroundColor Yellow
Write-Host "Files missing aidecision tags: $($missingAidecision.Count)" -ForegroundColor Red
Write-Host "Files missing category attribute: $($missingCategory.Count)" -ForegroundColor Magenta
Write-Host "Files with improper naming: $($improperFileNames.Count)" -ForegroundColor Yellow
Write-Host "Files with category/prefix mismatch: $($categoryMismatch.Count)" -ForegroundColor Yellow
Write-Host "VS Code nesting patterns configured: $($nestedPatternsConfigured)" -ForegroundColor $(if ($nestedPatternsConfigured) { "Green" } else { "Red" })
Write-Host "Properly formatted files: $($properFiles.Count)" -ForegroundColor Green

# Generate detailed report if requested
if ($GenerateReport) {
    $report = @"
# Rules Standardization Report
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Summary
- Total rule files: $($ruleFiles.Count)
- Files with double YAML frontmatter: $($yamlFiles.Count)
- Files missing aidecision tags: $($missingAidecision.Count)
- Files missing category attribute: $($missingCategory.Count)
- Files with improper naming: $($improperFileNames.Count)
- Files with category/prefix mismatch: $($categoryMismatch.Count)
- VS Code nesting patterns configured: $($nestedPatternsConfigured)
- Properly formatted files: $($properFiles.Count)

## Files with Double YAML Frontmatter
These files need to have their second YAML block converted to XML aidecision tags:

$(foreach ($file in $yamlFiles) { "- $($file.Name)`n" })

## Files Missing aidecision Tags
These files need aidecision tags added:

$(foreach ($file in $missingAidecision) { "- $($file.Name)`n" })

## Files Missing category Attribute
These files need to have the category attribute added to their aidecision tags:

$(foreach ($file in $missingCategory) { "- $($file.Name)`n" })

## Files with Improper Naming Conventions
These files need to be renamed to follow the PREFIX-descriptive-name.mdc pattern with valid prefix:

$(foreach ($item in $improperFileNames) { "- $($item.File.Name) - $(if(-not $item.Test.IsValidFormat){"Invalid format"}elseif(-not $item.Test.IsValidPrefix){"Invalid prefix"})`n" })

## Files with Category/Prefix Mismatch
These files have a category attribute that doesn't match their filename prefix:

$(foreach ($item in $categoryMismatch) { "- $($item.File.Name) - Expected: $($item.ExpectedCategory), Actual: $($item.ActualCategory)`n" })

## Next Steps
1. Convert second YAML block to XML aidecision tags
2. Add missing aidecision tags
3. Add missing category attributes
4. Rename files to follow proper naming conventions
5. Correct category mismatches
6. Update VS Code settings for virtual nesting if needed
"@

    $report | Out-File -FilePath $reportPath
    Write-Host "Detailed report saved to: $reportPath" -ForegroundColor Green
}

# If FixIssues switch is provided, offer to fix some issues automatically
if ($FixIssues) {
    Write-Host "`nAutomated fixes are not implemented in this version of the script." -ForegroundColor Yellow
    Write-Host "Please review the report and make manual corrections." -ForegroundColor Yellow
}
