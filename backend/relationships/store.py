"""
Relationship storage functionality.

This module provides classes and utilities for storing and retrieving
file relationships in a persistent database.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .relationship import Relationship, RelationshipType

logger = logging.getLogger(__name__)


class RelationshipStore:
    """
    Stores and retrieves file relationships in a SQLite database.

    This class handles the persistence of relationship data, providing
    methods to add, update, query, and delete relationships.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the relationship store with the given database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Initialize the database schema if it doesn't exist.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create relationships table
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    rel_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
                )

                # Create indexes for faster querying
                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_source_path ON relationships (source_path)
                """
                )

                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_target_path ON relationships (target_path)
                """
                )

                cursor.execute(
                    """
                CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships (rel_type)
                """
                )

                conn.commit()
                logger.debug("Relationship database initialized")
        except sqlite3.Error as e:
            logger.error(f"Error initializing relationship database: {str(e)}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.

        Returns:
            SQLite connection object
        """
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def add_relationship(self, relationship: Relationship) -> None:
        """
        Add a new relationship to the store.

        Args:
            relationship: The relationship to add

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Convert metadata to JSON string
                metadata_json = json.dumps(relationship.metadata)

                cursor.execute(
                    """
                INSERT OR REPLACE INTO relationships
                (id, source_path, target_path, rel_type, strength, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        relationship.id,
                        str(relationship.source_path),
                        str(relationship.target_path),
                        relationship.rel_type.name,
                        relationship.strength,
                        metadata_json,
                        relationship.created_at.isoformat(),
                        relationship.updated_at.isoformat(),
                    ),
                )

                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error adding relationship: {str(e)}")
            raise

    def add_relationships(self, relationships: List[Relationship]) -> None:
        """
        Add multiple relationships to the store in a single transaction.

        Args:
            relationships: List of relationships to add

        Raises:
            sqlite3.Error: If there's a database error
        """
        if not relationships:
            return

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                for relationship in relationships:
                    # Convert metadata to JSON string
                    metadata_json = json.dumps(relationship.metadata)

                    cursor.execute(
                        """
                    INSERT OR REPLACE INTO relationships
                    (id, source_path, target_path, rel_type, strength, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            relationship.id,
                            str(relationship.source_path),
                            str(relationship.target_path),
                            relationship.rel_type.name,
                            relationship.strength,
                            metadata_json,
                            relationship.created_at.isoformat(),
                            relationship.updated_at.isoformat(),
                        ),
                    )

                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error adding relationships: {str(e)}")
            raise

    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """
        Get a relationship by its ID.

        Args:
            relationship_id: ID of the relationship to retrieve

        Returns:
            The relationship if found, None otherwise

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                SELECT * FROM relationships WHERE id = ?
                """,
                    (relationship_id,),
                )

                row = cursor.fetchone()
                if row:
                    return self._row_to_relationship(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting relationship: {str(e)}")
            raise

    def get_relationships_for_file(
        self,
        file_path: Path,
        as_source: bool = True,
        as_target: bool = True,
        rel_types: Optional[List[RelationshipType]] = None,
    ) -> List[Relationship]:
        """
        Get all relationships for a specific file.

        Args:
            file_path: Path to the file
            as_source: Include relationships where file is the source
            as_target: Include relationships where file is the target
            rel_types: Optional filter for relationship types

        Returns:
            List of relationships involving the file

        Raises:
            sqlite3.Error: If there's a database error
        """
        if not as_source and not as_target:
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query_parts = []
                params = []

                if as_source:
                    query_parts.append("source_path = ?")
                    params.append(str(file_path))

                if as_target:
                    query_parts.append("target_path = ?")
                    params.append(str(file_path))

                query = f"SELECT * FROM relationships WHERE {' OR '.join(query_parts)}"

                # Add relationship type filter if specified
                if rel_types:
                    type_placeholders = ", ".join("?" for _ in rel_types)
                    query += f" AND rel_type IN ({type_placeholders})"
                    params.extend(rel_type.name for rel_type in rel_types)

                cursor.execute(query, params)

                return [self._row_to_relationship(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting relationships for file: {str(e)}")
            raise

    def get_related_files(
        self,
        file_path: Path,
        rel_types: Optional[List[RelationshipType]] = None,
        min_strength: float = 0.0,
    ) -> List[Tuple[Path, RelationshipType, float]]:
        """
        Get all files related to the given file.

        Args:
            file_path: Path to the file
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            List of tuples containing (related_file_path, relationship_type, strength)

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build query for outgoing relationships (file as source)
                query_outgoing = """
                SELECT target_path, rel_type, strength
                FROM relationships
                WHERE source_path = ? AND strength >= ?
                """

                # Build query for incoming relationships (file as target)
                query_incoming = """
                SELECT source_path, rel_type, strength
                FROM relationships
                WHERE target_path = ? AND strength >= ?
                """

                params = [str(file_path), min_strength]

                # Add relationship type filter if specified
                if rel_types:
                    type_placeholders = ", ".join("?" for _ in rel_types)
                    query_outgoing += f" AND rel_type IN ({type_placeholders})"
                    query_incoming += f" AND rel_type IN ({type_placeholders})"
                    params.extend(rel_type.name for rel_type in rel_types)

                # Execute queries
                cursor.execute(query_outgoing, params)
                outgoing_results = [
                    (
                        Path(row["target_path"]),
                        RelationshipType[row["rel_type"]],
                        row["strength"],
                    )
                    for row in cursor.fetchall()
                ]

                cursor.execute(query_incoming, params)
                incoming_results = [
                    (
                        Path(row["source_path"]),
                        RelationshipType[row["rel_type"]],
                        row["strength"],
                    )
                    for row in cursor.fetchall()
                ]

                # Combine results
                return outgoing_results + incoming_results
        except sqlite3.Error as e:
            logger.error(f"Error getting related files: {str(e)}")
            raise

    def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship by its ID.

        Args:
            relationship_id: ID of the relationship to delete

        Returns:
            True if the relationship was deleted, False if not found

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                DELETE FROM relationships WHERE id = ?
                """,
                    (relationship_id,),
                )

                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting relationship: {str(e)}")
            raise

    def delete_relationships_for_file(self, file_path: Path) -> int:
        """
        Delete all relationships involving a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Number of relationships deleted

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                DELETE FROM relationships
                WHERE source_path = ? OR target_path = ?
                """,
                    (str(file_path), str(file_path)),
                )

                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error deleting relationships for file: {str(e)}")
            raise

    def clear_all_relationships(self) -> int:
        """
        Delete all relationships from the store.

        Returns:
            Number of relationships deleted

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM relationships")

                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Error clearing relationships: {str(e)}")
            raise

    def get_all_relationships(
        self,
        rel_types: Optional[List[RelationshipType]] = None,
        min_strength: float = 0.0,
    ) -> List[Relationship]:
        """
        Get all relationships in the store.

        Args:
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            List of all relationships

        Raises:
            sqlite3.Error: If there's a database error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM relationships WHERE strength >= ?"
                params = [min_strength]

                # Add relationship type filter if specified
                if rel_types:
                    type_placeholders = ", ".join("?" for _ in rel_types)
                    query += f" AND rel_type IN ({type_placeholders})"
                    params.extend(rel_type.name for rel_type in rel_types)

                cursor.execute(query, params)

                return [self._row_to_relationship(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting all relationships: {str(e)}")
            raise

    def _row_to_relationship(self, row: sqlite3.Row) -> Relationship:
        """
        Convert a database row to a Relationship object.

        Args:
            row: SQLite row containing relationship data

        Returns:
            Relationship object
        """
        return Relationship(
            source_path=Path(row["source_path"]),
            target_path=Path(row["target_path"]),
            rel_type=RelationshipType[row["rel_type"]],
            strength=row["strength"],
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            id=row["id"],
        )
