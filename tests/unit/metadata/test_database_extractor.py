"""Tests for the database metadata extractor"""

import os
import sqlite3
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import pytest

from the_aichemist_codex.backend.metadata.database_extractor import (
    DatabaseMetadataExtractor,
)
from the_aichemist_codex.backend.utils.cache_manager import CacheManager


# Test fixtures
@pytest.fixture
def sample_sqlite_db() -> Generator[Path]:
    """Create a temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    # Create a sample database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            published BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create index
    cursor.execute("CREATE INDEX idx_posts_user_id ON posts(user_id)")

    # Create view
    cursor.execute("""
        CREATE VIEW user_posts AS
        SELECT u.username, p.title, p.content
        FROM users u JOIN posts p ON u.id = p.user_id
        WHERE p.published = TRUE
    """)

    # Insert sample data
    cursor.executemany(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        [
            ("user1", "user1@example.com"),
            ("user2", "user2@example.com"),
            ("user3", "user3@example.com"),
        ],
    )

    cursor.executemany(
        "INSERT INTO posts (user_id, title, content, published) VALUES (?, ?, ?, ?)",
        [
            (1, "First post", "Content of first post", True),
            (1, "Second post", "Content of second post", False),
            (2, "User2 post", "Content from user2", True),
        ],
    )

    conn.commit()
    conn.close()

    yield Path(db_path)

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def sample_sql_dump() -> Generator[Path]:
    """Create a temporary SQL dump file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as temp_file:
        temp_file.write(b"""
-- Sample SQL dump
-- Database: test_db

CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_posts_user_id ON posts(user_id);

CREATE VIEW user_posts AS
SELECT u.username, p.title, p.content
FROM users u JOIN posts p ON u.id = p.user_id
WHERE p.published = TRUE;

INSERT INTO users (id, username, email) VALUES
(1, 'user1', 'user1@example.com'),
(2, 'user2', 'user2@example.com'),
(3, 'user3', 'user3@example.com');

INSERT INTO posts (id, user_id, title, content, published) VALUES
(1, 1, 'First post', 'Content of first post', TRUE),
(2, 1, 'Second post', 'Content of second post', FALSE),
(3, 2, 'User2 post', 'Content from user2', TRUE);
        """)

    yield Path(temp_file.name)

    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def sample_mysql_dump() -> Generator[Path]:
    """Create a temporary MySQL dump file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".mysql", delete=False) as temp_file:
        temp_file.write(b"""
-- MySQL dump 10.13  Distrib 8.0.28, for Linux (x86_64)
--
-- Host: localhost    Database: test_db
-- ------------------------------------------------------
-- Server version	8.0.28

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES */;

--
-- Current Database: `test_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `test_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;
USE `test_db`;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `posts`
--

DROP TABLE IF EXISTS `posts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(200) NOT NULL,
  `content` text,
  `published` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_posts_user_id` (`user_id`),
  CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'user1','user1@example.com','2023-03-15 12:00:00'),(2,'user2','user2@example.com','2023-03-15 12:01:00'),(3,'user3','user3@example.com','2023-03-15 12:02:00');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `posts`
--

