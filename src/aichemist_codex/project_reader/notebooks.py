"""Jupyter notebook processing for project_reader."""

import json
import logging
from pathlib import Path


class NotebookConverter:
    @staticmethod
    def to_script(file_path: Path) -> str:
        """Convert a Jupyter Notebook (.ipynb) into a Python script format."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                nb = json.load(f)

            code_cells = [
                "".join(cell.get("source", ""))  # Ensure source exists
                for cell in nb.get("cells", [])
                if cell.get("cell_type") == "code"
            ]
            return "\n\n# Cell\n".join(code_cells)
        except Exception as e:
            logging.error(f"Error processing notebook {file_path}: {e}")
            return f"# Error processing notebook: {e}"


def convert_notebook(file_path: Path) -> str:
    """
    Extract code cells from a Jupyter notebook (.ipynb).
    Handles both list and string formats for cell 'source'.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        code_cells = []
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                source = cell.get("source", "")
                if isinstance(source, list):
                    code_cells.append("".join(source))
                elif isinstance(source, str):
                    code_cells.append(source)
        return "\n".join(code_cells)
    except Exception as e:
        logging.error(f"Error processing notebook {file_path}: {e}")
        return f"# Error processing notebook: {e}"
