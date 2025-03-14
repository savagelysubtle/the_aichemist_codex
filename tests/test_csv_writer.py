# test_csv_writer.py
import csv

from backend.src.output_formatter.csv_writer import save_as_csv


def test_csv_writer(tmp_path):
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ]
    output_file = tmp_path / "output.csv"
    save_as_csv(data, output_file)

    with open(output_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows[0]["name"] == "Alice"
    # CSV reader returns all values as strings.
    assert rows[1]["age"] == "25"
