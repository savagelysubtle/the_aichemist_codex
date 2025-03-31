"""
Windows API Wrapper - Provides access to Win32 API functions for file operations.
"""

import logging
import os
from enum import IntEnum
from pathlib import Path
from typing import Any

# Check if running on Windows
if os.name != "nt":
    raise ImportError("This module can only be used on Windows")

try:
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32security
    import winerror
except ImportError:
    raise ImportError(
        "pywin32 is required for Windows API integration. Install with: pip install pywin32"
    )


class FileAttribute(IntEnum):
    """Windows file attribute constants."""

    READONLY = win32con.FILE_ATTRIBUTE_READONLY
    HIDDEN = win32con.FILE_ATTRIBUTE_HIDDEN
    SYSTEM = win32con.FILE_ATTRIBUTE_SYSTEM
    DIRECTORY = win32con.FILE_ATTRIBUTE_DIRECTORY
    ARCHIVE = win32con.FILE_ATTRIBUTE_ARCHIVE
    NORMAL = win32con.FILE_ATTRIBUTE_NORMAL
    TEMPORARY = win32con.FILE_ATTRIBUTE_TEMPORARY
    COMPRESSED = win32con.FILE_ATTRIBUTE_COMPRESSED
    ENCRYPTED = win32con.FILE_ATTRIBUTE_ENCRYPTED


class SecurityInfo:
    """Contains security information for a file or directory."""

    def __init__(self, owner: str, group: str, dacl: list[dict[str, Any]]):
        """
        Initialize security info.

        Args:
            owner: Owner name
            group: Group name
            dacl: Discretionary access control list
        """
        self.owner = owner
        self.group = group
        self.dacl = dacl

    @classmethod
    def from_path(cls, path: str | Path) -> "SecurityInfo":
        """Create SecurityInfo from a file or directory path."""
        path_str = str(path)

        try:
            # Get security descriptor
            sd = win32security.GetFileSecurity(
                path_str,
                win32security.OWNER_SECURITY_INFORMATION
                | win32security.GROUP_SECURITY_INFORMATION
                | win32security.DACL_SECURITY_INFORMATION,
            )

            # Get owner and group SIDs
            owner_sid = sd.GetSecurityDescriptorOwner()
            group_sid = sd.GetSecurityDescriptorGroup()

            # Convert SIDs to account names
            owner_name, _, _ = win32security.LookupAccountSid(None, owner_sid)
            group_name, _, _ = win32security.LookupAccountSid(None, group_sid)

            # Get DACL
            dacl = sd.GetSecurityDescriptorDacl()
            dacl_entries = []

            if dacl:
                for i in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(i)
                    sid = ace[2]
                    try:
                        name, domain, _ = win32security.LookupAccountSid(None, sid)
                        account = f"{domain}\\{name}" if domain else name
                    except pywintypes.error:
                        account = str(sid)

                    dacl_entries.append(
                        {
                            "type": ace[0],
                            "flags": ace[1],
                            "account": account,
                            "access_mask": ace[3] if len(ace) > 3 else 0,
                        }
                    )

            return cls(owner_name, group_name, dacl_entries)

        except Exception as e:
            logging.error(f"Error getting security info for {path}: {e}")
            return cls("unknown", "unknown", [])


class WindowsFileUtils:
    """Utility class for Windows-specific file operations."""

    @staticmethod
    def get_file_attributes(path: str | Path) -> dict[FileAttribute, bool]:
        """
        Get file attributes.

        Args:
            path: Path to the file or directory

        Returns:
            Dictionary of attributes and their states
        """
        path_str = str(path)

        try:
            attrs = win32file.GetFileAttributes(path_str)

            return {
                FileAttribute.READONLY: bool(attrs & FileAttribute.READONLY),
                FileAttribute.HIDDEN: bool(attrs & FileAttribute.HIDDEN),
                FileAttribute.SYSTEM: bool(attrs & FileAttribute.SYSTEM),
                FileAttribute.DIRECTORY: bool(attrs & FileAttribute.DIRECTORY),
                FileAttribute.ARCHIVE: bool(attrs & FileAttribute.ARCHIVE),
                FileAttribute.NORMAL: bool(attrs & FileAttribute.NORMAL),
                FileAttribute.TEMPORARY: bool(attrs & FileAttribute.TEMPORARY),
                FileAttribute.COMPRESSED: bool(attrs & FileAttribute.COMPRESSED),
                FileAttribute.ENCRYPTED: bool(attrs & FileAttribute.ENCRYPTED),
            }
        except Exception as e:
            logging.error(f"Error getting attributes for {path}: {e}")
            return {}

    @staticmethod
    def set_file_attributes(
        path: str | Path, attributes: dict[FileAttribute, bool]
    ) -> bool:
        """
        Set file attributes.

        Args:
            path: Path to the file or directory
            attributes: Dictionary of attributes and their desired states

        Returns:
            True if successful
        """
        path_str = str(path)

        try:
            # Get current attributes
            current_attrs = win32file.GetFileAttributes(path_str)

            # Calculate new attributes
            new_attrs = current_attrs
            for attr, state in attributes.items():
                if state:
                    new_attrs |= attr  # Set the bit
                else:
                    new_attrs &= ~attr  # Clear the bit

            # Set the new attributes
            win32file.SetFileAttributes(path_str, new_attrs)
            return True
        except Exception as e:
            logging.error(f"Error setting attributes for {path}: {e}")
            return False
