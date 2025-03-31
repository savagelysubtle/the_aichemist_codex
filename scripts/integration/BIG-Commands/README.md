# BIG Command System

The BIG Command System provides a standardized interface for interacting with the BIG BRAIN Memory Bank. These commands follow a consistent structure and provide a comprehensive set of operations for managing and analyzing the memory bank.

## Overview

The BIG Command System implements the following pattern:

```
BIG [category] [command] [parameters] [--options]
```

This structure provides a clear, consistent way to interact with all aspects of the memory bank system.

## BIG-Analytics Commands

The `BIG-Analytics.ps1` script provides commands for monitoring and analyzing memory bank health, generating statistics, and creating usage reports. All analytics data is stored in the `memory-bank/active/analytics/` directory for review and reference.

### Available Commands

| Command  | Description                                                                                    |
| -------- | ---------------------------------------------------------------------------------------------- |
| `stats`  | Gathers statistics about the memory bank, including file counts, sizes, and complexity metrics |
| `report` | Generates formatted reports of memory bank usage with visualizations and recommendations       |
| `health` | Performs a quick health check with targeted recommendations based on a threshold               |

### Common Parameters

| Parameter         | Description                                  | Default                                   |
| ----------------- | -------------------------------------------- | ----------------------------------------- |
| `-OutputPath`     | Custom path where output should be saved     | `memory-bank/active/analytics/` directory |
| `-IncludeDetails` | Include detailed file listings in statistics | `false`                                   |
| `-Format`         | Output format for reports (Text, HTML, JSON) | `HTML`                                    |
| `-Days`           | Number of days to analyze for reports        | `30`                                      |
| `-Threshold`      | Minimum acceptable health score percentage   | `60`                                      |

## Usage Examples

### Gathering Memory Statistics

```powershell
# Basic statistics gathering
BIG analytics stats

# Include detailed file listing
BIG analytics stats -IncludeDetails

# Save to custom location
BIG analytics stats -OutputPath "memory-bank/active/analytics/custom-stats.json"
```

### Generating Memory Reports

```powershell
# Generate HTML report (default)
BIG analytics report

# Generate text report
BIG analytics report -Format Text

# Generate report for past 7 days
BIG analytics report -Days 7

# Save to custom location
BIG analytics report -OutputPath "memory-bank/active/analytics/custom-report.html"
```

### Checking Memory Health

```powershell
# Check health with default threshold (60%)
BIG analytics health

# Check health with custom threshold
BIG analytics health -Threshold 75
```

## Output Files

By default, all analytics output is stored in the `memory-bank/active/analytics/` directory:

| File                       | Description                                    |
| -------------------------- | ---------------------------------------------- |
| `memory-statistics.json`   | Raw statistics data in JSON format             |
| `memory-usage-report.html` | HTML report with visualizations (default)      |
| `memory-usage-report.text` | Plain text report (when using `-Format Text`)  |
| `memory-usage-report.json` | JSON format report (when using `-Format JSON`) |

## Health Metrics

The BIG-Analytics system tracks five key metrics:

1. **Memory Diversity (0-1)**: Balance between active, short-term, and long-term memory types
2. **Long-Term Ratio (0-1)**: Proportion of content stored in long-term memory
3. **Category Balance (0-1)**: Distribution across long-term categories (episodic, semantic, procedural, creative)
4. **Activity Score (0-100%)**: Percentage of files modified in the last 7 days
5. **Overall Score (0-100%)**: Combined health rating with status categories:
   - 80-100%: Excellent
   - 60-79%: Good
   - 40-59%: Adequate
   - 20-39%: Needs Improvement
   - 0-19%: Critical

## Integration with Memory Bank

The analytics system is fully integrated with the memory bank structure:

1. **Data Storage**: All reports and statistics are stored in `memory-bank/active/analytics/`
2. **Memory Assessment**: Analytics directly assess the health of all memory bank components
3. **Structural Analysis**: The system evaluates memory bank organization against cognitive memory model standards
4. **Reorganization Guidance**: Health reports provide recommendations for memory bank optimization
5. **Bedtime Protocol Integration**: Analytics results inform the bedtime protocol for session transitions

## Integration with Bedtime Protocol

The analytics commands are designed to integrate with the Bedtime Protocol workflow:

1. Run `BIG analytics stats` to generate statistics before executing bedtime protocol
2. Run `BIG analytics report` to create a comprehensive report for session documentation
3. Run `BIG analytics health` to get a quick health status for verification
4. Include health metrics in your session summary
5. Address critical recommendations before completing the protocol

## Troubleshooting

### Common Issues

1. **Missing Statistics**: If you see "Statistics file not found", the system will automatically generate new statistics
2. **Report Generation Errors**: Ensure the Export-UsageReport.ps1 script exists in the scripts/Analytics directory
3. **HTML Reports Not Opening**: If automatic opening fails, manually navigate to the report in your browser
4. **Missing Output Directory**: The scripts will automatically create the required directories in memory-bank if they don't exist

### Potential Errors

```
Error: Statistics script not found
```
Solution: Verify that Get-MemoryBankStatistics.ps1 exists in the scripts/Analytics directory.

```
Error executing Export-UsageReport.ps1
```
Solution: Check that Export-UsageReport.ps1 exists and permissions are correct.

## Version History

- 1.0.0: Initial implementation of BIG Analytics commands (2025-03-25)
- 1.1.0: Improved error handling and compatibility with updated statistics script (2025-03-26)
- 1.2.0: Changed default output location to memory-bank/active/analytics directory (2025-03-27)
