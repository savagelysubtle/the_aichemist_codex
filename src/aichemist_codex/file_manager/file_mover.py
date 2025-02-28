import datetime
import logging
import shutil
from pathlib import Path

from aichemist_codex.config.rules_engine import rules_engine
from aichemist_codex.file_manager.directory_manager import DirectoryManager
from aichemist_codex.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)


class FileMover:
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.safe_scanner = SafeFileHandler

    @staticmethod
    def move_file(source: Path, destination: Path):
        if SafeFileHandler.should_ignore(source):
            logger.info(f"Skipping ignored file: {source}")
            return
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            logger.info(f"Moved {source} -> {destination}")
        except Exception as e:
            logger.error(f"Error moving {source}: {e}")

    def apply_rules(self, file_path: Path):
        for rule in rules_engine.rules:
            if any(
                file_path.suffix.lower() == ext.lower()
                for ext in rule.get("extensions", [])
            ):
                target_dir = Path(rule["target_dir"])
                if not target_dir.is_absolute():
                    target_dir = self.base_directory / target_dir
                DirectoryManager.ensure_directory(target_dir)
                self.move_file(file_path, target_dir / file_path.name)
                return True
        return False

    def auto_folder_structure(self, file_path: Path):
        # Organize by file extension and creation date (YYYY-MM).
        ext = file_path.suffix.lower().lstrip(".")
        creation_time = file_path.stat().st_ctime
        dt = datetime.datetime.fromtimestamp(creation_time)
        date_folder = dt.strftime("%Y-%m")
        target_dir = self.base_directory / "organized" / ext / date_folder
        DirectoryManager.ensure_directory(target_dir)
        return target_dir
