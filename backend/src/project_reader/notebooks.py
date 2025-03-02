"""Jupyter notebook processing for project_reader."""

import json
import logging
from pathlib import Path

from src.utils import AsyncFileIO
from src.utils.errors import NotebookProcessingError

logger = logging.getLogger(__name__)


class NotebookConverter:
    """Convert Jupyter notebooks to Python scripts and extract metadata."""

    @staticmethod
    async def to_script_async(notebook_path: Path) -> str:
        """Convert notebook to Python script asynchronously."""
        try:
            # Use AsyncFileIO to read the notebook file
            notebook_content = await AsyncFileIO.read(notebook_path)
            if notebook_content.startswith("# "):  # Error message or skipped file
                raise NotebookProcessingError(
                    f"Error reading notebook: {notebook_content}"
                )

            notebook_dict = json.loads(notebook_content)

            # Extract only code cells
            code_cells = []
            for cell in notebook_dict.get("cells", []):
                if cell.get("cell_type") == "code":
                    source = cell.get("source", "")
                    if isinstance(source, list):
                        code_cells.append("".join(source))
                    elif isinstance(source, str):
                        code_cells.append(source)

            return "\n\n".join(code_cells)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid notebook format in {notebook_path}: {e}"
            logger.error(error_msg)
            raise NotebookProcessingError(error_msg) from e
        except Exception as e:
            error_msg = f"Error processing notebook {notebook_path}: {e}"
            logger.error(error_msg)
            raise NotebookProcessingError(error_msg) from e

    @staticmethod
    def to_script(notebook_path: Path) -> str:
        """Convert notebook to Python script (synchronous wrapper)."""
        import asyncio

        try:
            return asyncio.run(NotebookConverter.to_script_async(notebook_path))
        except NotebookProcessingError as e:
            logger.error(f"Error in to_script: {e}")
            return f"# Error processing notebook: {e}"
        except Exception as e:
            logger.error(f"Unexpected error in to_script: {e}")
            return f"# Unexpected error processing notebook: {e}"
