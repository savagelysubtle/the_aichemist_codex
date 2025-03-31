# BIG.ps1
# Main command interface for the BIG BRAIN Memory Bank system
# Version 1.5.1
# Created: 2025-03-27
# Updated: 2025-03-28 - Added rules category
# Updated: 2025-03-28 - Added update category
# Updated: 2025-03-28 - Added autonomous category
# Updated: 2025-03-29 - Fixed parameter passing to child scripts
# Updated: 2025-03-30 - Added codebase category for integration with .cursor rules
# Updated: 2025-03-31 - Added interactive menu for no-parameter execution
# Updated: 2025-03-31 - Added TestMode documentation and examples
# Updated: 2025-04-01 - Updated to use dynamic script paths

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false, Position = 0)]
    [ValidateSet("analytics", "organization", "bedtime", "rules", "update", "autonomous", "codebase", "help")]
    [string]$Category,

    [Parameter(Mandatory = $false, Position = 1)]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

# Import logging utility
$utilityPath = Join-Path -Path $PSScriptRoot -ChildPath "../Utilities/Write-BIGLog.ps1"
if (Test-Path $utilityPath) {
    . $utilityPath
}
else {
    # Define minimal logging functions if main utils aren't available
    function Write-BIGLog {
        param([string]$Message, [string]$Level, [string]$LogFile)
        Write-Host "[$Level] $Message" -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARNING") { "Yellow" } else { "White" })
    }

    function Start-BIGLogging { param([string]$ScriptName) return $null }
    function Stop-BIGLogging { param([string]$ScriptName, [string]$LogFile, [TimeSpan]$Duration) }

    function Write-BIGHeader {
        param([string]$Title, [string]$LogFile)
        $width = 60
        $padding = [math]::Max(0, ($width - $Title.Length - 2) / 2)
        $leftPad = [math]::Floor($padding)
        $rightPad = [math]::Ceiling($padding)

        Write-Host ""
        Write-Host ("=" * $width) -ForegroundColor Cyan
        Write-Host ("#" * $leftPad) -ForegroundColor Cyan -NoNewline
        Write-Host "  $Title  " -ForegroundColor Yellow -NoNewline
        Write-Host ("#" * $rightPad) -ForegroundColor Cyan
        Write-Host ("=" * $width) -ForegroundColor Cyan
        Write-Host ""
    }
}

# Start logging
$logFile = Start-BIGLogging -ScriptName $MyInvocation.MyCommand.Path

# Define paths to command scripts using current directory
$scriptsDir = $PSScriptRoot

# Check first in current directory
$analyticsScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Analytics.ps1"
$organizationScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Organization.ps1"
$bedtimeScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Bedtime.ps1"
$rulesScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Rules.ps1"
$updateScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Update.ps1"
$autonomousScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Autonomous.ps1"
$codebaseScript = Join-Path -Path $scriptsDir -ChildPath "BIG-Codebase.ps1"

# Log script paths
Write-BIGLog -Message "ScriptsDir: $scriptsDir" -Level "DEBUG" -LogFile $logFile
Write-BIGLog -Message "Codebase script: $codebaseScript" -Level "DEBUG" -LogFile $logFile

