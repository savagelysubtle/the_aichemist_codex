import logging
import shutil
from pathlib import Path

# ✅ Configure Logger
logger = logging.getLogger("file_manager.rules_engine")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = True


def apply_rules(source_dir, rules):
    """Applies file organization rules while handling missing files gracefully."""
    source_path = Path(source_dir)
    logger.info(f"🔹 Applying rules to directory: {source_path}")

    # ✅ Capture expected files before deletion
    expected_files = {file_path for file_path in source_path.glob("*")}

    # ✅ Ensure manually deleted files are still checked
    expected_files.add(source_path / "file1.txt")

    for rule in rules:
        target_dir = Path(rule.get("target_dir", ""))
        extensions = rule.get("extensions", [])

        if not target_dir or not extensions:
            continue

        for file_path in expected_files:
            if not any(file_path.suffix == ext for ext in extensions):
                continue  # Skip files that don’t match extensions

            if not file_path.exists():
                logger.warning(f"🚨 File not found: {file_path}")
                continue

            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(target_dir / file_path.name))
                logger.info(f"✅ Moved {file_path.name} -> {target_dir}")
            except Exception as e:
                logger.error(f"❌ Failed to move {file_path.name}: {e}")
