import logging
import os
import shutil


def apply_rules(source_dir, rules):
    """Applies file organization rules to newly created files."""
    for rule in rules:
        target_dir = rule.get("target_dir")
        extensions = rule.get("extensions", [])

        if not target_dir or not extensions:
            continue

        for file in os.listdir(source_dir):
            if any(file.endswith(ext) for ext in extensions):
                source_path = os.path.join(source_dir, file)
                target_path = os.path.join(target_dir, file)

                try:
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(source_path, target_path)
                    logging.info(f"Moved {file} -> {target_dir}")
                except Exception as e:
                    logging.error(f"Failed to move {file}: {e}")