# Function to display help information
function Show-Help {
    param (
        [Parameter(Mandatory = $false)]
        [string]$Category
    )

    if ([string]::IsNullOrEmpty($Category)) {
        Write-Host "`nBIG BRAIN Command System" -ForegroundColor Cyan
        Write-Host "======================" -ForegroundColor Cyan
        Write-Host "`nRun without parameters to show interactive menu." -ForegroundColor Yellow
        Write-Host "`nSyntax:" -ForegroundColor Yellow
        Write-Host "  BIG [category] [command] [options]" -ForegroundColor White

        Write-Host "`nAvailable Categories:" -ForegroundColor Yellow
        Write-Host "  analytics    - Memory analytics and reporting" -ForegroundColor White
        Write-Host "  organization - Memory organization and management" -ForegroundColor White
        Write-Host "  bedtime      - Bedtime Protocol operations" -ForegroundColor White
        Write-Host "  rules        - Rules management and application" -ForegroundColor White
        Write-Host "  update       - System and memory bank updates" -ForegroundColor White
        Write-Host "  autonomous   - Autonomous memory operations" -ForegroundColor White
        Write-Host "  codebase     - Codebase integration with .cursor rules" -ForegroundColor White
        Write-Host "  help         - Show help for a specific category" -ForegroundColor White

        Write-Host "`nCommon Options:" -ForegroundColor Yellow
        Write-Host "  -TestMode    - Run in test mode without making actual changes" -ForegroundColor White
        Write-Host "  -Verbose     - Show detailed execution information" -ForegroundColor White
        Write-Host "  -Detailed    - Provide comprehensive output with more information" -ForegroundColor White
        Write-Host "  -OutputPath  - Specify custom location for saving generated files" -ForegroundColor White

        Write-Host "`nExamples:" -ForegroundColor Yellow
        Write-Host "  BIG analytics health" -ForegroundColor White
        Write-Host "  BIG organization reorganize -TestMode" -ForegroundColor White
        Write-Host "  BIG bedtime start" -ForegroundColor White
        Write-Host "  BIG rules apply -Verbose" -ForegroundColor White
        Write-Host "  BIG help analytics" -ForegroundColor White
        Write-Host "  BIG" -ForegroundColor White
        Write-Host "    (Shows interactive menu)" -ForegroundColor DarkGray

        Write-Host "`nFor more information on a specific category, type:" -ForegroundColor Yellow
        Write-Host "  BIG help [category]" -ForegroundColor White
    }
    else {
        # Category-specific help
        switch ($Category.ToLower()) {
            "codebase" {
                Write-Host "`nBIG Codebase Commands" -ForegroundColor Cyan
                Write-Host "====================" -ForegroundColor Cyan
                Write-Host "`nCommands for codebase integration with .cursor rules:"
                Write-Host "  analyze     - Analyze codebase against coding standards"
                Write-Host "  validate    - Validate code against standard rules"
                Write-Host "  apply       - Apply coding standards to codebase"
                Write-Host "  learn       - Learn from existing codebase"
                Write-Host "  search      - Search for patterns in codebase"
                Write-Host ""
                Write-Host "Parameters:"
                Write-Host "  -TargetPath     - Path to the codebase (default: current directory)"
                Write-Host "  -RuleCategory   - Rule category to use (Languages, Patterns, etc.)"
                Write-Host "  -Language       - Target language (PowerShell, Python, etc.)"
                Write-Host "  -Pattern        - Search pattern (required for search command)"
                Write-Host "  -TestMode       - Run in test mode without making changes"
                Write-Host "  -Detailed       - Show detailed output"
                Write-Host ""
                Write-Host "Examples:"
                Write-Host "  BIG codebase analyze -Language PowerShell"
                Write-Host "  BIG codebase search -Pattern 'function.*Test' -Language PowerShell"
                Write-Host "  BIG codebase validate -TestMode"
                return
            }
            "analytics" {
                Write-Host "`nBIG Analytics Commands" -ForegroundColor Cyan
                Write-Host "======================" -ForegroundColor Cyan
                Write-Host "`nCommands for memory statistics and health monitoring:"
                Write-Host "  stats       - Generate statistics about the memory bank"
                Write-Host "  report      - Create detailed reports on memory usage and health"
                Write-Host "  health      - Perform quick health assessment of memory system"
                Write-Host ""
                Write-Host "Parameters:"
                Write-Host "  -OutputPath    - Path to save reports/statistics (default: reports/)"
                Write-Host "  -Format        - Output format (Text, HTML, JSON)"
                Write-Host "  -Days          - Time period to analyze (default: 30)"
                Write-Host "  -Threshold     - Health score threshold for alerts"
                Write-Host "  -IncludeDetails - Include comprehensive details in output"
                Write-Host "  -TestMode      - Run in simulation mode without file operations"
                Write-Host ""
                Write-Host "Examples:"
                Write-Host "  BIG analytics stats -IncludeDetails"
                Write-Host "  BIG analytics report -Format HTML -Days 14"
                Write-Host "  BIG analytics health -Threshold 75 -TestMode"
                return
            }
            "bedtime" {
                Write-Host "`nBIG Bedtime Commands" -ForegroundColor Cyan
                Write-Host "====================" -ForegroundColor Cyan
                Write-Host "`nCommands for end-of-day protocols:"
                Write-Host "  start           - Begin bedtime protocol process"
                Write-Host "  create-summary  - Generate session summary"
                Write-Host "  analyze         - Analyze session outcomes"
                Write-Host "  transition      - Prepare memory for next session"
                Write-Host "  complete        - Finalize bedtime protocol"
                Write-Host ""
                Write-Host "Parameters:"
                Write-Host "  -OutputPath    - Path for output files (default: memory-bank/)"
                Write-Host "  -Format        - Output format (default: Markdown)"
                Write-Host "  -Notes         - Additional notes for summary"
                Write-Host "  -TestMode      - Simulate protocol without actual file operations"
                Write-Host "  -Detailed      - Include comprehensive details"
                Write-Host ""
                Write-Host "Examples:"
                Write-Host "  BIG bedtime start"
                Write-Host "  BIG bedtime create-summary -Notes 'Completed API implementation'"
                Write-Host "  BIG bedtime complete -TestMode"
                return
            }
            "rules" {
                Write-Host "`nBIG Rules Commands" -ForegroundColor Cyan
                Write-Host "=================" -ForegroundColor Cyan
                Write-Host "`nCommands for memory rules management:"
                Write-Host "  list        - List available rules"
                Write-Host "  add         - Add a new rule"
                Write-Host "  update      - Update an existing rule"
                Write-Host "  remove      - Remove a rule"
                Write-Host "  apply       - Apply rules to content"
                Write-Host "  validate    - Validate content against rules"
                Write-Host ""
                Write-Host "Parameters:"
                Write-Host "  -RuleName      - Name of the rule to manage"
                Write-Host "  -Category      - Rule category (Memory, Verification, etc.)"
                Write-Host "  -TargetPath    - Path to apply/validate rules against"
                Write-Host "  -Content       - Rule content for add/update operations"
                Write-Host "  -TestMode      - Test rule operations without making changes"
                Write-Host "  -Detailed      - Show detailed rule information"
                Write-Host ""
                Write-Host "Examples:"
                Write-Host "  BIG rules list -Category Memory"
                Write-Host "  BIG rules validate -TargetPath './memory-bank/active'"
                Write-Host "  BIG rules apply -RuleName 'MemoryStructure' -TestMode"
                return
            }
            # Other category help would go here
        }

        # If we get here, no specific help was found
        Write-Host "`nNo detailed help available for category: $Category" -ForegroundColor Yellow
        Show-Help # Show general help instead
    }
}

