# Duplicate Content Finder Script
# This script identifies potential duplicate content between RST and MD files

# Function to get a normalized version of file content for comparison
function Get-NormalizedContent {
    param (
        [string]$filePath
    )

    $content = Get-Content -Path $filePath -Raw

    # For RST files, remove RST-specific formatting like headings, directives, etc.
    if ($filePath -like "*.rst") {
        # Remove RST heading underlines (====, ----, etc.)
        $content = $content -replace '[\=\-\~\^]+\n', ''
        # Remove RST directives
        $content = $content -replace '\.\. [a-z]+::.+\n', ''
        # Remove code blocks
        $content = $content -replace '\.\. code-block::.+\n', ''
    }

    # For MD files, remove markdown-specific formatting
    if ($filePath -like "*.md") {
        # Remove MD headings
        $content = $content -replace '#+ .+\n', ''
        # Remove code blocks
        $content = $content -replace '```[a-z]*\n', ''
        $content = $content -replace '```\n', ''
    }

    # Remove all whitespace and newlines for content comparison
    $content = $content -replace '\s+', ''
    return $content
}

# Function to compare file content and determine similarity
function Compare-FileContent {
    param (
        [string]$file1,
        [string]$file2
    )

    $content1 = Get-NormalizedContent -filePath $file1
    $content2 = Get-NormalizedContent -filePath $file2

    # If either file is empty, return 0
    if ($content1.Length -eq 0 -or $content2.Length -eq 0) {
        return 0
    }

    # Simple similarity calculation based on common substring detection
    # This is a basic approach and might not be perfect
    $minLength = [Math]::Min($content1.Length, $content2.Length)
    $maxLength = [Math]::Max($content1.Length, $content2.Length)

    # Find longest common substring (simplified approach)
    $commonChars = 0
    for ($i = 0; $i -lt $minLength; $i++) {
        if ($content1[$i] -eq $content2[$i]) {
            $commonChars++
        }
    }

    # Calculate similarity percentage
    $similarity = [Math]::Round(($commonChars / $maxLength) * 100, 2)
    return $similarity
}

# Get all RST and MD files
$rstFiles = Get-ChildItem -Path "docs" -Filter "*.rst" -Recurse
$mdFiles = Get-ChildItem -Path "docs\markdown" -Filter "*.md" -Recurse

# Create a report file
$reportFile = "docs\duplicate_content_report.md"
"# Duplicate Content Report`n" | Out-File -FilePath $reportFile
"This report lists potential duplicate content between RST and MD files.`n" | Out-File -FilePath $reportFile -Append
"## High Similarity Files (>70% similar)`n" | Out-File -FilePath $reportFile -Append
"| RST File | MD File | Similarity % |" | Out-File -FilePath $reportFile -Append
"|---------|---------|--------------|" | Out-File -FilePath $reportFile -Append

$highSimilarityFound = $false
$moderateSimilarityFound = $false

# Check each RST file against each MD file
foreach ($rstFile in $rstFiles) {
    foreach ($mdFile in $mdFiles) {
        # Get base filenames without extension
        $rstBaseName = $rstFile.BaseName
        $mdBaseName = $mdFile.BaseName

        # Skip if the base names are completely different
        # (to reduce unnecessary comparisons)
        if (-not ($rstBaseName -like "*$mdBaseName*" -or $mdBaseName -like "*$rstBaseName*")) {
            continue
        }

        # Compare content
        $similarity = Compare-FileContent -file1 $rstFile.FullName -file2 $mdFile.FullName

        # Log high similarity files
        if ($similarity -gt 70) {
            $highSimilarityFound = $true
            "| $($rstFile.FullName) | $($mdFile.FullName) | $similarity% |" | Out-File -FilePath $reportFile -Append
            Write-Host "High similarity ($similarity%) between $($rstFile.Name) and $($mdFile.Name)" -ForegroundColor Yellow
        }
        # Track moderate similarity for separate section
        elseif ($similarity -gt 40) {
            $moderateSimilarityFound = $true
            if (-not $moderateSimilaritiesHeader) {
                "`n## Moderate Similarity Files (40-70% similar)`n" | Out-File -FilePath $reportFile -Append
                "| RST File | MD File | Similarity % |" | Out-File -FilePath $reportFile -Append
                "|---------|---------|--------------|" | Out-File -FilePath $reportFile -Append
                $moderateSimilaritiesHeader = $true
            }
            "| $($rstFile.FullName) | $($mdFile.FullName) | $similarity% |" | Out-File -FilePath $reportFile -Append
        }
    }
}

if (-not $highSimilarityFound) {
    "No files with high similarity found." | Out-File -FilePath $reportFile -Append
}

if (-not $moderateSimilarityFound -and $moderateSimilaritiesHeader) {
    "No files with moderate similarity found." | Out-File -FilePath $reportFile -Append
}

"`n## Recommendations`n" | Out-File -FilePath $reportFile -Append
"For files with high similarity (>70%):" | Out-File -FilePath $reportFile -Append
"1. Consider keeping only one version (preferably the RST file for Sphinx documentation)" | Out-File -FilePath $reportFile -Append
"2. If both formats are needed, ensure they are kept in sync or one is generated from the other" | Out-File -FilePath $reportFile -Append
"3. Add cross-references between related files" | Out-File -FilePath $reportFile -Append

"`nFor files with moderate similarity (40-70%):" | Out-File -FilePath $reportFile -Append
"1. Review to determine if they contain duplicate information" | Out-File -FilePath $reportFile -Append
"2. Consider consolidating related information" | Out-File -FilePath $reportFile -Append
"3. Add cross-references if they are complementary" | Out-File -FilePath $reportFile -Append

Write-Host "Duplicate content analysis complete. Report saved to $reportFile" -ForegroundColor Green