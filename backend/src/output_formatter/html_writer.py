import logging
from pathlib import Path

from utils.async_io import AsyncFileIO  # Adjust import as needed

logger = logging.getLogger(__name__)


async def save_as_html(
    output_file: Path, data: dict, title="Project Code Summary"
) -> bool:
    """Asynchronously saves extracted code summary as an HTML report."""
    try:
        html_content = f"<html><head><title>{title}</title></head><body>"
        html_content += f"<h1>{title}</h1>"

        for file, functions in data.items():
            if not functions:
                continue
            html_content += f"<h2>{file}</h2>"
            # If a summary exists in data for the file, include it; otherwise a default message.
            html_content += (
                f"<p><b>Summary:</b> {data.get(file, 'No summary available.')}</p>"
            )
            html_content += "<ul>"
            for func in functions:
                html_content += f"<li><b>{func['type'].capitalize()}</b>: {func['name']} (Line {func['lineno']})"
                if func.get("args"):
                    html_content += f" | Arguments: {', '.join(func['args'])}"
                html_content += "</li>"
            html_content += "</ul>"

        html_content += "</body></html>"

        success = await AsyncFileIO.write(output_file, html_content)
        if success:
            logger.info(f"HTML summary saved: {output_file}")
        else:
            logger.error(f"Error writing HTML output to {output_file}")
        return success

    except Exception as e:
        logger.error(f"Error writing HTML output to {output_file}: {e}")
        return False
