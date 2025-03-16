import hashlib
import logging
from pathlib import Path

from backend.src.utils.async_io import AsyncFileIO

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

    async def scan_directory(
        self, directory: Path, method="md5"
    ) -> dict[str, list[Path]]:
        """
        Scan a directory for duplicate files.

        Args:
            directory: Path to the directory to scan
            method: Either a specific hash algorithm (md5, sha1, sha256) or
                    a method name (hash, name, content)

        Returns:
            Dictionary mapping hash values to lists of file paths
        """
        # Translate method name to actual hash algorithm if needed
        hash_algo = method
        if method == "hash":
            # Default to md5 when "hash" is specified as the method
            hash_algo = "md5"
        elif method == "name" or method == "content":
            # Handle other methods (these would need their own implementation)
            logger.warning(f"Method '{method}' not fully implemented; using md5 hash")
            hash_algo = "md5"

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
