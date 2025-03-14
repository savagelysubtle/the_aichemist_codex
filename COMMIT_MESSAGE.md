feat: Implement secure configuration manager and update documentation

This commit adds a secure configuration management system with the following features:

- Encrypted storage for sensitive configuration values using Fernet encryption
- Key rotation mechanism for enhanced security
- Environment variable support for encryption keys
- Cross-platform secure file permissions
- Comprehensive error handling and logging

Documentation updates:
- Updated architecture_docs/config.md with secure configuration details
- Created backend/config/README.md with usage examples and best practices
- Updated main README.md to reflect new security features
- Removed redundant requirements.txt in favor of pyproject.toml

Tests:
- Added comprehensive tests for secure configuration manager
- Fixed platform-specific issues in tests for Windows compatibility

This completes the security and compliance enhancements from Phase 1 of the project checklist.