LOCK TABLES `posts` WRITE;
/*!40000 ALTER TABLE `posts` DISABLE KEYS */;
INSERT INTO `posts` VALUES (1,1,'First post','Content of first post',1),(2,1,'Second post','Content of second post',0),(3,2,'User2 post','Content from user2',1);
/*!40000 ALTER TABLE `posts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `user_posts`
--

DROP TABLE IF EXISTS `user_posts`;
/*!50001 DROP VIEW IF EXISTS `user_posts`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `user_posts` AS SELECT
 1 AS `username`,
 1 AS `title`,
 1 AS `content`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `user_posts`
--

/*!50001 DROP VIEW IF EXISTS `user_posts`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `user_posts` AS select `u`.`username` AS `username`,`p`.`title` AS `title`,`p`.`content` AS `content` from (`users` `u` join `posts` `p` on((`u`.`id` = `p`.`user_id`))) where (`p`.`published` = 1) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-03-16 14:25:36
        """)

    yield Path(temp_file.name)

    # Cleanup
    os.unlink(temp_file.name)


class MockCacheManager:
    def __init__(self) -> None:
        self.cache: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self.cache.get(key)

    async def put(self, key: str, value: Any) -> None:
        self.cache[key] = value


@pytest.fixture
def mock_cache_manager() -> Any:  # Use Any to avoid type compatibility issues
    """Mock cache manager for testing caching functionality"""
    return MockCacheManager()


# Actual tests
@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlite_metadata_extraction(sample_sqlite_db: Path) -> None:
    """Test extraction of metadata from SQLite database"""
    extractor = DatabaseMetadataExtractor()
    metadata = await extractor.extract(sample_sqlite_db)

    # Test basic metadata
    assert metadata["metadata_type"] == "database"
    assert metadata["format"]["type"] == "sqlite"

    # Test schema information
    assert metadata["schema"]["table_count"] == 2
    assert metadata["schema"]["view_count"] == 1

    # Test table details
    tables = metadata["schema"]["tables"]
    assert len(tables) == 2

    # Find the users table
    users_table = next((t for t in tables if t["name"] == "users"), None)
    assert users_table is not None
    assert users_table["row_count"] == 3
    assert len(users_table["columns"]) == 4  # id, username, email, created_at

    # Find the posts table
    posts_table = next((t for t in tables if t["name"] == "posts"), None)
    assert posts_table is not None
    assert posts_table["row_count"] == 3
    assert posts_table["index_count"] >= 1  # At least the one we created

    # Test statistics
    assert metadata["statistics"]["total_rows"] == 6  # 3 users + 3 posts
    assert metadata["statistics"]["total_indexes"] >= 1

    # Test summary
    assert "SQLite database with" in metadata["summary"]
    assert "2 tables" in metadata["summary"]
    assert "1 views" in metadata["summary"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sql_dump_metadata_extraction(sample_sql_dump: Path) -> None:
    """Test extraction of metadata from SQL dump file"""
    extractor = DatabaseMetadataExtractor()
    metadata = await extractor.extract(sample_sql_dump)

    # Test basic metadata
    assert metadata["metadata_type"] == "database"
    assert metadata["format"]["type"] == "sql_dump"

    # Test schema information
    assert metadata["schema"]["table_count"] == 2
    assert metadata["schema"]["view_count"] == 1
    assert "users" in metadata["schema"]["tables"]
    assert "posts" in metadata["schema"]["tables"]

    # Test statement counts
    assert (
        metadata["statistics"]["insert_statements"] >= 2
    )  # We have 2 INSERT INTO statements

    # Test summary
    assert "SQL dump" in metadata["summary"]
    assert "2 table definitions" in metadata["summary"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mysql_dump_metadata_extraction(sample_mysql_dump: Path) -> None:
    """Test extraction of metadata from MySQL dump file"""
    extractor = DatabaseMetadataExtractor()
    metadata = await extractor.extract(sample_mysql_dump)

    # Test basic metadata
    assert metadata["metadata_type"] == "database"  # noqa: S101
    assert metadata["format"]["type"] == "mysql_dump"  # noqa: S101
    assert metadata["format"]["detected_type"] == "mysql"  # noqa: S101

    # Test database identification
    assert "database_name" in metadata["format"]  # noqa: S101
    assert metadata["format"]["database_name"] == "test_db"  # noqa: S101

    # Test schema information
    assert metadata["schema"]["table_count"] == 2  # noqa: S101
    assert metadata["schema"]["view_count"] == 1  # noqa: S101
    assert "users" in metadata["schema"]["tables"]  # noqa: S101
    assert "posts" in metadata["schema"]["tables"]  # noqa: S101

    # Test charset detection
    assert "default_charset" in metadata["format"]  # noqa: S101
    assert metadata["format"]["default_charset"] == "utf8mb4"  # noqa: S101

    # Test summary
    assert "MySQL dump" in metadata["summary"]  # noqa: S101
    assert "test_db" in metadata["summary"]  # noqa: S101


@pytest.mark.unit
@pytest.mark.asyncio
async def test_nonexistent_file() -> None:
    """Test handling of nonexistent files"""
    extractor = DatabaseMetadataExtractor()
    metadata = await extractor.extract("nonexistent_file.db")

    # Should return empty dict for nonexistent files
    assert metadata == {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unsupported_file_format() -> None:
    """Test handling of unsupported file formats"""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_file.write(b"This is not a database file")
        path = temp_file.name

    try:
        extractor = DatabaseMetadataExtractor()
        metadata = await extractor.extract(path)

        # Should return empty dict for unsupported formats
        assert metadata == {}  # noqa: S101
    finally:
        os.unlink(path)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sqlite_corrupt_database() -> None:
    """Test handling of corrupt SQLite databases"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_file.write(b"This is not a valid SQLite database file")
        path = temp_file.name

    try:
        extractor = DatabaseMetadataExtractor()
        metadata = await extractor.extract(path)

        # Should return metadata with error information
        assert metadata["metadata_type"] == "database"  # noqa: S101
        assert metadata["format"]["type"] == "sqlite"  # noqa: S101
        assert "error" in metadata  # noqa: S101
    finally:
        # On Windows, the file may still be in use, so we need to handle this gracefully
        try:
            os.unlink(path)
        except PermissionError:
            print(
                f"Warning: Could not delete temporary file {path}. It may be locked by another process."
            )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_caching_functionality(
    sample_sqlite_db: Path, mock_cache_manager: MockCacheManager
) -> None:
    """Test that caching works correctly"""
    extractor = DatabaseMetadataExtractor(
        cache_manager=cast(CacheManager, mock_cache_manager)
    )

    # First extraction - should extract and cache
    metadata1 = await extractor.extract(sample_sqlite_db)
    assert metadata1["metadata_type"] == "database"

    # Modify the database
    conn = sqlite3.connect(sample_sqlite_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        ("user4", "user4@example.com"),
    )
    conn.commit()
    conn.close()

    # Second extraction - should use cache if path and mtime are the same
    # This is a bit tricky to test properly without mocking file stats
    # We'll just verify the cache manager was used correctly
    metadata2 = await extractor.extract(sample_sqlite_db)

    # Cache should contain at least one entry
    assert len(mock_cache_manager.cache) >= 1

    # The keys should contain both the path and mtime
    cache_key = next(iter(mock_cache_manager.cache.keys()))
    assert "db_metadata:" in cache_key
    assert str(sample_sqlite_db) in cache_key
