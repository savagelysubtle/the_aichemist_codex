# test_schemas.py
import pytest
from jsonschema import ValidationError, validate

from src.config.schemas import code_summary_schema, file_tree_schema


def test_file_tree_schema_valid():
    valid_data = {"folder": {"file.txt": {"size": 123, "type": "file"}}}
    validate(instance=valid_data, schema=file_tree_schema)


def test_file_tree_schema_invalid():
    invalid_data = {"folder": "not an object"}
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=file_tree_schema)


def test_code_summary_schema_valid():
    valid_data = {"module": [{"type": "function", "name": "func", "lineno": 10}]}
    validate(instance=valid_data, schema=code_summary_schema)


def test_code_summary_schema_invalid():
    invalid_data = {
        "module": [{"type": "function", "name": "func"}]
    }  # Missing 'lineno'
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=code_summary_schema)
