import logging
from pathlib import Path

from backend.utils.async_io import AsyncFileIO  # Adjust import as needed

logger = logging.getLogger(__name__)


async def save_as_markdown(
    output_file: Path, data: dict, gpt_summaries=None, title="Project Code Summary"
) -> bool:
    """Asynchronously saves extracted code summary in a Markdown format."""
    if gpt_summaries is None:
        gpt_summaries = {}

    try:
        markdown_content = f"# 📖 {title}\n\n"
        markdown_content += (
            "This document provides an AI-optimized summary of the project, including file organization, "
            "summaries, and function breakdowns.\n\n"
        )
        markdown_content += "---\n\n"

        if not data:
            markdown_content += (
                "No files were analyzed. Check for errors in `code_summary.json`.\n"
            )
        else:
            # Group files by folder.
            folder_map = {}
            for file, details in data.items():
                folder = details.get("folder", "Other")
                folder_map.setdefault(folder, []).append((file, details))

            for folder, files in sorted(folder_map.items()):
                markdown_content += f"## 📂 Folder: `{folder}/`\n"
                for file, details in sorted(files):
                    markdown_content += f"### 📄 `{file}`\n"
                    markdown_content += f"**Summary:** {details.get('summary', 'No summary available.')}\n\n"

                    if not details.get("functions"):
                        markdown_content += (
                            "**No functions detected in this file.**\n\n"
                        )
                    else:
                        markdown_content += f"#### Functions in `{file}`:\n"
                        for func in details["functions"]:
                            func_name = func.get("name", "Unnamed Function")
                            func_args = (
                                ", ".join(func.get("args", []))
                                if func.get("args")
                                else "None"
                            )
                            func_lineno = func.get("lineno", "Unknown")
                            func_docstring = func.get(
                                "docstring", "No docstring provided."
                            )
                            markdown_content += f"##### 🔹 `{func_name}({func_args})`\n"
                            markdown_content += (
                                f"- **Defined at:** Line {func_lineno}\n"
                            )
                            markdown_content += f"- **Docstring:** {func_docstring}\n\n"
                    markdown_content += "\n---\n\n"

        success = await AsyncFileIO.write(output_file, markdown_content)
        if success:
            logger.info(f"Markdown summary saved: {output_file}")
        else:
            logger.error(f"Error writing Markdown output to {output_file}")
        return success

    except Exception as e:
        logger.error(f"Error writing Markdown output to {output_file}: {e}")
        return False
