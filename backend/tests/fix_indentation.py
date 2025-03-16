#!/usr/bin/env python
"""
Script to fix indentation and invalid markers in test files.

Run this script with a specific file path:
    python backend/tests/fix_indentation.py PATH_TO_FILE
"""

import re
import sys


def fix_file(file_path):
    """
    Fix indentation issues and invalid markers in the given file.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False

    # Fix invalid syntax like @pytest.mark.[a-z]+
    invalid_marker_pattern = r"@pytest\.mark\.\[a-z\]\+"
    if re.search(invalid_marker_pattern, content):
        content = re.sub(invalid_marker_pattern, "@pytest.mark.search", content)
        print(f"Fixed invalid marker pattern in {file_path}")

    # Fix indentation issues with markers
    lines = content.split("\n")
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for marker at current line
        if re.match(r"\s*@pytest\.mark\.[a-z]+\s*$", line):
            marker_match = re.match(r"(\s*)", line)
            marker_indent = marker_match.group(1) if marker_match else ""

            # Look ahead for next line
            next_line_idx = i + 1
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx]

                # If next line is also a marker, ensure same indentation
                if re.match(r"\s*@pytest\.mark\.[a-z]+\s*$", next_line):
                    next_match = re.match(r"(\s*)", next_line)
                    next_indent = next_match.group(1) if next_match else ""
                    if len(next_indent) != len(marker_indent):
                        lines[next_line_idx] = marker_indent + next_line.lstrip()
                        print(f"Fixed marker indentation at line {next_line_idx + 1}")

                # If next line is empty, remove it (common issue)
                elif not next_line.strip():
                    print(
                        f"Removing empty line after marker at line {next_line_idx + 1}"
                    )
                    i += 1  # Skip the empty line

                # If next line is a function definition, ensure proper indentation
                elif re.match(r"\s*(async\s+)?def\s+test_\w+", next_line):
                    # Function should have same indentation as marker
                    if not next_line.startswith(marker_indent):
                        lines[next_line_idx] = marker_indent + next_line.lstrip()
                        print(f"Fixed function indentation at line {next_line_idx + 1}")

        fixed_lines.append(line)
        i += 1

    # Merge the fixed lines
    fixed_content = "\n".join(fixed_lines)

    # Only write if changes were made
    if fixed_content != content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            print(f"Successfully fixed {file_path}")
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    print(f"No indentation issues found in {file_path}")
    return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python fix_indentation.py FILE_PATH")
        return 1

    file_path = sys.argv[1]
    fix_file(file_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
