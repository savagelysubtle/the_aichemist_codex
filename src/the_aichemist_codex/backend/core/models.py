"""
Core data models for the_aichemist_codex.

This module defines shared data structures used across the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


@dataclass
class FileMetadata:
    """Data model for file metadata."""

    path: str
    filename: str
    extension: str
    size: int
    created_time: datetime
    modified_time: datetime
    content_type: str
    keywords: list[str] = field(default_factory=list)
    description: str | None = None
    title: str | None = None
    author: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Data model for search results."""

    file_path: str
    score: float
    title: str | None = None
    snippet: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class EnvironmentInfo:
    """Data model for environment information."""

    is_development: bool
    is_production: bool
    is_test: bool
    python_version: str
    platform: str
    env_vars: dict[str, str] = field(default_factory=dict)


@dataclass
class DirectoryInfo:
    """Data model for directory information."""

    path: Path
    name: str
    is_hidden: bool = False
    children: list[Any] = field(
        default_factory=list
    )  # Can contain DirectoryInfo or FileInfo


@dataclass
class FileInfo:
    """Data model for file information."""

    path: Path
    name: str
    extension: str
    size: int
    modified_time: datetime
    is_hidden: bool = False


class RelationshipType(Enum):
    """Enumeration of possible relationship types between files."""

    # Reference relationships
    IMPORTS = auto()  # File imports or includes another file
    REFERENCES = auto()  # File references another file (e.g., in comments, docs)
    LINKS_TO = auto()  # File contains a link to another file

    # Content relationships
    SIMILAR_CONTENT = auto()  # Files have similar textual content
    SHARED_KEYWORDS = auto()  # Files share significant keywords

    # Structural relationships
    PARENT_CHILD = auto()  # Directory contains file relationship
    SIBLING = auto()  # Files in same directory

    # Temporal relationships
    MODIFIED_TOGETHER = auto()  # Files frequently modified in same commit/session
    CREATED_TOGETHER = auto()  # Files created at similar times

    # Derived relationships
    COMPILED_FROM = auto()  # File is compiled/generated from another file
    EXTRACTED_FROM = auto()  # File was extracted from another file

    # Custom relationship
    CUSTOM = auto()  # User-defined relationship


@dataclass
class Relationship:
    """Data model for file relationships."""

    id: str
    source_path: str
    target_path: str
    rel_type: RelationshipType
    strength: float
    created_time: datetime
    modified_time: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class UserRole(Enum):
    """Enumeration of user roles in the application."""

    ADMIN = "admin"  # Administrator with full access
    STAFF = "staff"  # Staff with elevated access
    USER = "user"  # Regular user
    GUEST = "guest"  # Guest with limited access


class PermissionType(Enum):
    """Enumeration of permission types available in the application."""

    # File permissions
    FILE_READ = "file:read"  # Read file content
    FILE_WRITE = "file:write"  # Write/modify file content
    FILE_DELETE = "file:delete"  # Delete files
    FILE_CREATE = "file:create"  # Create new files

    # User management permissions
    USER_READ = "user:read"  # View user information
    USER_WRITE = "user:write"  # Modify user information
    USER_CREATE = "user:create"  # Create new users
    USER_DELETE = "user:delete"  # Delete users

    # System permissions
    SYSTEM_CONFIG = "system:config"  # Configure system settings
    SYSTEM_MONITOR = "system:monitor"  # View system status and logs

    # Content permissions
    CONTENT_ANALYZE = "content:analyze"  # Analyze content
    CONTENT_GENERATE = "content:generate"  # Generate content

    # Custom permission
    CUSTOM = "custom"  # Custom user-defined permission


@dataclass
class User:
    """Data model for a user."""

    id: str
    username: str
    email: str
    full_name: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_time: datetime = field(default_factory=datetime.now)
    modified_time: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None
    preferences: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Permission:
    """Data model for a user permission."""

    id: str
    user_id: str
    permission_type: PermissionType
    resource_id: str | None = None  # Optional resource this permission applies to
    granted_time: datetime = field(default_factory=datetime.now)
    granted_by: str | None = None  # User ID of the grantor
    metadata: dict[str, Any] = field(default_factory=dict)