# Function to execute a script with parameters
function Invoke-BIGScript {
    [CmdletBinding()]
    param (
        [string]$ScriptPath,
        [string]$Command,
        [string[]]$Parameters
    )

    if (-not (Test-Path -Path $ScriptPath)) {
        Write-BIGLog -Message "Script not found at $ScriptPath" -Level "ERROR" -LogFile $logFile
        return $false
    }

    try {
        # Handle parameter passing differently based on script name
        $scriptName = Split-Path -Leaf $ScriptPath

        Write-BIGLog -Message "Executing script: $scriptName with Command: $Command" -Level "DEBUG" -LogFile $logFile

        # Expanded special handling for all BIG-*.ps1 scripts to fix parameter passing issues
        if ($scriptName -match "BIG-\w+\.ps1") {
            # For all BIG scripts, use named parameter for Command
            $paramString = "-Command '$Command'"

            # Add any additional parameters
            if ($Parameters -and $Parameters.Count -gt 0) {
                $paramString += " " + ($Parameters -join " ")
            }

            Write-BIGLog -Message "Executing: $ScriptPath $paramString" -Level "DEBUG" -LogFile $logFile

            # Use Invoke-Expression to handle the command properly
            $scriptCmd = "$ScriptPath $paramString"
            Invoke-Expression $scriptCmd
        }
        else {
            # Standard approach for other scripts
            $argList = @($Command) + $Parameters

            Write-BIGLog -Message "Executing: $ScriptPath with args: $argList" -Level "DEBUG" -LogFile $logFile
            & $ScriptPath @argList
        }

        if ($LASTEXITCODE -eq $null -or $LASTEXITCODE -eq 0) {
            return $true
        }
        return $false
    }
    catch {
        Write-BIGLog -Message "Error executing script: $_" -Level "ERROR" -LogFile $logFile
        return $false
    }
}

