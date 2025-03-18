"""
Project reader implementation for analyzing and summarizing code.

This module provides functionality for reading code projects, extracting
information about structure, functions, and converting notebooks to scripts.
"""

import ast
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import tiktoken

from the_aichemist_codex.backend.core.exceptions import FileError, ProjectReaderError
from the_aichemist_codex.backend.core.interfaces import ProjectReader
from the_aichemist_codex.backend.services.file_system import FileSystemService
from the_aichemist_codex.backend.utils.async_helpers import AsyncFileReader

logger = logging.getLogger(__name__)


class ProjectReaderImpl(ProjectReader):
    """Implementation of the ProjectReader interface."""

    def __init__(self, file_system_service: FileSystemService | None = None):
        """
        Initialize the ProjectReader.

        Args:
            file_system_service: Optional FileSystemService for file operations.
                If not provided, a new instance will be created.
        """
        self.file_system_service = file_system_service or FileSystemService()
        self.token_analyzer = TokenAnalyzer()
        self.notebook_converter = NotebookConverter(self.file_system_service)
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the project reader.

        Raises:
            ProjectReaderError: If initialization fails.
        """
        try:
            if not self._initialized:
                # Initialize any resources needed
                self._initialized = True
                logger.info("ProjectReader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ProjectReader: {e}")
            raise ProjectReaderError(f"Failed to initialize ProjectReader: {e}")

    async def close(self) -> None:
        """Close any resources used by the project reader."""
        self._initialized = False
        logger.info("ProjectReader closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def summarize_project(
        self,
        directory: Path,
        output_markdown: Path | None = None,
        output_json: Path | None = None,
    ) -> dict[str, Any]:
        """
        Generate a summary of the project in the specified directory.

        Args:
            directory: Path to the project directory.
            output_markdown: Optional path to save the summary as markdown.
            output_json: Optional path to save the summary as JSON.

        Returns:
            A dictionary containing the project summary.

        Raises:
            ProjectReaderError: If summarization fails.
            FileError: If the directory cannot be read.
        """
        try:
            if not self._initialized:
                await self.initialize()

            directory = Path(directory).resolve()
            if not directory.exists() or not directory.is_dir():
                raise FileError(
                    f"Directory does not exist or is not readable: {directory}"
                )

            # Collect and process Python files
            summary = await self._analyze_project_code(directory)

            # Save output if paths are provided
            if output_markdown:
                await self._save_as_markdown(output_markdown, summary)

            if output_json:
                await self._save_as_json(output_json, summary)

            return summary
        except FileError as e:
            logger.error(f"File error during project summarization: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to summarize project: {e}")
            raise ProjectReaderError(
                f"Failed to summarize project: {e}", str(directory)
            )

    async def _analyze_project_code(self, directory: Path) -> dict[str, Any]:
        """
        Analyze Python code in the project directory.

        Args:
            directory: Path to the project directory.

        Returns:
            Dictionary mapping file paths to their summaries.
        """
        # Get all Python files, filtering ignored files
        python_files = []
        for path in await self.file_system_service.glob(directory, "**/*.py"):
            if await self.file_system_service.should_ignore(path):
                continue
            python_files.append(path)

        if not python_files:
            logger.warning(
                f"No Python files found in {directory} after filtering ignored paths."
            )
            return {}

        # Process each file and collect results
        tasks = [self._process_file(file) for file in python_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter valid results
        valid_results = {}
        for res in results:
            if isinstance(res, tuple) and len(res) == 2:
                valid_results[res[0]] = res[1]
            else:
                logging.error(f"Invalid result from _process_file(): {res}")

        return valid_results

    async def _process_file(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """
        Extract information from a Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (file path, file summary dictionary)
        """
        try:
            code = await AsyncFileReader.read_text(file_path)
            tree = ast.parse(code, filename=str(file_path))

            file_summary = ast.get_docstring(tree) or "No summary available."
            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node) or "No docstring provided."
                    functions.append(
                        {
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "lineno": node.lineno,
                            "docstring": docstring,
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or "No docstring provided."
                    methods = []

                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            method_docstring = (
                                ast.get_docstring(child) or "No docstring provided."
                            )
                            methods.append(
                                {
                                    "name": child.name,
                                    "args": [arg.arg for arg in child.args.args],
                                    "lineno": child.lineno,
                                    "docstring": method_docstring,
                                }
                            )

                    classes.append(
                        {
                            "name": node.name,
                            "lineno": node.lineno,
                            "docstring": docstring,
                            "methods": methods,
                        }
                    )

            return file_path.resolve().as_posix(), {
                "summary": file_summary,
                "folder": file_path.parent.name,
                "functions": functions,
                "classes": classes,
            }

        except SyntaxError as e:
            logging.error(f"Syntax error in {file_path}: {e}")
            return file_path.resolve().as_posix(), {
                "summary": f"Syntax error: {e}",
                "folder": file_path.parent.name,
                "functions": [],
                "classes": [],
            }
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            return file_path.resolve().as_posix(), {
                "summary": f"Processing error: {e}",
                "folder": file_path.parent.name,
                "functions": [],
                "classes": [],
            }

    async def _save_as_markdown(
        self, output_path: Path, summary: dict[str, Any]
    ) -> None:
        """
        Save the summary as markdown.

        Args:
            output_path: Path to save the markdown file.
            summary: Project summary dictionary.
        """
        try:
            markdown_content = ["# Project Code Summary\n"]

            for file_path, file_info in summary.items():
                markdown_content.append(f"## {file_path}\n")
                markdown_content.append(f"**Summary:** {file_info['summary']}\n")

                if file_info.get("functions"):
                    markdown_content.append("\n### Functions\n")
                    for func in file_info["functions"]:
                        markdown_content.append(f"#### {func['name']}\n")
                        markdown_content.append(
                            f"**Arguments:** {', '.join(func['args'])}\n"
                        )
                        markdown_content.append(f"**Line:** {func['lineno']}\n")
                        markdown_content.append(
                            f"**Docstring:** {func['docstring']}\n\n"
                        )

                if file_info.get("classes"):
                    markdown_content.append("\n### Classes\n")
                    for cls in file_info["classes"]:
                        markdown_content.append(f"#### {cls['name']}\n")
                        markdown_content.append(f"**Line:** {cls['lineno']}\n")
                        markdown_content.append(
                            f"**Docstring:** {cls['docstring']}\n\n"
                        )

                        if cls.get("methods"):
                            markdown_content.append("##### Methods\n")
                            for method in cls["methods"]:
                                markdown_content.append(f"###### {method['name']}\n")
                                markdown_content.append(
                                    f"**Arguments:** {', '.join(method['args'])}\n"
                                )
                                markdown_content.append(
                                    f"**Line:** {method['lineno']}\n"
                                )
                                markdown_content.append(
                                    f"**Docstring:** {method['docstring']}\n\n"
                                )

                markdown_content.append("\n---\n\n")

            await self.file_system_service.write_text(
                output_path, "\n".join(markdown_content)
            )
            logger.info(f"Markdown summary saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save markdown summary: {e}")
            raise ProjectReaderError(
                f"Failed to save markdown summary: {e}", str(output_path)
            )

    async def _save_as_json(self, output_path: Path, summary: dict[str, Any]) -> None:
        """
        Save the summary as JSON.

        Args:
            output_path: Path to save the JSON file.
            summary: Project summary dictionary.
        """
        try:
            await self.file_system_service.write_text(
                output_path, json.dumps(summary, indent=2)
            )
            logger.info(f"JSON summary saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON summary: {e}")
            raise ProjectReaderError(
                f"Failed to save JSON summary: {e}", str(output_path)
            )

    async def convert_notebook(
        self, notebook_path: Path, output_path: Path | None = None
    ) -> str:
        """
        Convert a Jupyter notebook to a Python script.

        Args:
            notebook_path: Path to the notebook file.
            output_path: Optional path to save the converted script.

        Returns:
            The converted Python script as a string.

        Raises:
            ProjectReaderError: If conversion fails.
            FileError: If the notebook file cannot be read.
        """
        try:
            if not self._initialized:
                await self.initialize()

            script = await self.notebook_converter.to_script_async(notebook_path)

            if output_path:
                await self.file_system_service.write_text(output_path, script)
                logger.info(f"Converted notebook saved to {output_path}")

            return script

        except FileError as e:
            logger.error(f"File error during notebook conversion: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to convert notebook: {e}")
            raise ProjectReaderError(
                f"Failed to convert notebook: {e}", str(notebook_path)
            )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in the given text.

        Args:
            text: The text to analyze.

        Returns:
            The estimated number of tokens.
        """
        return self.token_analyzer.estimate(text)


