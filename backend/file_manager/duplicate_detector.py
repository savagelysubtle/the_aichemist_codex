import hashlib
import logging
from pathlib import Path

from backend.utils.async_io import AsyncFileIO

logger = logging.getLogger(__name__)


class DuplicateDetector:
    def __init__(self):
        self.hashes = {}  # Maps file hash to a list of file paths.

    async def compute_hash(self, file_path: Path, hash_algo="md5") -> str:
        h = hashlib.new(hash_algo)
        try:
            data = await AsyncFileIO.read_binary(file_path)
            h.update(data)
            return h.hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return ""

    async def scan_directory(self, directory: Path, hash_algo="md5"):
        for file in directory.rglob("*"):
            if file.is_file():
                file_hash = await self.compute_hash(file, hash_algo)
                if file_hash:
                    if file_hash in self.hashes:
                        self.hashes[file_hash].append(file)
                    else:
                        self.hashes[file_hash] = [file]
        return self.hashes

    def get_duplicates(self):
        # Return only the hashes with more than one file.
        return {h: files for h, files in self.hashes.items() if len(files) > 1}