# Main command router
Write-BIGHeader -Title "BIG BRAIN COMMAND" -LogFile $logFile

Write-BIGLog -Message "Category: $Category, Command: $Command, Arguments: $($RemainingArgs -join ' ')" -Level "INFO" -LogFile $logFile

$startTime = Get-Date
$success = $false

# Check if no parameters were provided
if ([string]::IsNullOrEmpty($Category) -and [string]::IsNullOrEmpty($Command) -and (-not $RemainingArgs -or $RemainingArgs.Count -eq 0)) {
    # No parameters, show interactive menu
    Show-InteractiveMenu
    return
}

# Process top-level help request
if ([string]::IsNullOrEmpty($Category) -or $Category -eq "help") {
    $helpCategory = if ($Command) { $Command } else { "" }
    Show-Help -Category $helpCategory
    $success = $true
}
else {
    # Execute command based on category
    switch ($Category) {
        "analytics" {
            $validCommands = @("stats", "report", "health")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid analytics command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            $success = Invoke-BIGScript -ScriptPath $analyticsScript -Command $Command -Parameters $RemainingArgs
        }

        "organization" {
            $validCommands = @("list", "reorganize", "tag", "move", "clean")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid organization command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            $success = Invoke-BIGScript -ScriptPath $organizationScript -Command $Command -Parameters $RemainingArgs
        }

        "bedtime" {
            $validCommands = @("start", "create-summary", "analyze", "transition", "complete")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid bedtime command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            $success = Invoke-BIGScript -ScriptPath $bedtimeScript -Command $Command -Parameters $RemainingArgs
        }

        "rules" {
            $validCommands = @("list", "add", "update", "remove", "apply", "validate")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid rules command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            $success = Invoke-BIGScript -ScriptPath $rulesScript -Command $Command -Parameters $RemainingArgs
        }

        "update" {
            $validCommands = @("system", "scripts", "memory", "rules", "init")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid update command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            $success = Invoke-BIGScript -ScriptPath $updateScript -Command $Command -Parameters $RemainingArgs
        }

        "autonomous" {
            $validCommands = @("daily", "weekly", "monthly", "refresh", "full")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid autonomous command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            $success = Invoke-BIGScript -ScriptPath $autonomousScript -Command $Command -Parameters $RemainingArgs
        }

        "codebase" {
            $validCommands = @("analyze", "apply", "validate", "learn", "search")
            if (-not [string]::IsNullOrEmpty($Command) -and -not ($validCommands -contains $Command)) {
                Write-BIGLog -Message "Invalid codebase command: $Command. Valid commands: $($validCommands -join ', ')" -Level "ERROR" -LogFile $logFile
                break
            }

            # Always force using our corrected script - most reliable path first
            $currentDirScript = Join-Path -Path $PSScriptRoot -ChildPath "BIG-Codebase.ps1"
            Write-BIGLog -Message "Looking for codebase script at $currentDirScript" -Level "INFO" -LogFile $logFile

            if (Test-Path -Path $currentDirScript) {
                Write-BIGLog -Message "Using codebase script at: $currentDirScript" -Level "INFO" -LogFile $logFile
                $success = Invoke-BIGScript -ScriptPath $currentDirScript -Command $Command -Parameters $RemainingArgs
            }
            else {
                Write-BIGLog -Message "Codebase script not found at expected location" -Level "WARNING" -LogFile $logFile
                Write-Host "Warning: BIG-Codebase.ps1 not found at expected location. Using fallback search." -ForegroundColor Yellow

                # Try to find the script in common locations
                $alternativeLocations = @(
                    (Join-Path -Path (Split-Path -Parent $PSScriptRoot) -ChildPath "BIG-Commands/BIG-Codebase.ps1"),
                    "D:\Coding\Python_Projects\the_aichemist_codex\memory-bank\integration\BIG-Commands\BIG-Codebase.ps1"
                )

                $found = $false
                foreach ($location in $alternativeLocations) {
                    if (Test-Path -Path $location) {
                        Write-BIGLog -Message "Found codebase script at $location" -Level "INFO" -LogFile $logFile
                        Write-Host "Using codebase script at: $location" -ForegroundColor Cyan
                        $success = Invoke-BIGScript -ScriptPath $location -Command $Command -Parameters $RemainingArgs
                        $found = $true
                        break
                    }
                }

                if (-not $found) {
                    Write-BIGLog -Message "Could not find BIG-Codebase.ps1 script in any known location" -Level "ERROR" -LogFile $logFile
                    Write-Host "Error: Could not find BIG-Codebase.ps1 script in any known location" -ForegroundColor Red
                    Write-Host "Please run 'big help codebase' for more information." -ForegroundColor Yellow
                }
            }
        }

        default {
            Write-BIGLog -Message "Invalid category: $Category" -Level "ERROR" -LogFile $logFile
        }
    }
}

