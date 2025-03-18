"""
User Manager implementation for AIChemist Codex.

This module provides the implementation of the UserManager interface
for managing users, including authentication, authorization, profile
management, and user preferences.
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import bcrypt

from the_aichemist_codex.backend.core.exceptions import UserError, ValidationError
from the_aichemist_codex.backend.core.interfaces import (
    FileValidator,
    ProjectPaths,
)
from the_aichemist_codex.backend.core.interfaces import (
    UserManager as UserManagerInterface,
)
from the_aichemist_codex.backend.core.models import (
    PermissionType,
    UserRole,
)

from .schema import SCHEMA_SQL

logger = logging.getLogger(__name__)


class UserManagerImpl(UserManagerInterface):
    """Implementation of the UserManager interface."""

    def __init__(self, project_paths: ProjectPaths, file_validator: FileValidator):
        """
        Initialize the UserManagerImpl.

        Args:
            project_paths: Service for accessing application paths
            file_validator: Service for validating file paths
        """
        self._project_paths = project_paths
        self._file_validator = file_validator
        self._conn: sqlite3.Connection | None = None
        self._initialized = False
        self._db_path: Path | None = None

    async def initialize(self) -> None:
        """
        Initialize the user manager.

        This method sets up the database connection and creates tables if needed.

        Raises:
            UserError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Create data directory if it doesn't exist
            data_dir = self._project_paths.get_data_dir() / "user_management"
            os.makedirs(data_dir, exist_ok=True)

            # Initialize database connection
            self._db_path = data_dir / "users.db"
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row

            # Create tables if they don't exist
            cursor = self._conn.cursor()
            cursor.executescript(SCHEMA_SQL)
            self._conn.commit()

            # Create default admin user if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            if user_count == 0:
                await self._create_default_admin()

            self._initialized = True
            logger.info("UserManager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize UserManager: {e}")
            if self._conn:
                self._conn.close()
                self._conn = None
            raise UserError(f"Failed to initialize UserManager: {e}") from e

    async def close(self) -> None:
        """
        Close the user manager and free resources.

        Raises:
            UserError: If closing fails
        """
        if not self._initialized:
            return

        try:
            if self._conn:
                self._conn.close()
                self._conn = None
            self._initialized = False
            logger.info("UserManager closed successfully")
        except Exception as e:
            logger.error(f"Error closing UserManager: {e}")
            raise UserError(f"Failed to close UserManager: {e}") from e

    async def _create_default_admin(self) -> None:
        """
        Create the default admin user.

        This is called during initialization if no users exist in the database.
        """
        # Generate a random password for the admin user
        default_password = uuid.uuid4().hex[:12]

        # Create the admin user
        admin_user = await self.create_user(
            username="admin",
            email="admin@local.aichemist",
            password=default_password,
            full_name="AIChemist Admin",
            role="admin",
        )

        # Grant all permissions to the admin user
        for permission in PermissionType:
            await self.grant_permission(admin_user["id"], permission.value)

        logger.info(
            f"Created default admin user with username 'admin' and password '{default_password}'"
        )
        logger.info("Please change this password immediately after first login")

    def _ensure_initialized(self) -> None:
        """
        Ensure the manager is initialized.

        Raises:
            UserError: If the manager is not initialized
        """
        if not self._initialized or not self._conn:
            raise UserError("UserManager is not initialized")

    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValidationError(
                "Password must be at least 8 characters long", "password"
            )

        # Add more validation rules as needed

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Password hash
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Plain text password
            password_hash: Hashed password

        Returns:
            True if the password matches the hash, False otherwise
        """
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def _row_to_user(self, row: sqlite3.Row) -> dict[str, Any]:
        """
        Convert a database row to a user dictionary.

        Args:
            row: Database row

        Returns:
            User dictionary
        """
        user_dict = dict(row)

        # Convert JSON strings to dictionaries
        if "metadata" in user_dict and user_dict["metadata"]:
            try:
                user_dict["metadata"] = json.loads(user_dict["metadata"])
            except json.JSONDecodeError:
                user_dict["metadata"] = {}

        # Remove password hash from result
        if "password_hash" in user_dict:
            del user_dict["password_hash"]

        return user_dict

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
        role: str = "user",
    ) -> dict[str, Any]:
        """
        Create a new user.

        Args:
            username: Unique username for the user
            email: Email address for the user
            password: Password for the user (will be securely hashed)
            full_name: Full name of the user (optional)
            role: Role for the user (default: "user")

        Returns:
            Dictionary containing user information

        Raises:
            UserError: If user creation fails
            ValidationError: If input validation fails
        """
        self._ensure_initialized()

        # Validate input
        if not username or len(username) < 3:
            raise ValidationError(
                "Username must be at least 3 characters long", "username"
            )

        if not email or "@" not in email:
            raise ValidationError("Valid email address is required", "email")

        self._validate_password(password)

        # Check valid role
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise ValidationError(
                f"Invalid role: {role}. Must be one of: {', '.join(valid_roles)}",
                "role",
            )

        try:
            cursor = self._conn.cursor()

            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                raise ValidationError(
                    f"Username '{username}' is already taken", "username"
                )

            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                raise ValidationError(f"Email '{email}' is already registered", "email")

            # Generate user ID
            user_id = str(uuid.uuid4())

            # Hash password
            password_hash = self._hash_password(password)

            # Get current time
            now = datetime.utcnow().isoformat()

            # Insert user
            cursor.execute(
                """
                INSERT INTO users (
                    id, username, email, password_hash, full_name, role,
                    is_active, created_time, modified_time, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, '{}')
                """,
                (user_id, username, email, password_hash, full_name, role, now, now),
            )

            self._conn.commit()

            # Return created user
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                raise UserError("Failed to retrieve created user")

            return self._row_to_user(row)

        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            self._conn.rollback()
            raise UserError(f"Failed to create user: {e}", operation="create") from e

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """
        Get user information by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            Dictionary containing user information, or None if not found

        Raises:
            UserError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # Get user preferences
            user_dict = self._row_to_user(row)
            user_dict["preferences"] = await self.get_user_preferences(user_id)

            return user_dict

        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise UserError(f"Failed to get user: {e}", user_id=user_id) from e

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """
        Get user information by username.

        Args:
            username: Username to retrieve

        Returns:
            Dictionary containing user information, or None if not found

        Raises:
            UserError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if not row:
                return None

            # Get user preferences
            user_dict = self._row_to_user(row)
            user_dict["preferences"] = await self.get_user_preferences(user_dict["id"])

            return user_dict

        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            raise UserError(f"Failed to get user: {e}", username=username) from e

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Get user information by email.

        Args:
            email: Email address to retrieve

        Returns:
            Dictionary containing user information, or None if not found

        Raises:
            UserError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

            if not row:
                return None

            # Get user preferences
            user_dict = self._row_to_user(row)
            user_dict["preferences"] = await self.get_user_preferences(user_dict["id"])

            return user_dict

        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise UserError(f"Failed to get user: {e}", username=email) from e

    async def update_user(
        self, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update user information.

        Args:
            user_id: User ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated user information

        Raises:
            UserError: If update fails
            ValidationError: If input validation fails
        """
        self._ensure_initialized()

        # Check if user exists
        existing_user = await self.get_user(user_id)
        if not existing_user:
            raise UserError(f"User not found: {user_id}", user_id=user_id)

        # Fields that can be updated
        allowed_fields = {
            "username",
            "email",
            "full_name",
            "role",
            "is_active",
            "metadata",
        }
        update_fields = set(updates.keys()) & allowed_fields

        if not update_fields:
            return existing_user  # Nothing to update

        try:
            cursor = self._conn.cursor()

            # Validate username if it's being updated
            if "username" in update_fields:
                username = updates["username"]
                if not username or len(username) < 3:
                    raise ValidationError(
                        "Username must be at least 3 characters long", "username"
                    )

                # Check if the new username is already taken by another user
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? AND id != ?",
                    (username, user_id),
                )
                if cursor.fetchone():
                    raise ValidationError(
                        f"Username '{username}' is already taken", "username"
                    )

            # Validate email if it's being updated
            if "email" in update_fields:
                email = updates["email"]
                if not email or "@" not in email:
                    raise ValidationError("Valid email address is required", "email")

                # Check if the new email is already registered by another user
                cursor.execute(
                    "SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)
                )
                if cursor.fetchone():
                    raise ValidationError(
                        f"Email '{email}' is already registered", "email"
                    )

            # Validate role if it's being updated
            if "role" in update_fields:
                role = updates["role"]
                valid_roles = [r.value for r in UserRole]
                if role not in valid_roles:
                    raise ValidationError(
                        f"Invalid role: {role}. Must be one of: {', '.join(valid_roles)}",
                        "role",
                    )

            # Process metadata if it's being updated
            if "metadata" in update_fields and isinstance(updates["metadata"], dict):
                updates["metadata"] = json.dumps(updates["metadata"])

            # Build SQL update statement
            fields = []
            values = []
            for field in update_fields:
                fields.append(f"{field} = ?")
                values.append(updates[field])

            # Add modified time
            fields.append("modified_time = ?")
            values.append(datetime.utcnow().isoformat())

            # Add user_id to values
            values.append(user_id)

            # Execute update
            cursor.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id = ?", tuple(values)
            )

            self._conn.commit()

            # Return updated user
            return await self.get_user(user_id)

        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            self._conn.rollback()
            raise UserError(
                f"Failed to update user: {e}", user_id=user_id, operation="update"
            ) from e

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: User ID to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            UserError: If deletion fails
        """
        self._ensure_initialized()

        # Check if user exists
        existing_user = await self.get_user(user_id)
        if not existing_user:
            return False  # User not found

        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self._conn.commit()

            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            self._conn.rollback()
            raise UserError(
                f"Failed to delete user: {e}", user_id=user_id, operation="delete"
            ) from e

    async def authenticate(
        self, username_or_email: str, password: str
    ) -> dict[str, Any] | None:
        """
        Authenticate a user with username/email and password.

        Args:
            username_or_email: Username or email address
            password: Password to verify

        Returns:
            Dictionary containing user information if authentication succeeds,
            None otherwise

        Raises:
            UserError: If authentication fails for a reason other than
                       invalid credentials
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Check if input is email or username
            is_email = "@" in username_or_email

            # Get user by email or username
            if is_email:
                cursor.execute(
                    "SELECT * FROM users WHERE email = ?", (username_or_email,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM users WHERE username = ?", (username_or_email,)
                )

            row = cursor.fetchone()

            # User not found
            if not row:
                return None

            # Check if user is active
            user_dict = dict(row)
            if not user_dict.get("is_active"):
                logger.warning(
                    f"Authentication attempt for inactive user: {username_or_email}"
                )
                return None

            # Verify password
            password_hash = user_dict.get("password_hash", "")
            if not self._verify_password(password, password_hash):
                logger.warning(
                    f"Failed authentication attempt for user: {username_or_email}"
                )
                return None

            # Update last login time
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?", (now, user_dict["id"])
            )
            self._conn.commit()

            # Get full user info
            return await self.get_user(user_dict["id"])

        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            raise UserError(
                f"Authentication failed: {e}", operation="authenticate"
            ) from e

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password change was successful, False otherwise

        Raises:
            UserError: If password change fails
            ValidationError: If password validation fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Get current password hash
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                return False  # User not found

            # Verify current password
            current_hash = row["password_hash"]
            if not self._verify_password(current_password, current_hash):
                return False  # Current password incorrect

            # Validate new password
            self._validate_password(new_password)

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "UPDATE users SET password_hash = ?, modified_time = ? WHERE id = ?",
                (new_hash, now, user_id),
            )
            self._conn.commit()

            return True

        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            self._conn.rollback()
            raise UserError(
                f"Failed to change password: {e}",
                user_id=user_id,
                operation="change_password",
            ) from e

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """
        Reset a user's password (admin function).

        Args:
            user_id: User ID
            new_password: New password to set

        Returns:
            True if password reset was successful, False otherwise

        Raises:
            UserError: If password reset fails
            ValidationError: If password validation fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False  # User not found

            # Validate new password
            self._validate_password(new_password)

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            now = datetime.utcnow().isoformat()
            cursor.execute(
                "UPDATE users SET password_hash = ?, modified_time = ? WHERE id = ?",
                (new_hash, now, user_id),
            )
            self._conn.commit()

            return True

        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            self._conn.rollback()
            raise UserError(
                f"Failed to reset password: {e}",
                user_id=user_id,
                operation="reset_password",
            ) from e

    async def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """
        Get user preferences.

        Args:
            user_id: User ID

        Returns:
            Dictionary containing user preferences

        Raises:
            UserError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                raise UserError(f"User not found: {user_id}", user_id=user_id)

            # Get preferences
            cursor.execute(
                "SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?",
                (user_id,),
            )
            rows = cursor.fetchall()

            # Build preferences dictionary
            preferences = {}
            for row in rows:
                key = row["preference_key"]
                value = row["preference_value"]

                # Try to convert to appropriate type
                try:
                    # Try to parse as JSON
                    preferences[key] = json.loads(value)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    preferences[key] = value

            return preferences

        except UserError:
            # Re-raise user errors
            raise
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            raise UserError(
                f"Failed to get user preferences: {e}", user_id=user_id
            ) from e

    async def update_preferences(
        self, user_id: str, preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: Dictionary of preference updates

        Returns:
            Updated preferences dictionary

        Raises:
            UserError: If update fails
        """
        self._ensure_initialized()

        if not preferences:
            return await self.get_user_preferences(user_id)

        try:
            cursor = self._conn.cursor()

            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                raise UserError(f"User not found: {user_id}", user_id=user_id)

            # Get current time
            now = datetime.utcnow().isoformat()

            # Update or insert each preference
            for key, value in preferences.items():
                # Skip if key is empty
                if not key:
                    continue

                # Convert value to string if it's not
                if not isinstance(value, str):
                    value = json.dumps(value)

                # Insert or update the preference
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, preference_key, preference_value, modified_time)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, preference_key) DO UPDATE SET
                    preference_value = excluded.preference_value,
                    modified_time = excluded.modified_time
                    """,
                    (user_id, key, value, now),
                )

            self._conn.commit()

            # Return updated preferences
            return await self.get_user_preferences(user_id)

        except UserError:
            # Re-raise user errors
            raise
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            self._conn.rollback()
            raise UserError(
                f"Failed to update user preferences: {e}", user_id=user_id
            ) from e

    async def check_permission(
        self, user_id: str, permission: str, resource_id: str | None = None
    ) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: User ID to check
            permission: Permission to check for
            resource_id: Optional resource ID to check permission against

        Returns:
            True if the user has the permission, False otherwise

        Raises:
            UserError: If permission check fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # First, check if user exists and get role
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                return False  # User not found

            # Admin users have all permissions
            if row["role"] == UserRole.ADMIN.value:
                return True

            # Check for resource-specific permissions first
            if resource_id:
                cursor.execute(
                    "SELECT id FROM permissions WHERE user_id = ? AND permission_type = ? AND resource_id = ?",
                    (user_id, permission, resource_id),
                )
                if cursor.fetchone():
                    return True

            # Check for global permissions (null resource_id)
            cursor.execute(
                "SELECT id FROM permissions WHERE user_id = ? AND permission_type = ? AND resource_id IS NULL",
                (user_id, permission),
            )
            return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            raise UserError(f"Failed to check permission: {e}", user_id=user_id) from e

    async def grant_permission(
        self, user_id: str, permission: str, resource_id: str | None = None
    ) -> bool:
        """
        Grant a permission to a user.

        Args:
            user_id: User ID to grant permission to
            permission: Permission to grant
            resource_id: Optional resource ID to grant permission on

        Returns:
            True if permission was granted, False otherwise

        Raises:
            UserError: If granting permission fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False  # User not found

            # Check if permission already exists
            params = [user_id, permission]
            resource_clause = "IS NULL" if resource_id is None else "= ?"
            if resource_id is not None:
                params.append(resource_id)

            cursor.execute(
                f"SELECT id FROM permissions WHERE user_id = ? AND permission_type = ? AND resource_id {resource_clause}",
                tuple(params),
            )

            if cursor.fetchone():
                return True  # Permission already exists

            # Generate permission ID and timestamp
            permission_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            # Insert the permission
            cursor.execute(
                """
                INSERT INTO permissions
                (id, user_id, permission_type, resource_id, granted_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (permission_id, user_id, permission, resource_id, now),
            )

            self._conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            self._conn.rollback()
            raise UserError(f"Failed to grant permission: {e}", user_id=user_id) from e

    async def revoke_permission(
        self, user_id: str, permission: str, resource_id: str | None = None
    ) -> bool:
        """
        Revoke a permission from a user.

        Args:
            user_id: User ID to revoke permission from
            permission: Permission to revoke
            resource_id: Optional resource ID to revoke permission from

        Returns:
            True if permission was revoked, False otherwise

        Raises:
            UserError: If revoking permission fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False  # User not found

            # Delete the permission
            params = [user_id, permission]
            resource_clause = "IS NULL" if resource_id is None else "= ?"
            if resource_id is not None:
                params.append(resource_id)

            cursor.execute(
                f"DELETE FROM permissions WHERE user_id = ? AND permission_type = ? AND resource_id {resource_clause}",
                tuple(params),
            )

            self._conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            self._conn.rollback()
            raise UserError(f"Failed to revoke permission: {e}", user_id=user_id) from e

    async def get_user_permissions(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all permissions for a user.

        Args:
            user_id: User ID to get permissions for

        Returns:
            List of permission dictionaries

        Raises:
            UserError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Check if user exists
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                raise UserError(f"User not found: {user_id}", user_id=user_id)

            # If user is admin, return all permissions
            role = row["role"]

            # Get user permissions
            cursor.execute(
                """
                SELECT id, permission_type, resource_id, granted_time, granted_by, metadata
                FROM permissions
                WHERE user_id = ?
                """,
                (user_id,),
            )

            permissions = []
            for row in cursor.fetchall():
                perm = dict(row)

                # Convert metadata json to dict
                if "metadata" in perm and perm["metadata"]:
                    try:
                        perm["metadata"] = json.loads(perm["metadata"])
                    except json.JSONDecodeError:
                        perm["metadata"] = {}

                permissions.append(perm)

            # If user is admin, add a note about implicit permissions
            if role == UserRole.ADMIN.value:
                permissions.append(
                    {
                        "id": "admin-all-permissions",
                        "permission_type": "all",
                        "resource_id": None,
                        "granted_time": None,
                        "granted_by": None,
                        "metadata": {
                            "note": "Admin users implicitly have all permissions"
                        },
                        "is_implicit": True,
                    }
                )

            return permissions

        except UserError:
            # Re-raise user errors
            raise
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            raise UserError(
                f"Failed to get user permissions: {e}", user_id=user_id
            ) from e

    async def list_users(
        self,
        query: str | None = None,
        role: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List users, optionally filtered.

        Args:
            query: Optional search query to filter results
            role: Optional role to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of user dictionaries

        Raises:
            UserError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Build query
            sql = "SELECT * FROM users"
            params = []
            where_clauses = []

            # Add search query if provided
            if query:
                search_term = f"%{query}%"
                where_clauses.append(
                    "(username LIKE ? OR email LIKE ? OR full_name LIKE ?)"
                )
                params.extend([search_term, search_term, search_term])

            # Add role filter if provided
            if role:
                where_clauses.append("role = ?")
                params.append(role)

            # Add WHERE clause if needed
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

            # Add ORDER BY, LIMIT and OFFSET
            sql += " ORDER BY username LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            # Execute query
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

            # Convert rows to user dictionaries
            users = []
            for row in rows:
                users.append(self._row_to_user(row))

            return users

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            raise UserError(f"Failed to list users: {e}") from e

    async def count_users(
        self, query: str | None = None, role: str | None = None
    ) -> int:
        """
        Count users, optionally filtered.

        Args:
            query: Optional search query to filter results
            role: Optional role to filter by

        Returns:
            Number of matching users

        Raises:
            UserError: If counting fails
        """
        self._ensure_initialized()

        try:
            cursor = self._conn.cursor()

            # Build query
            sql = "SELECT COUNT(*) FROM users"
            params = []
            where_clauses = []

            # Add search query if provided
            if query:
                search_term = f"%{query}%"
                where_clauses.append(
                    "(username LIKE ? OR email LIKE ? OR full_name LIKE ?)"
                )
                params.extend([search_term, search_term, search_term])

            # Add role filter if provided
            if role:
                where_clauses.append("role = ?")
                params.append(role)

            # Add WHERE clause if needed
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

            # Execute query
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()

            return row[0] if row else 0

        except Exception as e:
            logger.error(f"Error counting users: {e}")
            raise UserError(f"Failed to count users: {e}") from e
