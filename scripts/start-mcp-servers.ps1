# AIchemist MCP Servers Autostart Script
# This script automatically starts the MCP servers for Cursor

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false, HelpMessage = "Path to Cursor executable")]
    [ValidateNotNullOrEmpty()]
    [string]$CursorPath = "D:\ProgramData\cursor\Cursor.exe",

    [Parameter(Mandatory = $false, HelpMessage = "Launch Cursor after servers start")]
    [switch]$LaunchCursor = $true,

    [Parameter(Mandatory = $false, HelpMessage = "Run servers with completely hidden windows")]
    [switch]$HiddenMode = $false,

    [Parameter(Mandatory = $false, HelpMessage = "Skip any confirmation prompts")]
    [switch]$Force
)

# Initialize status tracking
$serversStarted = @{
    "AIchemistMcpHub"          = $false
    "SequentialThinkingServer" = $false
    "SequentialThinkingTools"  = $false
}

# Display startup banner
Write-Host "=================================="
Write-Host "  Starting AIchemist MCP Servers  "
Write-Host "=================================="

# Verify Cursor executable exists
if ($LaunchCursor -and -not (Test-Path $CursorPath)) {
    Write-Warning "Cursor executable not found at: $CursorPath"
    $confirmPrompt = Read-Host "Continue without launching Cursor? (Y/N)"
    if ($confirmPrompt -ne "Y" -and -not $Force) {
        Write-Host "Operation cancelled by user."
        exit 1
    }
    $LaunchCursor = $false
}

# Get the workspace root directory
$workspaceRoot = $PSScriptRoot | Split-Path -Parent
Write-Host "Workspace root: $workspaceRoot"

# Check and activate virtual environment if needed
if (-not (Test-Path "$workspaceRoot\.venv\Scripts\activate.ps1")) {
    Write-Host "Virtual environment not found. Creating one..."
    try {
        Set-Location $workspaceRoot
        uv venv
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }
    }
    catch {
        Write-Error "Failed to create virtual environment: $_"
        exit 1
    }
}

# Activate the virtual environment
Write-Host "Activating virtual environment..."
try {
    & "$workspaceRoot\.venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Failed to activate virtual environment. Continuing anyway..."
    }
}
catch {
    Write-Warning "Failed to activate virtual environment: $_. Continuing anyway..."
}

# Ensure dependencies are installed
Write-Host "Checking dependencies..."
if (Test-Path "$workspaceRoot\pyproject.toml" -and -not (Test-Path "$workspaceRoot\.venv\Lib\site-packages\mcp")) {
    Write-Host "Installing dependencies..."
    try {
        uv sync
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to sync dependencies"
        }

        uv pip install -e .
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install package in development mode"
        }
    }
    catch {
        Write-Error "Failed to install dependencies: $_"
        exit 1
    }
}

# Set environment variables for MCP servers
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:LOG_LEVEL = "DEBUG"
$env:PYTHONPATH = $workspaceRoot
$env:AICHEMIST_ROOT = $workspaceRoot
$env:NODE_ENV = "development"
$env:MCP_DEBUG = "true"
$env:MCP_VERBOSE = "true"

# Check if Node.js is installed
$nodeInstalled = $false
try {
    $nodeVersion = cmd /c "node --version 2>&1"
    if ($nodeVersion -match "v\d+") {
        $nodeInstalled = $true
        Write-Host "Node.js is installed: $nodeVersion"
    }
}
catch {
    Write-Host "Node.js is not installed or not in PATH"
}

# Determine window style based on user preference
$windowStyle = if ($HiddenMode) { "Hidden" } else { "Minimized" }

# Function to start the Python MCP hub
function Start-AichemistMcpHub {
    Write-Host "Starting AIchemist MCP Hub..."
    $mcpScript = Join-Path $workspaceRoot "mcp\aichemist_mcp_hub_new.py"

    if (Test-Path $mcpScript) {
        try {
            # Create a log file for this server
            $logPath = Join-Path $workspaceRoot "mcp_hub.log"

            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$workspaceRoot'; python '$mcpScript' | Tee-Object -FilePath '$logPath'" -WindowStyle $windowStyle

            # Wait briefly to check if process is still running (basic verification)
            Start-Sleep -Seconds 1

            # Check log file for basic startup confirmation
            if (Test-Path $logPath) {
                $logContent = Get-Content $logPath -ErrorAction SilentlyContinue
                if ($logContent -match "Starting AIchemist MCP Hub") {
                    Write-Host "AIchemist MCP Hub started successfully" -ForegroundColor Green
                    $script:serversStarted["AIchemistMcpHub"] = $true
                    return $true
                }
            }

            Write-Host "AIchemist MCP Hub started, but verification pending" -ForegroundColor Yellow
            $script:serversStarted["AIchemistMcpHub"] = $true
            return $true
        }
        catch {
            Write-Error "Failed to start AIchemist MCP Hub: $_"
            return $false
        }
    }
    else {
        Write-Error "ERROR: MCP Hub script not found at $mcpScript"
        return $false
    }
}

