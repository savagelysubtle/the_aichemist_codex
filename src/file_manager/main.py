import logging
import sys

from .file_mover import FileMover
from .json_loader import load_file_moves

# Configure logging globally
logging.basicConfig(
    filename="file_manager.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Entry point when running as a script."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <file_moves.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    file_moves = load_file_moves(json_file)

    if not file_moves:
        print("No valid file moves found.")
        sys.exit(1)

    mover = FileMover(base_dir="D:/Sorted_Files")
    mover.batch_move_files(file_moves)
    print("🎯 File Management Completed")


if __name__ == "__main__":
    main()
