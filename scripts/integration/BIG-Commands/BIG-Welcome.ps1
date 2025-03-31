# BIG-Welcome.ps1
# Display an eye-catching welcome banner for BIG BRAIN
# Version 1.1.0
# Created: 2025-04-01
# Updated: 2025-04-01 - Enhanced header and added TestMode info

function Show-BIGWelcomeBanner {
    try {
        # Define colors
        $foregroundColor = "Cyan"
        $accentColor = "Magenta"
        $headerColor = "Yellow"
        $exampleColor = "DarkCyan"

        # Fancy header with ASCII art
        Write-Host "`n"
        Write-Host "    ██████╗ ██╗ ██████╗     ██████╗ ██████╗  █████╗ ██╗███╗   ██╗" -ForegroundColor $accentColor
        Write-Host "    ██╔══██╗██║██╔════╝     ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║" -ForegroundColor $accentColor
        Write-Host "    ██████╔╝██║██║  ███╗    ██████╔╝██████╔╝███████║██║██╔██╗ ██║" -ForegroundColor $accentColor
        Write-Host "    ██╔══██╗██║██║   ██║    ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║" -ForegroundColor $accentColor
        Write-Host "    ██████╔╝██║╚██████╔╝    ██████╔╝██║  ██║██║  ██║██║██║ ╚████║" -ForegroundColor $accentColor
        Write-Host "    ╚═════╝ ╚═╝ ╚═════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝" -ForegroundColor $accentColor
        Write-Host "══════════════════════════════════════════════════════════════════" -ForegroundColor $foregroundColor
        Write-Host "                  MEMORY BANK COMMAND SYSTEM v2.0.1               " -ForegroundColor $headerColor -BackgroundColor Black
        Write-Host "══════════════════════════════════════════════════════════════════" -ForegroundColor $foregroundColor

        # Get project root
        $projectRoot = $null
        try {
            $projectRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
        }
        catch {
            $projectRoot = $PWD.Path
        }

        # Memory statistics section
        Write-Host "`n Memory Bank Status:" -ForegroundColor $foregroundColor

        # Get memory stats with error handling for each path
        $activePath = Join-Path -Path $projectRoot -ChildPath "memory-bank/active"
        $shortTermPath = Join-Path -Path $projectRoot -ChildPath "memory-bank/short-term"
        $longTermPath = Join-Path -Path $projectRoot -ChildPath "memory-bank/long-term"

        $activeCount = 0
        $shortTermCount = 0
        $longTermCount = 0

        if (Test-Path $activePath) {
            try { $activeCount = (Get-ChildItem -Path $activePath -Recurse -File -ErrorAction SilentlyContinue).Count } catch {}
        }

        if (Test-Path $shortTermPath) {
            try { $shortTermCount = (Get-ChildItem -Path $shortTermPath -Recurse -File -ErrorAction SilentlyContinue).Count } catch {}
        }

        if (Test-Path $longTermPath) {
            try { $longTermCount = (Get-ChildItem -Path $longTermPath -Recurse -File -ErrorAction SilentlyContinue).Count } catch {}
        }

        $totalCount = $activeCount + $shortTermCount + $longTermCount

        # System status
        Write-Host "  • System:             " -NoNewline -ForegroundColor $foregroundColor
        Write-Host "ONLINE" -ForegroundColor Green

        # Memory counts
        Write-Host "  • Active Memories:    $activeCount files" -ForegroundColor White
        Write-Host "  • Short-Term:         $shortTermCount files" -ForegroundColor White
        Write-Host "  • Long-Term Archive:  $longTermCount files" -ForegroundColor White
        Write-Host "  • Total Memory Bank:  $totalCount files" -ForegroundColor White

        # Last bedtime
        $lastBedtime = "Not recorded"
        try {
            $bedtimeDir = Join-Path -Path $projectRoot -ChildPath "memory-bank/Bedtime"
            if (Test-Path $bedtimeDir) {
                $lastBedtimeFile = Get-ChildItem -Path $bedtimeDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                if ($lastBedtimeFile) {
                    $lastBedtime = $lastBedtimeFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                }
            }
        }
        catch {}

        Write-Host "  • Last Bedtime:       $lastBedtime" -ForegroundColor White

        # Command categories section
        Write-Host "`n Available Categories:" -ForegroundColor $foregroundColor
        Write-Host "  • analytics    - Memory analytics and reporting" -ForegroundColor White
        Write-Host "  • organization - Memory organization and management" -ForegroundColor White
        Write-Host "  • bedtime      - Bedtime Protocol operations" -ForegroundColor White
        Write-Host "  • rules        - Rules management and application" -ForegroundColor White
        Write-Host "  • update       - System and memory bank updates" -ForegroundColor White
        Write-Host "  • autonomous   - Autonomous memory operations" -ForegroundColor White
        Write-Host "  • codebase     - Codebase integration with .cursor rules" -ForegroundColor White
        Write-Host "  • help         - Show help for a specific category" -ForegroundColor White

        # Common options section
        Write-Host "`n Common Options:" -ForegroundColor $foregroundColor
        Write-Host "  • -TestMode    - Run in test mode without making actual changes" -ForegroundColor White
        Write-Host "  • -Verbose     - Show detailed execution information" -ForegroundColor White
        Write-Host "  • -Detailed    - Provide comprehensive output with more information" -ForegroundColor White
        Write-Host "  • -OutputPath  - Specify custom location for saving generated files" -ForegroundColor White

        # Example commands
        Write-Host "`n Example Commands:" -ForegroundColor $foregroundColor
        Write-Host "  big analytics health" -ForegroundColor $exampleColor
        Write-Host "  big analytics report -Format HTML -Days 14" -ForegroundColor $exampleColor
        Write-Host "  big bedtime start" -ForegroundColor $exampleColor
        Write-Host "  big rules list -Category Memory" -ForegroundColor $exampleColor
        Write-Host "  big codebase analyze -Language PowerShell -TestMode" -ForegroundColor $exampleColor
        Write-Host "  big help analytics" -ForegroundColor $exampleColor

        Write-Host "`n══════════════════════════════════════════════════════════════════" -ForegroundColor $foregroundColor
        Write-Host "`n"
    }
    catch {
        # Fallback simple welcome message if anything goes wrong
        Write-Host "`nBIG BRAIN Memory Bank System loaded. Type 'big help' for available commands.`n" -ForegroundColor Cyan
    }
}

# Display the welcome banner
Show-BIGWelcomeBanner
