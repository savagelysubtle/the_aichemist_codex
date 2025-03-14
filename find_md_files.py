import os
import re
import sys


def find_md_files(directory):
    """Find all Markdown files in the given directory."""
    pattern = re.compile(r"\.md$")
    md_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if pattern.search(file):
                md_files.append(os.path.join(root, file))

    return md_files


if __name__ == "__main__":
    directory = "."
    if len(sys.argv) > 1:
        directory = sys.argv[1]

    md_files = find_md_files(directory)
    print(f"Found {len(md_files)} Markdown files:")
    for file in md_files:
        print(file)
