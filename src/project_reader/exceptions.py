from pathlib import Path


class CodexError(Exception):
    """Base exception for project_reader errors."""

    pass


class MaxTokenError(CodexError):
    def __init__(self, file_path: Path, max_tokens: int):
        super().__init__(f"{file_path} exceeds {max_tokens} token limit")


class NotebookProcessingError(CodexError):
    def __init__(self, file_path: Path):
        super().__init__(f"Failed to process notebook: {file_path}")
