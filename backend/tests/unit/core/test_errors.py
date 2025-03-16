# test_errors.py
import pytest

from backend.src.utils.errors import NotebookProcessingError


@pytest.mark.[a-z]+

@pytest.mark.unit
def test_notebook_processing_error() -> None:
    with pytest.raises(NotebookProcessingError):
        raise NotebookProcessingError("Test error")