# Function to start the Sequential Thinking Server
function Start-SequentialThinkingServer {
    if (-not $nodeInstalled) {
        Write-Error "ERROR: Node.js not found. Cannot start Sequential Thinking Server"
        return $false
    }

    Write-Host "Starting Sequential Thinking Server..."
    try {
        # Create a log file for this server
        $logPath = Join-Path $workspaceRoot "sequential_thinking_server.log"

        # Use cmd /c to avoid issues with NPX on Windows
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$workspaceRoot'; cmd /c 'npx -y @modelcontextprotocol/server-sequential-thinking --config {\"port\": 8778, \"logLevel\": \"info\", \"allowOrigin\": \"*\"}' | Tee-Object -FilePath '$logPath'" -WindowStyle $windowStyle

        # Wait briefly to check if process is still running
        Start-Sleep -Seconds 2

        Write-Host "Sequential Thinking Server started" -ForegroundColor Green
        $script:serversStarted["SequentialThinkingServer"] = $true
        return $true
    }
    catch {
        Write-Error "Failed to start Sequential Thinking Server: $_"
        return $false
    }
}

# Function to start the Sequential Thinking Tools
function Start-SequentialThinkingTools {
    if (-not $nodeInstalled) {
        Write-Error "ERROR: Node.js not found. Cannot start Sequential Thinking Tools"
        return $false
    }

    Write-Host "Starting Sequential Thinking Tools..."
    try {
        # Create a log file for this server
        $logPath = Join-Path $workspaceRoot "sequential_thinking_tools.log"

        # Use cmd /c to avoid issues with NPX on Windows
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$workspaceRoot'; cmd /c 'npx -y mcp-sequentialthinking-tools' | Tee-Object -FilePath '$logPath'" -WindowStyle $windowStyle

        # Wait briefly to check if process is still running
        Start-Sleep -Seconds 2

        Write-Host "Sequential Thinking Tools started" -ForegroundColor Green
        $script:serversStarted["SequentialThinkingTools"] = $true
        return $true
    }
    catch {
        Write-Error "Failed to start Sequential Thinking Tools: $_"
        return $false
    }
}

# Function to launch Cursor
function Start-Cursor {
    if (-not $LaunchCursor) {
        return
    }

    Write-Host "Launching Cursor..." -ForegroundColor Cyan
    try {
        Start-Process -FilePath $CursorPath -WindowStyle Normal
        Write-Host "Cursor launched successfully!" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to launch Cursor: $_"
    }
}

# Start all MCP servers and track success
$success = $true

# Start AIchemist MCP Hub
$hubSuccess = Start-AichemistMcpHub
$success = $success -and $hubSuccess
Start-Sleep -Seconds 2  # Small delay to prevent resource contention

# Start Sequential Thinking Server
$stsSuccess = Start-SequentialThinkingServer
$success = $success -and $stsSuccess
Start-Sleep -Seconds 2  # Small delay to prevent resource contention

# Start Sequential Thinking Tools
$sttSuccess = Start-SequentialThinkingTools
$success = $success -and $sttSuccess

# Summary
Write-Host ""
Write-Host "MCP Server Startup Summary:" -ForegroundColor Cyan
Write-Host "- AIchemist MCP Hub: $(if ($serversStarted['AIchemistMcpHub']) { 'Started ✓' } else { 'Failed ✗' })"
Write-Host "- Sequential Thinking Server: $(if ($serversStarted['SequentialThinkingServer']) { 'Started ✓' } else { 'Failed ✗' })"
Write-Host "- Sequential Thinking Tools: $(if ($serversStarted['SequentialThinkingTools']) { 'Started ✓' } else { 'Failed ✗' })"
Write-Host ""

# Launch Cursor if all servers started successfully
if ($success) {
    Write-Host "All MCP servers have been started successfully!" -ForegroundColor Green
    Write-Host "These terminal windows will remain running in the background for the MCP servers to function."
    Write-Host ""
    Write-Host "To use MCP servers in Cursor, make sure to: "
    Write-Host "1. Enable MCP servers in Cursor settings"
    Write-Host "2. Use Cursor in Agent mode to access MCP tools"

    # Launch Cursor
    Start-Cursor
}
else {
    Write-Host "WARNING: Some MCP servers failed to start." -ForegroundColor Red
    Write-Host "Please check the logs for more information."

    if ($LaunchCursor) {
        $confirmPrompt = "N"
        if (-not $Force) {
            $confirmPrompt = Read-Host "Do you still want to launch Cursor? (Y/N)"
        }

        if ($confirmPrompt -eq "Y" -or $Force) {
            Start-Cursor
        }
        else {
            Write-Host "Cursor will not be launched due to server startup failures."
        }
    }

    # Return non-zero exit code
    exit 1
}

# Exit with success code
exit 0
