import asyncio
import datetime
import logging
from pathlib import Path

from backend.config.rules_engine import rules_engine
from backend.rollback.rollback_manager import RollbackManager
from backend.utils.async_io import AsyncFileIO
from backend.utils.safety import SafeFileHandler

from .directory_manager import DirectoryManager as directory_manager

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class FileMover:
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.safe_scanner = SafeFileHandler

    @staticmethod
    async def move_file(source: Path, destination: Path):
        if SafeFileHandler.should_ignore(source):
            logger.info(f"Skipping ignored file: {source}")
            return
        try:
            # Ensure destination directory exists asynchronously.
            await directory_manager.DirectoryManager.ensure_directory(
                destination.parent
            )
            if await AsyncFileIO.copy(source, destination):
                # Remove the source file in a non-blocking way.
                await asyncio.to_thread(source.unlink)
                logger.info(f"Moved {source} -> {destination}")
                # Record the move operation for potential rollback.
                rollback_manager.record_operation("move", str(source), str(destination))
            else:
                logger.error(f"Failed to copy {source} to {destination}")
        except Exception as e:
            logger.error(f"Error moving {source}: {e}")

    async def apply_rules(self, file_path: Path):
        for rule in rules_engine.rules:
            if any(
                file_path.suffix.lower() == ext.lower()
                for ext in rule.get("extensions", [])
            ):
                target_dir = Path(rule["target_dir"])
                if not target_dir.is_absolute():
                    target_dir = self.base_directory / target_dir
                await directory_manager.DirectoryManager.ensure_directory(target_dir)
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
        await directory_manager.DirectoryManager.ensure_directory(target_dir)
        return target_dir
