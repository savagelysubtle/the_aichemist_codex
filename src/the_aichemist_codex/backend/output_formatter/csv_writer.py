import csv
import io
import logging
from pathlib import Path

from the_aichemist_codex.backend.utils.async_io import AsyncFileIO  # Adjust import as needed

logger = logging.getLogger(__name__)


async def save_as_csv(output_file: Path, data: dict) -> bool:
    """Asynchronously saves extracted code summary as a CSV file."""
    try:
        # Create CSV content in memory using StringIO.
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
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
        csv_content = csv_buffer.getvalue()

        # Write CSV content asynchronously.
        success = await AsyncFileIO.write(output_file, csv_content)
        if success:
            logger.info(f"CSV summary saved: {output_file}")
        else:
            logger.error(f"Error writing CSV output to {output_file}")
        return success

    except Exception as e:
        logger.error(f"Error writing CSV output to {output_file}: {e}")
        return False
