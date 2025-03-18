import logging
import os
from typing import Any

from ....core.exceptions import ExtractorError
from ..extractor import Extractor

logger = logging.getLogger(__name__)


class CodeExtractor(Extractor):
    """Extractor for source code files."""

    def __init__(self):
        super().__init__()
        # Code file extensions
        self._supported_extensions = {
            # Python
            ".py",
            ".pyx",
            ".pyi",
            ".ipynb",
            # Web
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".less",
            # Java/JVM
            ".java",
            ".kt",
            ".groovy",
            ".scala",
            # C-family
            ".c",
            ".cpp",
            ".cc",
            ".h",
            ".hpp",
            ".cs",
            ".m",
            ".mm",
            # Go
            ".go",
            # Rust
            ".rs",
            # Ruby
            ".rb",
            # PHP
            ".php",
            # C#
            # Swift
            ".swift",
            # Shell
            ".sh",
            ".bash",
            ".zsh",
            ".ps1",
            ".bat",
            ".cmd",
            # Others
            ".pl",
            ".pm",
            ".lua",
            ".r",
            ".d",
            ".dart",
        }

        self._supported_mime_types = {
            "text/x-python",
            "application/x-python-code",
            "application/javascript",
            "text/javascript",
            "text/typescript",
            "text/html",
            "text/css",
            "text/x-java",
            "text/x-c",
            "text/x-c++",
            "text/x-csharp",
        }

        # Language patterns
        self._language_patterns = {
            "python": {
                "extensions": [".py", ".pyx", ".pyi"],
                "import_patterns": [
                    r"^import\s+([a-zA-Z0-9_.]+)",
                    r"^from\s+([a-zA-Z0-9_.]+)\s+import",
                ],
                "class_patterns": [r"^class\s+([a-zA-Z0-9_]+)"],
                "function_patterns": [r"^def\s+([a-zA-Z0-9_]+)"],
            },
            "javascript": {
                "extensions": [".js", ".jsx"],
                "import_patterns": [
                    r"import\s+.*?from\s+['\"]([^'\"]+)['\"]",
                    r"require\(['\"]([^'\"]+)['\"]",
                ],
                "class_patterns": [
                    r"class\s+([a-zA-Z0-9_]+)",
                ],
                "function_patterns": [
                    r"function\s+([a-zA-Z0-9_]+)",
                    r"const\s+([a-zA-Z0-9_]+)\s*=\s*\([^)]*\)\s*=>",
                ],
            },
            "typescript": {
                "extensions": [".ts", ".tsx"],
                "import_patterns": [
                    r"import\s+.*?from\s+['\"]([^'\"]+)['\"]",
                ],
                "class_patterns": [
                    r"class\s+([a-zA-Z0-9_]+)",
                    r"interface\s+([a-zA-Z0-9_]+)",
                ],
                "function_patterns": [
                    r"function\s+([a-zA-Z0-9_]+)",
                    r"const\s+([a-zA-Z0-9_]+)\s*=\s*\([^)]*\)\s*=>",
                ],
            },
            "java": {
                "extensions": [".java"],
                "import_patterns": [
                    r"import\s+([a-zA-Z0-9_.]+);",
                ],
                "class_patterns": [
                    r"class\s+([a-zA-Z0-9_]+)",
                    r"interface\s+([a-zA-Z0-9_]+)",
                    r"enum\s+([a-zA-Z0-9_]+)",
                ],
                "function_patterns": [
                    r"(?:public|private|protected|static)?\s+(?:[a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)\s*\(",
                ],
            },
            "c": {
                "extensions": [".c", ".h"],
                "import_patterns": [
                    r"#include\s+[<\"]([^>\"]+)[>\"]",
                ],
                "function_patterns": [
                    r"([a-zA-Z0-9_]+)\s*\([^)]*\)\s*{",
                ],
            },
            "cpp": {
                "extensions": [".cpp", ".hpp", ".cc", ".h"],
                "import_patterns": [
                    r"#include\s+[<\"]([^>\"]+)[>\"]",
                ],
                "class_patterns": [
                    r"class\s+([a-zA-Z0-9_]+)",
                    r"struct\s+([a-zA-Z0-9_]+)",
                ],
                "function_patterns": [
                    r"([a-zA-Z0-9_]+)::[a-zA-Z0-9_]+\s*\(",
                    r"(?:void|int|char|float|double|bool|auto)\s+([a-zA-Z0-9_]+)\s*\(",
                ],
            },
            "go": {
                "extensions": [".go"],
                "import_patterns": [
                    r"import\s+[(\"]([^)\"]+)[\")]",
                ],
                "function_patterns": [
                    r"func\s+([a-zA-Z0-9_]+)\s*\(",
                ],
                "class_patterns": [
                    r"type\s+([a-zA-Z0-9_]+)\s+struct",
                    r"type\s+([a-zA-Z0-9_]+)\s+interface",
                ],
            },
        }

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from a code file.

        Args:
            file_path: Path to the code file

        Returns:
            Dictionary containing metadata

        Raises:
            ExtractorError: If metadata extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            # Basic file info
            stat_info = os.stat(file_path)
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # Determine language from extension
            language = self._get_language_from_extension(ext)

            metadata = {
                "file_type": "code",
                "language": language,
                "extension": ext,
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
            }

            # Read file content for enhanced metadata
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Get line and character count
                lines = content.splitlines()
                metadata["line_count"] = len(lines)
                metadata["char_count"] = len(content)

                # Extract imports, classes, and functions
                imports, classes, functions = self._extract_code_elements(
                    content, language
                )

                if imports:
                    metadata["imports"] = imports
                if classes:
                    metadata["classes"] = classes
                if functions:
                    metadata["functions"] = functions

                # Check for license headers or
            except Exception as e:
                logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
                raise ExtractorError(
                    f"Failed to extract metadata from {file_path}: {str(e)}"
                ) from e

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e
