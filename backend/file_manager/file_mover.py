import asyncio
import datetime
import hashlib
import logging
import os
from pathlib import Path

from backend.config.rules_engine import rules_engine
from backend.rollback.rollback_manager import RollbackManager
from backend.utils.async_io import AsyncFileIO
from backend.utils.safety import SafeFileHandler

from .directory_manager import DirectoryManager as DirectoryManager

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class FileMover:
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.safe_scanner = SafeFileHandler

    @staticmethod
    async def get_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            hasher = hashlib.sha256()
            # Read file in chunks to handle large files efficiently
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    @staticmethod
    async def verify_file_copy(source: Path, destination: Path) -> bool:
        """Verify that the destination file exists and has the same size and hash as the source."""
        try:
            if not destination.exists():
                logger.error(f"Destination file does not exist: {destination}")
                return False

            # Check file sizes match
            if source.stat().st_size != destination.stat().st_size:
                logger.error(
                    f"File size mismatch: {source} ({source.stat().st_size} bytes) -> {destination} ({destination.stat().st_size} bytes)"
                )
                return False

            # For small files (< 10MB), also verify contents with hash
            if source.stat().st_size < 10_000_000:
                source_hash = await FileMover.get_file_hash(source)
                dest_hash = await FileMover.get_file_hash(destination)
                if source_hash != dest_hash:
                    logger.error(f"File hash mismatch: {source} -> {destination}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error verifying file copy {source} -> {destination}: {e}")
            return False

    @staticmethod
    async def safe_remove_file(file_path: Path) -> bool:
        """Safely remove a file, ensuring it doesn't go to trash."""
        try:
            # Use os.remove to bypass trash bin
            await asyncio.to_thread(os.remove, str(file_path))
            return True
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
            return False

    @staticmethod
    async def move_file(source: Path, destination: Path):
        if SafeFileHandler.should_ignore(source):
            logger.info(f"Skipping ignored file: {source}")
            return

        # Create a backup BEFORE attempting any move
        try:
            # Ensure backup directory exists
            backup_dir = Path("backup/file_backups")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create timestamped backup
            timestamp = int(datetime.datetime.now().timestamp())
            backup_path = backup_dir / f"{source.name}.{timestamp}.bak"

            # Perform backup
            await AsyncFileIO.copy(source, backup_path)
            logger.info(f"Created backup of {source} at {backup_path}")
        except Exception as backup_error:
            logger.error(f"Failed to create backup of {source}: {backup_error}")
            # Even if backup fails, we'll continue with the move

        # Track success for rollback operations
        move_successful = False

        try:
            # Ensure destination directory exists asynchronously
            await DirectoryManager.ensure_directory(destination.parent)

            # Check if destination already exists
            if destination.exists():
                logger.warning(f"Destination file already exists: {destination}")
                # Generate a unique name by adding a timestamp
                new_name = f"{destination.stem}_{int(datetime.datetime.now().timestamp())}{destination.suffix}"
                destination = destination.parent / new_name
                logger.info(f"Using alternative destination: {destination}")

            # Perform the copy operation
            copy_success = await AsyncFileIO.copy(source, destination)

            if copy_success:
                # Verify the file was copied correctly
                verification = await FileMover.verify_file_copy(source, destination)

                if verification:
                    logger.info(f"Verified copy successful: {source} -> {destination}")

                    # Remove original file only after successful copy and verification
                    removal_success = await FileMover.safe_remove_file(source)

                    if removal_success:
                        logger.info(f"Moved {source} -> {destination}")
                        move_successful = True
                    else:
                        logger.error(
                            f"Failed to remove source file after copying: {source}"
                        )
                else:
                    logger.error(
                        f"File verification failed, cancelling move operation: {source} -> {destination}"
                    )
                    # Try to clean up the potentially corrupted destination file
                    try:
                        if destination.exists():
                            await FileMover.safe_remove_file(destination)
                    except Exception as cleanup_error:
                        logger.error(
                            f"Error cleaning up destination file: {cleanup_error}"
                        )
            else:
                logger.error(f"Failed to copy {source} to {destination}")
        except Exception as e:
            logger.error(f"Error moving {source}: {e}")

        # ALWAYS record the operation, even if it failed
        try:
            # Use await to properly wait for the coroutine
            await rollback_manager.record_operation(
                "move", str(source), str(destination)
            )
        except Exception as rollback_error:
            logger.error(f"Error recording rollback operation: {rollback_error}")

    async def apply_rules(self, file_path: Path):
        for rule in rules_engine.rules:
            if any(
                file_path.suffix.lower() == ext.lower()
                for ext in rule.get("extensions", [])
            ):
                target_dir = Path(rule["target_dir"])
                if not target_dir.is_absolute():
                    target_dir = self.base_directory / target_dir
                await DirectoryManager.ensure_directory(target_dir)
                await FileMover.move_file(file_path, target_dir / file_path.name)
                return True
        return False

    async def auto_folder_structure(self, file_path: Path):
        # Organize by file extension and creation date (YYYY-MM).
        ext = file_path.suffix.lower().lstrip(".")
        creation_time = file_path.stat().st_ctime
        dt = datetime.datetime.fromtimestamp(creation_time)
        date_folder = dt.strftime("%Y-%m")
        target_dir = self.base_directory / "organized" / ext / date_folder
        await DirectoryManager.ensure_directory(target_dir)
        return target_dir
