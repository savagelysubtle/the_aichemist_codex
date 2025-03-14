"""Provides batch file operations with rollback support."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

from backend.rollback.rollback_manager import rollback_manager
from backend.utils.async_io import AsyncFileIO
from backend.utils.batch_processor import BatchProcessor
from backend.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)


class BatchFileOperations:
    """Handles batch file operations with rollback support."""

    @staticmethod
    async def move_files(
        file_mappings: Dict[Path, Path], batch_size: int = 10
    ) -> List[Tuple[Path, Path]]:
        """
        Move multiple files in batches with rollback tracking.

        Args:
            file_mappings: Dict mapping source paths to destination paths
            batch_size: Number of files to move in each batch

        Returns:
            List of successfully moved files (source, destination) tuples
        """
        # Convert dict to list of tuples for batch processing
        operations = [(src, dst) for src, dst in file_mappings.items()]

        # Safety checks before processing
        for src, dst in operations:
            if not await AsyncFileIO.exists(src):
                logger.error(f"Source file does not exist: {src}")
                return []
            if SafeFileHandler.should_ignore(src):
                logger.warning(f"Ignoring blocked file: {src}")
                return []

        async def move_operation(item: Tuple[Path, Path]) -> Tuple[Path, Path]:
            src, dst = item

            # Record operation for rollback
            await rollback_manager.record_operation("move", src, dst)

            # Ensure destination directory exists
            await AsyncFileIO.write("", dst.parent / ".placeholder")

            # Move the file
            content = await AsyncFileIO.read_binary(src)
            success = await AsyncFileIO.write_binary(dst, content)

            if success:
                try:
                    os.remove(src)
                    return (src, dst)
                except Exception as e:
                    logger.error(f"Error removing source file {src}: {e}")
                    # Try to rollback the write
                    await AsyncFileIO.write_binary(src, content)
                    raise e
            else:
                raise Exception(f"Failed to write file to {dst}")

        results = await BatchProcessor.process_batch(
            operations, move_operation, batch_size=batch_size
        )

        return results

    @staticmethod
    async def copy_files(
        file_mappings: Dict[Path, Path], batch_size: int = 10
    ) -> List[Tuple[Path, Path]]:
        """
        Copy multiple files in batches with rollback tracking.

        Args:
            file_mappings: Dict mapping source paths to destination paths
            batch_size: Number of files to copy in each batch

        Returns:
            List of successfully copied files (source, destination) tuples
        """
        operations = [(src, dst) for src, dst in file_mappings.items()]

        # Safety checks before processing
        for src, dst in operations:
            if not await AsyncFileIO.exists(src):
                logger.error(f"Source file does not exist: {src}")
                return []
            if SafeFileHandler.should_ignore(src):
                logger.warning(f"Ignoring blocked file: {src}")
                return []

        async def copy_operation(item: Tuple[Path, Path]) -> Tuple[Path, Path]:
            src, dst = item

            # Record operation for rollback
            await rollback_manager.record_operation("copy", src, dst)

            # Ensure destination directory exists
            await AsyncFileIO.write("", dst.parent / ".placeholder")

            # Copy the file
            success = await AsyncFileIO.copy(src, dst)

            if success:
                return (src, dst)
            else:
                raise Exception(f"Failed to copy file to {dst}")

        results = await BatchProcessor.process_batch(
            operations, copy_operation, batch_size=batch_size
        )

        return results

    @staticmethod
    async def delete_files(files: List[Path], batch_size: int = 10) -> List[Path]:
        """
        Delete multiple files in batches with rollback tracking.

        Args:
            files: List of file paths to delete
            batch_size: Number of files to delete in each batch

        Returns:
            List of successfully deleted file paths
        """
        # Safety checks before processing
        for file_path in files:
            if not await AsyncFileIO.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return []
            if SafeFileHandler.should_ignore(file_path):
                logger.warning(f"Ignoring blocked file: {file_path}")
                return []

        async def delete_operation(file_path: Path) -> Path:
            # Record operation for rollback and backup the file
            content = await AsyncFileIO.read_binary(file_path)
            await rollback_manager.record_operation(
                "delete", file_path, backup_content=content
            )

            try:
                os.remove(file_path)
                return file_path
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                # Try to restore the file
                await AsyncFileIO.write_binary(file_path, content)
                raise e

        results = await BatchProcessor.process_batch(
            files, delete_operation, batch_size=batch_size
        )

        return results
