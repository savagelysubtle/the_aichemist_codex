"""Handles CSV output for structured code summaries."""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_as_csv(output_file: Path, data: dict):
    """Saves extracted code summary as a CSV file."""
    try:
        with output_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["File", "Type", "Name", "Arguments", "Line Number"])

            for file, functions in data.items():
                for func in functions:
                    writer.writerow(
                        [
                            file,
                            func["type"],
                            func["name"],
                            ", ".join(func.get("args", [])),
                            func["lineno"],
                        ]
                    )

        logger.info(f"CSV summary saved: {output_file}")

    except Exception as e:
        logger.error(f"Error writing CSV output to {output_file}: {e}")
