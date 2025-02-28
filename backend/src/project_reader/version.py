# src/project_reader/version.py

class InvalidVersion(Exception):
    """Raised when an invalid version string is encountered."""
    pass

class Version:
    def __init__(self, version_str: str):
        if not version_str:
            raise InvalidVersion("Version string cannot be empty.")
        self.version_str = version_str

    def __repr__(self):
        return f"Version({self.version_str})"
