"""Handles Markdown output for summarizing extracted code metadata."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# Function to generate markdown output with fixes
def save_as_markdown(
    output_file: Path, data: dict, gpt_summaries=None, title="Project Code Summary"
):
    """Saves extracted code summary in an LLM-friendly Markdown format."""
    if gpt_summaries is None:
        gpt_summaries = {}  # Default to an empty dictionary

    with output_file.open("w", encoding="utf-8") as f:
        f.write(f"# 📖 {title}\n\n")
        f.write(
            "This document provides an AI-optimized summary of the project, including file organization, summaries, and function breakdowns.\n\n"
        )
        f.write("---\n\n")

        if not data:
            f.write(
                "No files were analyzed. Check for errors in `code_summary.json`.\n"
            )
            return

        folder_map = {}

        # Group files by folder
        for file, details in data.items():
            folder = details.get("folder", "Other")
            if folder not in folder_map:
                folder_map[folder] = []
            folder_map[folder].append((file, details))

        for folder, files in sorted(folder_map.items()):
            f.write(f"## 📂 Folder: `{folder}/`\n")
            for file, details in sorted(files):
                f.write(f"### 📄 `{file}`\n")
                f.write(
                    f"**Summary:** {details.get('summary', 'No summary available.')}\n\n"
                )

                if not details["functions"]:
                    f.write("**No functions detected in this file.**\n\n")
                else:
                    f.write(f"#### Functions in `{file}`:\n")
                    for func in details["functions"]:
                        func_name = func.get("name", "Unnamed Function")
                        func_args = (
                            ", ".join(func.get("args", []))
                            if func.get("args")
                            else "None"
                        )
                        func_lineno = func.get("lineno", "Unknown")
                        func_docstring = func.get("docstring", "No docstring provided.")

                        f.write(f"##### 🔹 `{func_name}({func_args})`\n")
                        f.write(f"- **Defined at:** Line {func_lineno}\n")
                        f.write(f"- **Docstring:** {func_docstring}\n\n")

                f.write("\n---\n\n")
