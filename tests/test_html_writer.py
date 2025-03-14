# test_html_writer.py
from backend.output_formatter.html_writer import save_as_html


def test_html_writer(tmp_path):
    data = "<h1>Test</h1><p>Content</p>"
    output_file = tmp_path / "output.html"
    save_as_html(data, output_file)
    content = output_file.read_text(encoding="utf-8")
    assert "<h1>Test</h1>" in content
