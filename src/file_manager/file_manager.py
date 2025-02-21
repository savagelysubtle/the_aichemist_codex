import json
import logging
import shutil
import sys
from pathlib import Path

from common.logging_config import logger

logger.info("This is a log message.")

# Configure logging to print and save logs
logging.basicConfig(
    filename="file_manager.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

print("🚀 File Manager Script Started")  # Debugging


class FileManager:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.ensure_directory(self.base_dir)
        print(f"📂 Base directory set to: {self.base_dir}")

    @staticmethod
    def ensure_directory(directory: Path):
        """Ensures that a directory exists."""
        directory.mkdir(parents=True, exist_ok=True)

    def move_file(self, src: str, dest: str):
        """Moves a file to the specified destination, ensuring the directory exists."""
        try:
            src_path = Path(src)
            dest_path = self.base_dir / dest

            if not src_path.exists():
                logging.error(f"❌ Source file does not exist: {src_path}")
                print(f"❌ Source file not found: {src_path}")
                return False

            self.ensure_directory(dest_path.parent)
            shutil.move(str(src_path), str(dest_path))

            logging.info(f"✅ Moved {src} → {dest_path}")
            print(f"✅ Moved {src} → {dest_path}")
            return True
        except Exception as e:
            logging.error(f"❌ Error moving {src} → {dest_path}: {e}")
            print(f"❌ Error moving {src}: {e}")
            return False

    def batch_move_files(self, file_mapping: dict):
        """Moves multiple files in a batch."""
        if not file_mapping:
            print("⚠️ No files to move.")
            return

        print(f"📦 Moving {len(file_mapping)} files...")
        for src, dest_folder in file_mapping.items():
            dest_path = Path(dest_folder) / Path(src).name
            self.move_file(src, str(dest_path))


# ✅ Ensure script executes
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ No JSON file provided. Usage:")
        print("   python file_manager.py file_moves.json")
        sys.exit(1)

    json_file = sys.argv[1]

    # Load the JSON file
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            file_moves = json.load(f)

        fm = FileManager(base_dir="D:/Sorted_Files")
        fm.batch_move_files(file_moves)

        print("🎯 File Management Completed")

    except Exception as e:
        print(f"❌ Failed to load JSON file: {json_file}. Error: {e}")
        logging.error(f"❌ Error loading JSON: {e}")