class TokenAnalyzer:
    """Analyzes text to estimate token counts for LLM processing."""

    def __init__(self):
        """Initialize the TokenAnalyzer with the cl100k_base encoding."""
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def estimate(self, text: str) -> int:
        """
        Estimate the number of tokens in the given text.

        Args:
            text: The text to analyze.

        Returns:
            The estimated number of tokens.
        """
        return len(self.encoder.encode(text))


class NotebookConverter:
    """Convert Jupyter notebooks to Python scripts and extract metadata."""

    def __init__(self, file_system_service: FileSystemService):
        """
        Initialize the NotebookConverter.

        Args:
            file_system_service: FileSystemService for file operations.
        """
        self.file_system_service = file_system_service

    async def to_script_async(self, notebook_path: Path) -> str:
        """
        Convert notebook to Python script asynchronously.

        Args:
            notebook_path: Path to the notebook file.

        Returns:
            The converted Python script as a string.

        Raises:
            ProjectReaderError: If conversion fails.
            FileError: If the notebook file cannot be read.
        """
        try:
            # Read the notebook file
            notebook_content = await self.file_system_service.read_text(notebook_path)
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
            raise ProjectReaderError(error_msg, str(notebook_path))
        except FileError as e:
            logger.error(f"File error during notebook conversion: {e}")
            raise
        except Exception as e:
            error_msg = f"Error processing notebook {notebook_path}: {e}"
            logger.error(error_msg)
            raise ProjectReaderError(error_msg, str(notebook_path))

    async def to_script(self, notebook_path: Path) -> str:
        """
        Convert notebook to Python script (synchronous wrapper).

        Args:
            notebook_path: Path to the notebook file.

        Returns:
            The converted Python script as a string.
        """
        try:
            return await self.to_script_async(notebook_path)
        except Exception as e:
            logger.error(f"Error in to_script: {e}")
            return f"# Error processing notebook: {e}"
