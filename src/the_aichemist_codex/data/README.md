# AIChemist Codex Data Directory

This directory contains application data used by the AIChemist Codex system.
Each subdirectory serves a specific purpose:

## Directory Structure

- **backup/**: Stores automated backups of user data
- **cache/**: Contains temporary cached data for performance optimization
- **exports/**: Destination for exported data and reports
- **logs/**: Application logs and diagnostic information
- **trash/**: Temporarily stores deleted files before permanent deletion
- **versions/**: Stores version history of user files for rollback capabilities

## Notes

- In development mode, these directories are used directly
- In production/installed mode, these directories are replicated in the user's
  data directory
- Application data is segregated by user in multi-user environments

## Security

For security and privacy considerations:

- Sensitive data in these directories may be encrypted
- Password and authentication data is never stored in plaintext
- Local config can control data retention policies
