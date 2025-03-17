# test_errors.py
import pytest

from the_aichemist_codex.backend.utils.errors import NotebookProcessingError


@pytest.mark.core
@pytest.mark.unit
def test_notebook_processing_error() -> None:
    with pytest.raises(NotebookProcessingError):
        raise NotebookProcessingError("Test error")
