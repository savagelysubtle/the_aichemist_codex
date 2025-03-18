"""
Models for the project reader module.

This module contains data models and helper classes used by the project reader system.
"""


class InvalidVersion(Exception):
    """Raised when an invalid version string is encountered."""

    pass


class Version:
    """Represents a version string for a project or file."""

    def __init__(self, version_str: str):
        """
        Initialize a Version object.

        Args:
            version_str: The version string to parse.

        Raises:
            InvalidVersion: If the version string is empty or invalid.
        """
        if not version_str:
            raise InvalidVersion("Version string cannot be empty.")
        self.version_str = version_str

    def __repr__(self) -> str:
        """
        Get the string representation of the Version.

        Returns:
            A string representation of the Version object.
        """
        return f"Version({self.version_str})"


class Tag:
    """Represents a tag associated with a file or project."""

    def __init__(self, name: str):
        """
        Initialize a Tag object.

        Args:
            name: The name of the tag.
        """
        self.name = name

    def __repr__(self) -> str:
        """
        Get the string representation of the Tag.

        Returns:
            A string representation of the Tag object.
        """
        return f"Tag({self.name})"


def parse_tag(tag_str: str) -> Tag:
    """
    Parse a tag string into a Tag object.

    Args:
        tag_str: The string to parse into a Tag.

    Returns:
        A Tag object.
    """
    return Tag(tag_str.strip())
