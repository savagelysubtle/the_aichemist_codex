# AIchemist MCP Servers Startup Guide

This guide explains how to use the automated startup script for MCP servers in the AIchemist Codex project.

## Quick Start

1. **Double-click** the `start-mcp-servers.bat` file in the project root
2. Wait for all servers to start in minimized windows
3. Cursor will automatically launch if servers start successfully

## Advanced Options

The startup script supports several options:

- **Hidden Mode**: Run with `start-mcp-servers.bat --hidden` to make server windows completely hidden
- **Custom Parameters**: For advanced usage, run the PowerShell script directly with parameters:
  ```powershell
  .\scripts\start-mcp-servers.ps1 -HiddenMode -Force -CursorPath "D:\path\to\cursor.exe"
  ```

### Available Parameters

| Parameter | Description |
|-----------|-------------|
| `-CursorPath` | Path to Cursor executable (default: D:\ProgramData\cursor\Cursor.exe) |
| `-HiddenMode` | Run servers with completely hidden windows |
| `-LaunchCursor` | Whether to launch Cursor automatically (default: true) |
| `-Force` | Skip all confirmation prompts |

## What This Does

The startup script:

1. Activates the Python virtual environment
2. Ensures all dependencies are installed
3. Launches all three MCP servers in separate windows (minimized or hidden):
   - AIchemist MCP Hub (Python)
   - Sequential Thinking Server (Node.js)
   - Sequential Thinking Tools (Node.js)
4. Sets all necessary environment variables
5. Automatically launches Cursor if all servers start successfully
6. Provides clear error messages if there are issues

## Troubleshooting

If you encounter issues:

1. **Error with virtual environment**: Make sure Python and UV are installed
2. **Node.js errors**: Ensure Node.js is installed and in your PATH
3. **"Client closed" errors in Cursor**: Try restarting Cursor after servers are running
4. **Server not found errors**: Check that the paths in `.cursor/mcp.json` match your project structure
5. **Log files**: Check the log files in the project root for each server:
   - `mcp_hub.log`
   - `sequential_thinking_server.log`
   - `sequential_thinking_tools.log`

## Requirements

- Python 3.8+
- UV package manager (`pip install uv`)
- Node.js (for NPX-based MCP servers)
- Cursor IDE with MCP support

## Using MCP in Cursor

To use MCP tools in Cursor:

1. Open Cursor Settings > Features > MCP
2. Ensure all MCP servers are enabled (green dot)
3. Open a Composer window in "Agent" mode
4. Ask the AI to use MCP tools or capabilities

## Manual Launch

You can also start the servers manually with:

```powershell
# From PowerShell in the project root
.\scripts\start-mcp-servers.ps1
```

## Important Notes

- When using Hidden Mode, the server windows will not be visible but are still running
- To terminate hidden servers, you'll need to use Task Manager to end the PowerShell processes
- The startup script addresses Windows-specific issues with MCP servers
- Cursor now uses `cmd /c` prefixes for better Windows compatibility
