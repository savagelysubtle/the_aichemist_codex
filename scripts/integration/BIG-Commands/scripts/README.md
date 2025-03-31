# BIG-Help.ps1

A PowerShell helper script for working with BIG Commands and Patterns in the AiChemist Codex project.

## Purpose

This script provides a safe way to:

1. Get help and information about available BIG Commands
2. Explore code Patterns in the codebase
3. Fix MDC file glob pattern formatting issues
4. Perform operations with dry-run safety

## Key Features

- **Dry Run Mode**: Default behavior is to show what would happen without making changes
- **MDC Glob Pattern Fixer**: Fixes the YAML front matter glob patterns in MDC files
- **Command Documentation**: Shows detailed help for BIG Commands
- **Pattern Documentation**: Shows information about available code patterns
- **Safe Workspace**: Uses a dedicated work folder for operations

## Usage Examples

### List All Commands

```powershell
.\BIG-Help.ps1 -ListCommands
```

### List All Patterns

```powershell
.\BIG-Help.ps1 -ListPatterns
```

### Get Help for a Specific Command

```powershell
.\BIG-Help.ps1 -Command BIG-Rules
```

### Get Help for a Specific Pattern

```powershell
.\BIG-Help.ps1 -Pattern ModularCode
```

### Fix MDC Glob Patterns

```powershell
.\BIG-Help.ps1 -FixMdcGlobs
```

### Run with Live Mode (Not Dry Run)

```powershell
.\BIG-Help.ps1 -DryRun:$false -FixMdcGlobs
```

### Set a Custom Work Folder

```powershell
.\BIG-Help.ps1 -WorkFolder "C:\Temp\SafeWorkspace"
```

## Safety Features

The script includes several safety features:

1. **Dry Run Mode**: By default, the script runs in dry run mode, showing what would happen without making changes
2. **Backups**: Creates backups of files before modifying them
3. **Error Handling**: Gracefully handles errors and provides clear status messages
4. **Work Folder**: Uses a dedicated workspace for operations

## MDC Glob Pattern Fix

The script can fix the YAML front matter glob patterns in MDC files. It changes:

```yaml
globs: ["**/*"]
```

To the correct format:

```yaml
globs: **/*
```

This fixes the issue where Cursor duplicates front matter when editing MDC files.
