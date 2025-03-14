# test_errors.py
import pytest
from src.utils.errors import NotebookProcessingError


def test_notebook_processing_error():
    with pytest.raises(NotebookProcessingError):
        raise NotebookProcessingError("Test error")
