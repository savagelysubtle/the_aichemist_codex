from pathlib import Path


class SafeDirectoryScanner:
    @staticmethod
    def is_safe_path(target: Path, base: Path) -> bool:
        try:
            return base.resolve() in target.resolve().parents
        except (FileNotFoundError, RuntimeError):
            return False