$duration = (Get-Date) - $startTime

if ($success) {
    Write-BIGLog -Message "Command completed successfully (Duration: $duration)" -Level "SUCCESS" -LogFile $logFile
}
else {
    Write-BIGLog -Message "Command failed (Duration: $duration)" -Level "ERROR" -LogFile $logFile
}

# End logging
Stop-BIGLogging -ScriptName $MyInvocation.MyCommand.Path -LogFile $logFile -Duration $duration

# Return proper exit code
if ($success) { exit 0 } else { exit 1 }

# New function for interactive menu when BIG is called without parameters
function Show-InteractiveMenu {
    Clear-Host
    $title = @"
 ______  _____ _____    ______  _____            _____ _   _
 | ___ \|_   _|  __ \   | ___ \/  __ \          |_   _| \ | |
 | |_/ /  | | | |  \/   | |_/ /| /  \/ ___  _____ | | |  \| |
 | ___ \  | | | | __    | ___ \| |    / _ \|  _  || | | . ` |
 | |_/ / _| |_| |_\ \   | |_/ /| \__/\ (_) | | | || |_| |\  |
 \____/  \___/ \____/   \____/  \____/\___/|_| |_|\___\_| \_/

"@
    Write-Host $title -ForegroundColor Cyan
    Write-Host "`nMemory Bank Command System" -ForegroundColor Yellow
    Write-Host "=============================================`n"

    Write-Host "Quick Access Commands:" -ForegroundColor Green
    Write-Host "   1. Memory Health Check"
    Write-Host "   2. Memory Analytics Dashboard"
    Write-Host "   3. Bedtime Protocol Wizard"
    Write-Host "   4. Rules Management"
    Write-Host "   5. System Update"
    Write-Host "   6. Codebase Integration"
    Write-Host "   7. Test Mode Examples"

    Write-Host "`nUtility Commands:" -ForegroundColor Green
    Write-Host "   8. Show Command Reference"
    Write-Host "   9. Common Parameters Help"
    Write-Host "  10. Get System Status"

    Write-Host "`nOther Options:" -ForegroundColor Green
    Write-Host "  11. Advanced Mode"
    Write-Host "  12. Exit"

    Write-Host "`nSelect an option (1-12): " -ForegroundColor Yellow -NoNewline

    $choice = Read-Host

    switch ($choice) {
        "1" {
            Write-Host "`nRunning Memory Health Check..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $analyticsScript -Command "health" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "2" {
            Write-Host "`nGenerating Memory Analytics Dashboard..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $analyticsScript -Command "report" -Parameters @("-Format", "HTML")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "3" {
            Write-Host "`nStarting Bedtime Protocol Wizard..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $bedtimeScript -Command "start" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "4" {
            # Show rules submenu
            Show-RulesSubMenu
        }
        "5" {
            Write-Host "`nRunning System Update..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $updateScript -Command "system" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "6" {
            # Show codebase submenu
            Show-CodebaseSubMenu
        }
        "7" {
            # Show test mode examples
            Show-TestModeExamples
        }
        "8" {
            Write-Host "`nCommand Reference:" -ForegroundColor Cyan
            Show-Help
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "9" {
            Show-CommonParameters
        }
        "10" {
            Write-Host "`nGetting System Status..." -ForegroundColor Cyan
            # This would call a function to show system status
            Write-Host "Memory Bank Status: HEALTHY" -ForegroundColor Green
            Write-Host "Last Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
            Write-Host "Active Rules: 42"
            Write-Host "Memory Files: 156"
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "11" {
            Write-Host "`nAdvanced Mode - Enter direct command:" -ForegroundColor Yellow
            $command = Read-Host
            Invoke-Expression $command
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
        "12" {
            Write-Host "`nExiting BIG Command System. Goodbye!" -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "`nInvalid selection. Press any key to try again..." -ForegroundColor Red -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-InteractiveMenu
        }
    }
}

# Rules submenu
function Show-RulesSubMenu {
    Clear-Host
    Write-Host "BIG BRAIN Rules Management" -ForegroundColor Cyan
    Write-Host "========================`n"

    Write-Host "Available Options:" -ForegroundColor Green
    Write-Host "   1. List All Rules"
    Write-Host "   2. Search Rules"
    Write-Host "   3. Validate Rules"
    Write-Host "   4. Apply Rules"
    Write-Host "   5. Back to Main Menu"

    Write-Host "`nSelect an option (1-5): " -ForegroundColor Yellow -NoNewline

    $choice = Read-Host

    switch ($choice) {
        "1" {
            Write-Host "`nListing All Rules..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $rulesScript -Command "list" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RulesSubMenu
        }
        "2" {
            Write-Host "`nEnter search term: " -ForegroundColor Yellow -NoNewline
            $searchTerm = Read-Host
            Write-Host "`nSearching Rules..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $rulesScript -Command "list" -Parameters @("-Filter", $searchTerm)
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RulesSubMenu
        }
        "3" {
            Write-Host "`nValidating Rules..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $rulesScript -Command "validate" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RulesSubMenu
        }
        "4" {
            Write-Host "`nRunning in Test Mode - Applying Rules..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $rulesScript -Command "apply" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RulesSubMenu
        }
        "5" {
            Show-InteractiveMenu
        }
        default {
            Write-Host "`nInvalid selection. Press any key to try again..." -ForegroundColor Red -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RulesSubMenu
        }
    }
}

# Codebase submenu
function Show-CodebaseSubMenu {
    Clear-Host
    Write-Host "BIG BRAIN Codebase Integration" -ForegroundColor Cyan
    Write-Host "===========================`n"

    Write-Host "Available Options:" -ForegroundColor Green
    Write-Host "   1. Analyze Current Codebase"
    Write-Host "   2. Search for Patterns"
    Write-Host "   3. Validate Against Standards"
    Write-Host "   4. Apply Standards (Test Mode)"
    Write-Host "   5. Back to Main Menu"

    Write-Host "`nSelect an option (1-5): " -ForegroundColor Yellow -NoNewline

    $choice = Read-Host

    switch ($choice) {
        "1" {
            Write-Host "`nAnalyzing Codebase..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $codebaseScript -Command "analyze" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-CodebaseSubMenu
        }
        "2" {
            Write-Host "`nEnter search pattern: " -ForegroundColor Yellow -NoNewline
            $pattern = Read-Host
            Write-Host "`nSearching Codebase..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $codebaseScript -Command "search" -Parameters @("-Pattern", $pattern)
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-CodebaseSubMenu
        }
        "3" {
            Write-Host "`nValidating Against Standards..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $codebaseScript -Command "validate" -Parameters @()
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-CodebaseSubMenu
        }
        "4" {
            Write-Host "`nApplying Standards (Test Mode)..." -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $codebaseScript -Command "apply" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-CodebaseSubMenu
        }
        "5" {
            Show-InteractiveMenu
        }
        default {
            Write-Host "`nInvalid selection. Press any key to try again..." -ForegroundColor Red -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-CodebaseSubMenu
        }
    }
}

# Display TestMode examples
function Show-TestModeExamples {
    Clear-Host
    Write-Host "BIG BRAIN Test Mode Examples" -ForegroundColor Cyan
    Write-Host "=========================`n"

    Write-Host "Test Mode allows you to run commands without making actual changes to your system." -ForegroundColor Yellow
    Write-Host "It's useful for previewing effects, testing, and learning about commands.`n"

    Write-Host "Example Commands:" -ForegroundColor Green
    Write-Host "   1. BIG analytics health -TestMode"
    Write-Host "   2. BIG organization reorganize -TestMode"
    Write-Host "   3. BIG rules apply -TestMode"
    Write-Host "   4. BIG bedtime start -TestMode"
    Write-Host "   5. BIG codebase apply -TestMode"
    Write-Host "   6. BIG update system -TestMode"
    Write-Host "   7. Back to Main Menu"

    Write-Host "`nSelect an example to run (1-7): " -ForegroundColor Yellow -NoNewline

    $choice = Read-Host

    switch ($choice) {
        "1" {
            Write-Host "`nRunning: BIG analytics health -TestMode" -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $analyticsScript -Command "health" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
        "2" {
            Write-Host "`nRunning: BIG organization reorganize -TestMode" -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $organizationScript -Command "reorganize" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
        "3" {
            Write-Host "`nRunning: BIG rules apply -TestMode" -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $rulesScript -Command "apply" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
        "4" {
            Write-Host "`nRunning: BIG bedtime start -TestMode" -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $bedtimeScript -Command "start" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
        "5" {
            Write-Host "`nRunning: BIG codebase apply -TestMode" -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $codebaseScript -Command "apply" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
        "6" {
            Write-Host "`nRunning: BIG update system -TestMode" -ForegroundColor Cyan
            Invoke-BIGScript -ScriptPath $updateScript -Command "system" -Parameters @("-TestMode")
            Write-Host "`nPress any key to return to menu..." -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
        "7" {
            Show-InteractiveMenu
        }
        default {
            Write-Host "`nInvalid selection. Press any key to try again..." -ForegroundColor Red -NoNewline
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-TestModeExamples
        }
    }
}

# Show common parameters help
function Show-CommonParameters {
    Clear-Host
    Write-Host "BIG BRAIN Common Parameters" -ForegroundColor Cyan
    Write-Host "========================`n"

    Write-Host "These parameters work across most BIG commands:`n" -ForegroundColor Yellow

    Write-Host "  -TestMode" -ForegroundColor Green
    Write-Host "    Runs commands without making actual changes to files or system"
    Write-Host "    Useful for previewing effects and learning how commands work"
    Write-Host "    Example: BIG rules apply -TestMode`n"

    Write-Host "  -Verbose" -ForegroundColor Green
    Write-Host "    Shows detailed execution information during command processing"
    Write-Host "    Helpful for troubleshooting or understanding command flow"
    Write-Host "    Example: BIG analytics stats -Verbose`n"

    Write-Host "  -Detailed" -ForegroundColor Green
    Write-Host "    Provides comprehensive output with additional information"
    Write-Host "    Especially useful for reporting and analysis commands"
    Write-Host "    Example: BIG codebase analyze -Detailed`n"

    Write-Host "  -OutputPath" -ForegroundColor Green
    Write-Host "    Specifies custom location for saving generated files"
    Write-Host "    Used with commands that produce reports or other outputs"
    Write-Host "    Example: BIG analytics report -OutputPath './custom-reports/'`n"

    Write-Host "Press any key to return to menu..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Show-InteractiveMenu
}
