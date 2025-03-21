import asyncio
import datetime
import hashlib
import logging
import os
from pathlib import Path

from the_aichemist_codex.backend.config.rules.rules_engine import rules_engine
from the_aichemist_codex.backend.rollback.rollback_manager import RollbackManager
from the_aichemist_codex.backend.utils.io.async_io import AsyncFileIO
from the_aichemist_codex.backend.utils.common.safety import SafeFileHandler

from .directory_manager import DirectoryManager

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


# Function to get data directory without depending on settings.py
def get_data_dir() -> Path:
    """
    Get the data directory without creating circular imports.

    Returns:
        Path: The data directory
    """
    # Check environment variable first
    env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir)

    # Fall back to a directory relative to the project root
    return Path(__file__).resolve().parents[3] / "data"


# Create a DirectoryManager instance for use across the module
directory_manager = DirectoryManager(get_data_dir())


class FileMover:
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.safe_scanner = SafeFileHandler

    @staticmethod
    async def get_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file using async I/O."""
        try:
            hasher = hashlib.sha256()
            # Use AsyncFileIO for reading the file in chunks
            async for chunk in AsyncFileIO.read_chunked(file_path, chunk_size=4096):
                hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    @staticmethod
    async def verify_file_copy(source: Path, destination: Path) -> bool:
        """Verify that the destination file exists and has the same size and hash as the source."""
        try:
            if not await AsyncFileIO.exists(destination):
                logger.error(f"Destination file does not exist: {destination}")
                return False

            # Check file sizes match
            source_size = await AsyncFileIO.get_file_size(source)
            dest_size = await AsyncFileIO.get_file_size(destination)

            if source_size is None or dest_size is None:
                logger.error(
                    f"Could not determine file size for {source} or {destination}"
                )
                return False

            if source_size != dest_size:
                logger.error(
                    f"File size mismatch: {source} ({source_size} bytes) -> {destination} ({dest_size} bytes)"
                )
                return False

            # For small files (< 10MB), also verify contents with hash
            if source_size < 10_000_000:
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
        """Safely remove a file using AsyncFileIO."""
        try:
            # Instead of using os.remove directly, use a helper method from AsyncFileIO
            # Since AsyncFileIO doesn't have a direct remove method, we'll simulate it
            # by deleting the content and then using asyncio to remove the file
            await asyncio.to_thread(lambda: file_path.unlink(missing_ok=True))
            logger.debug(f"Removed file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
            return False

    @staticmethod
    async def move_file(source: Path, destination: Path):
        """Move a file from source to destination using AsyncFileIO operations."""
        if SafeFileHandler.should_ignore(source):
            logger.info(f"Skipping ignored file: {source}")
            return

        # Create a backup BEFORE attempting any move
        try:
            # Use DATA_DIR from settings for backup location
            backup_dir = get_data_dir() / "backup/file_backups"
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
            await directory_manager.ensure_directory(destination.parent)

            # Check if destination already exists
            if await AsyncFileIO.exists(destination):
                logger.warning(f"Destination file already exists: {destination}")
                # Generate a unique name by adding a timestamp
                new_name = f"{destination.stem}_{int(datetime.datetime.now().timestamp())}{destination.suffix}"
                destination = destination.parent / new_name
                logger.info(f"Using alternative destination: {destination}")

            # For large files, use chunked copy operation
            file_size = await AsyncFileIO.get_file_size(source)
            if file_size and file_size > 10_000_000:  # 10MB threshold
                logger.info(
                    f"Using chunked copy for large file: {source} ({file_size} bytes)"
                )
                copy_success = await AsyncFileIO.copy_chunked(source, destination)
            else:
                # Use regular copy for smaller files
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
                        if await AsyncFileIO.exists(destination):
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
        """
        Apply organization rules to a file.

        Args:
            file_path: Path to the file to be organized

        Returns:
            bool: True if a rule was applied, False otherwise
        """
        # Ensure we're using an absolute, resolved path
        file_path = file_path.resolve()
        logger.info(f"Applying rules to: {file_path}")

        # Skip if the file no longer exists
        if not await AsyncFileIO.exists(file_path):
            logger.warning(f"File no longer exists: {file_path}")
            return False

        for rule in rules_engine.rules:
            # Check if the file matches rule extensions
            if any(
                file_path.suffix.lower() == ext.lower()
                for ext in rule.get("extensions", [])
            ):
                # Build target directory path
                target_dir = Path(rule["target_dir"])
                if not target_dir.is_absolute():
                    target_dir = self.base_directory / target_dir
                target_dir = target_dir.resolve()

                logger.info(
                    f"Rule matched for {file_path}. Target directory: {target_dir}"
                )

                # Ensure the target directory exists
                await directory_manager.ensure_directory(target_dir)

                # Move the file
                target_file = target_dir / file_path.name
                logger.info(f"Moving file to {target_file}")
                await FileMover.move_file(file_path, target_file)
                return True

        logger.info(f"No rules matched for {file_path}")
        return False

    async def auto_folder_structure(self, file_path: Path):
        """
        Create an automatic folder structure based on file type and date.

        Args:
            file_path: Path to the file to organize

        Returns:
            Path: Path to the target directory
        """
        # Ensure we're using an absolute, resolved path
        file_path = file_path.resolve()
        logger.info(f"Creating auto folder structure for: {file_path}")

        # Skip if the file no longer exists
        if not await AsyncFileIO.exists(file_path):
            logger.warning(f"File no longer exists: {file_path}")
            return self.base_directory / "organized" / "unknown"

        # Organize by file extension and creation date (YYYY-MM)
        ext = file_path.suffix.lower().lstrip(".")
        if not ext:
            ext = "no_extension"

        # Get file creation time
        try:
            # Use AsyncFileIO where possible
            file_stats = await asyncio.to_thread(file_path.stat)
            creation_time = file_stats.st_ctime
            dt = datetime.datetime.fromtimestamp(creation_time)
            date_folder = dt.strftime("%Y-%m")
        except Exception as e:
            logger.warning(f"Error getting creation time for {file_path}: {e}")
            date_folder = "unknown_date"

        # Create path structure
        target_dir = (self.base_directory / "organized" / ext / date_folder).resolve()
        logger.info(f"Auto-organization target directory: {target_dir}")

        # Ensure the directory exists
        await directory_manager.ensure_directory(target_dir)

        return target_dir
