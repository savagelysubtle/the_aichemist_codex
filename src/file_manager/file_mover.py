import logging
import shutil
from pathlib import Path

from .directory_manager import DirectoryManager

logger = logging.getLogger(__name__)


class FileMover:
    """Handles file moving operations."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        DirectoryManager.ensure_directory(self.base_dir)
        logger.info(f"Base directory set to: {self.base_dir}")

    def move_file(self, src: str, dest: str) -> bool:
        """
        Moves a file from src to dest.
        - Ensures the destination directory exists.
        - Logs success or failure.
        """
        try:
            src_path = Path(src)
            dest_path = self.base_dir / dest

            if not src_path.exists():
                logger.error(f"Source file does not exist: {src_path}")
                return False

            DirectoryManager.ensure_directory(dest_path.parent)
            shutil.move(str(src_path), str(dest_path))

            logger.info(f"Moved {src} → {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Error moving {src} → {dest_path}: {e}")
            return False

    def batch_move_files(self, file_mapping: dict):
        """Moves multiple files based on a provided dictionary mapping."""
        if not file_mapping:
            logger.warning("No files to move.")
            return

        logger.info(f"Starting batch move for {len(file_mapping)} files.")
        for src, dest_folder in file_mapping.items():
            dest_path = Path(dest_folder) / Path(src).name
            self.move_file(src, str(dest_path))
        logger.info("Batch file move completed.")
