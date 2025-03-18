import re
from typing import Any


class CodeContentProcessor:
    def _detect_language(self, content: IngestContent) -> str:
        """
        Detect the programming language from file extension and content.

        Args:
            content: The content to analyze

        Returns:
            Detected language or "unknown"
        """
        # First try to detect from filename
        if content.filename:
            extension = content.filename.split(".")[-1].lower()

            extension_map = {
                "py": "python",
                "js": "javascript",
                "ts": "javascript",
                "jsx": "javascript",
                "tsx": "javascript",
                "java": "java",
                "c": "c",
                "cpp": "cpp",
                "cs": "csharp",
                "go": "go",
                "rb": "ruby",
                "php": "php",
                "swift": "swift",
                "kt": "kotlin",
                "rs": "rust",
            }

            if extension in extension_map:
                return extension_map[extension]

        # Try to detect from content
        if content.is_binary:
            return "unknown"

        text = content.text_content

        # Look for language indicators in the content
        if "def " in text and "import " in text and ":" in text:
            return "python"
        elif "function " in text and (
            "const " in text or "let " in text or "var " in text
        ):
            return "javascript"
        elif "public class " in text or "private class " in text:
            return "java"
        elif "#include" in text and ("{" in text and "}" in text):
            return "c" if ".h>" in text else "cpp"

        # Default to unknown
        return "unknown"

    def _analyze_complexity(self, code: str, language: str) -> dict[str, Any]:
        """
        Analyze code complexity.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Complexity metrics
        """
        # Initialize complexity metrics
        complexity = {
            "cyclomatic_complexity": 0,
            "nesting_depth": 0,
            "line_complexity": {},
        }

        # Simple cyclomatic complexity estimate based on control flow statements
        if language == "python":
            control_flow = ["if", "elif", "for", "while", "except"]
        elif language in ["javascript", "java"]:
            control_flow = ["if", "for", "while", "switch", "catch", "?"]
        else:
            control_flow = ["if", "for", "while"]

        lines = code.splitlines()
        current_nesting = 0
        max_nesting = 0

        for i, line in enumerate(lines):
            line_complexity = 0

            # Count control flow statements in this line
            for statement in control_flow:
                # Use word boundaries to avoid matching substrings
                pattern = r"\b" + re.escape(statement) + r"\b"
                matches = re.findall(pattern, line)
                line_complexity += len(matches)

            if line_complexity > 0:
                complexity["cyclomatic_complexity"] += line_complexity
                complexity["line_complexity"][i + 1] = line_complexity

            # Estimate nesting depth based on indentation
            if language == "python":
                # In Python, nesting is determined by indentation
                indent = len(line) - len(line.lstrip())
                current_nesting = indent // 4  # Assuming 4 spaces per indent
            else:
                # In other languages, track braces
                current_nesting += line.count("{") - line.count("}")

            max_nesting = max(max_nesting, current_nesting)

        complexity["nesting_depth"] = max_nesting

        return complexity

    def _ensure_initialized(self) -> None:
        """
        Ensure that the processor is initialized.

        Raises:
            RuntimeError: If not initialized
        """
        if not self._is_initialized:
            raise RuntimeError("Code content processor is not initialized")
