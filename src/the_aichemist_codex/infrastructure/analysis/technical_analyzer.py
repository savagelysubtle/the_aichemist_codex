"""
Technical Code Analysis Utilities

This module provides low-level functions for analyzing code content and structure,
operating primarily on basic types like strings, paths, and ASTs.
It is intended for internal use by services in the infrastructure or application layers.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any

from the_aichemist_codex.infrastructure.utils.io.async_io import AsyncFileIO

logger = logging.getLogger(__name__)


def calculate_python_complexity(tree: ast.AST) -> float:
    """
    Calculate complexity of Python code using AST.

    Args:
        tree: The AST of the Python code

    Returns:
        Complexity score
    """
    # Count functions and classes
    function_count = 0
    class_count = 0
    max_nesting = 0
    branch_count = 0

    # Helper function to track nesting depth
    def _track_nesting(node, current_depth):
        nonlocal max_nesting
        max_nesting = max(max_nesting, current_depth)
        for child in ast.iter_child_nodes(node):
            new_depth = current_depth
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                new_depth += 1
            _track_nesting(child, new_depth)

    # Count various syntax elements that contribute to complexity
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            function_count += 1
        elif isinstance(node, ast.ClassDef):
            class_count += 1
        elif isinstance(node, ast.If | ast.For | ast.While | ast.With):
            branch_count += 1
        elif isinstance(node, ast.Try):
            branch_count += (
                len(node.handlers)
                + (1 if node.orelse else 0)
                + (1 if node.finalbody else 0)
            )

    # Calculate max nesting depth
    _track_nesting(tree, 0)

    # Calculate complexity score
    complexity = (
        function_count * 0.5
        + class_count * 0.7
        + branch_count * 0.3
        + max_nesting * 1.0  # Added max_nesting contribution
    )

    return complexity


def calculate_basic_complexity(content: str | None) -> float:
    """
    Calculate basic complexity based on content.

    Args:
        content: The content to analyze

    Returns:
        Complexity score, or 0.0 if content is None
    """
    if not content:
        return 0.0

    # Count lines
    lines = content.split("\\n")
    line_count = len(lines)

    # Count logical elements that might indicate complexity
    control_flow_count = len(
        re.findall(r"\\b(if|else|for|while|switch|case|try|catch|finally)\\b", content)
    )
    function_count = len(re.findall(r"\\b(function|def|class|method)\\b", content))

    # Calculate complexity score
    complexity = line_count * 0.01 + control_flow_count * 0.3 + function_count * 0.5

    return complexity


def calculate_similarity(
    content1: str | None, content2: str | None, path1: Path, path2: Path
) -> float:
    """
    Calculate similarity between two code contents based on path and content.

    Args:
        content1: The content of the first file.
        content2: The content of the second file.
        path1: The path of the first file.
        path2: The path of the second file.

    Returns:
        Similarity score (0.0-1.0)
    """
    # This is a simple implementation for demonstration
    # A real implementation would use more sophisticated algorithms (e.g., Levenshtein, TF-IDF)

    if not content1 or not content2:
        return 0.0

    # Check if they're the same file type
    file_type_match = 0.0
    if path1.suffix.lower() == path2.suffix.lower():
        file_type_match = 0.2

    # Check name similarity
    name_similarity = 0.0
    if path1.name == path2.name:
        name_similarity = 0.3

    # Check content similarity (very basic Jaccard)
    content_similarity = 0.0
    lines1 = set(content1.split("\\n"))
    lines2 = set(content2.split("\\n"))

    # Jaccard similarity of lines
    if lines1 and lines2:
        intersection = len(lines1.intersection(lines2))
        union = len(lines1.union(lines2))
        if union > 0:
            content_similarity = (
                intersection / union * 0.5
            )  # Weighted less than path/name

    return file_type_match + name_similarity + content_similarity


def extract_comments(content: str | None) -> list[dict[str, Any]]:
    """
    Extract comments from code content.

    Args:
        content: The code content

    Returns:
        List of knowledge items from comments
    """
    if not content:
        return []

    knowledge_items = []

    # Extract comments (simplified)
    # This is a very basic implementation that would be enhanced in a real system
    comment_patterns = [
        (r"#\\s*(.*?)$", "python"),  # Python
        (r"//\\s*(.*?)$", "c-style"),  # C-style
        (r"/\\*(.*?)\\*/", "block"),  # Block comments
    ]

    for pattern, comment_type in comment_patterns:
        comments = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for i, comment in enumerate(comments):
            if len(comment.strip()) > 10:  # Ignore very short comments
                knowledge_items.append(
                    {
                        "type": f"{comment_type}_comment",
                        "content": comment.strip(),
                        "importance": 0.5,
                        "index": i,  # Add index for potential ordering/location use
                    }
                )

    return knowledge_items


def _get_python_structure(content: str) -> dict[str, list[dict[str, Any]]]:
    """
    Extract structure (classes, functions, variables) from Python code content using AST.

    Args:
        content: The Python code content as a string.

    Returns:
        A dictionary containing lists of classes, functions, and variables found.
        Returns empty lists if parsing fails.
    """
    structure = {"classes": [], "functions": [], "variables": []}
    try:
        tree = ast.parse(content)

        # Extract classes
        for node in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            methods = []
            # Extract methods within the class
            # Ensure we only look at direct children that are FunctionDef or AsyncFunctionDef
            for method in [
                m
                for m in node.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]:
                methods.append(
                    {
                        "name": method.name,
                        "line": method.lineno,
                        "docstring": ast.get_docstring(method) or "",
                        "args": [arg.arg for arg in method.args.args],
                        # Consider adding decorators, return types if needed
                    }
                )

            structure["classes"].append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                    "methods": methods,
                    # Consider adding base classes, decorators if needed
                }
            )

        # Extract top-level functions (direct children of the module)
        for node in [
            n
            for n in tree.body  # Use tree.body for top-level nodes
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]:
            structure["functions"].append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                    "args": [arg.arg for arg in node.args.args],
                    # Consider adding decorators, return types if needed
                }
            )

        # Extract top-level variables (assignments at module level)
        for node in [n for n in tree.body if isinstance(n, ast.Assign)]:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    structure["variables"].append(
                        {"name": target.id, "line": node.lineno}
                        # Consider adding type hints or assigned value preview if useful
                    )
                # Handle tuple unpacking assignment if necessary
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            structure["variables"].append(
                                {"name": elt.id, "line": node.lineno}
                            )

    except SyntaxError as e:
        logger.warning(f"Syntax error parsing content for structure: {e}")
        # Return empty structure on syntax error
    except Exception as e:
        logger.error(f"Unexpected error parsing content for structure: {e}")
        # Return empty structure on other errors

    return structure


def assess_complexity(complexity: float) -> str:
    """
    Assess the complexity score and return a descriptive string.

    Args:
        complexity: The complexity score

    Returns:
        Assessment description (e.g., "Low complexity", "High complexity")
    """
    if complexity < 5:
        return "Low complexity"
    elif complexity < 15:
        return "Moderate complexity"
    elif complexity < 30:
        return "High complexity"
    else:
        return "Very high complexity"


async def process_file(file_path: Path) -> tuple[str, dict[str, Any]]:
    """
    Extracts summary, functions, and class details from a Python file using AST.

    Args:
        file_path: Path object for the file to process.

    Returns:
        Tuple containing the resolved file path (as string) and a dictionary
        with file analysis data ('summary', 'folder', 'functions', 'classes',
        'line_count', 'file_type'). Returns error info in the dictionary
        if processing fails.
    """
    resolved_path_str = file_path.resolve().as_posix()
    try:
        # Read file contents using the project's AsyncFileIO utility
        code = await AsyncFileIO.read_text(file_path)

        # Check if reading the file encountered an error
        if code.startswith("# Error") or code.startswith("# Encoding"):
            logger.error(f"Error reading {resolved_path_str}: {code}")
            return resolved_path_str, {
                "summary": code,  # Return the error message as summary
                "folder": file_path.parent.name,
                "functions": [],
                "classes": [],
                "line_count": 0,
                "file_type": file_path.suffix,
                "error": True,
            }

        # Parse the AST
        tree = ast.parse(code, filename=str(file_path))

        # Get the module docstring (summary)
        file_summary = ast.get_docstring(tree) or "No summary available."

        # Extract structure using the helper function
        structure = _get_python_structure(code)

        # Format functions and classes from structure for output consistency
        functions_out = [
            {
                "name": f["name"],
                "args": f["args"],
                "lineno": f["lineno"],
                "docstring": f["docstring"],
            }
            for f in structure["functions"]
        ]

        classes_out = []
        for c in structure["classes"]:
            methods_out = [
                {
                    "name": m["name"],
                    "args": m["args"],
                    "lineno": m["lineno"],
                    "docstring": m["docstring"],
                }
                for m in c["methods"]
            ]
            classes_out.append(
                {
                    "name": c["name"],
                    "lineno": c["lineno"],
                    "docstring": c["docstring"],
                    "methods": methods_out,
                    "properties": [],  # Keep properties list for schema consistency if needed later
                }
            )

        # Create a summary of the file
        file_data = {
            "summary": file_summary,
            "folder": file_path.parent.name,
            "functions": functions_out,
            "classes": classes_out,
            "line_count": len(code.splitlines()),
            "file_type": file_path.suffix,
            "error": False,
        }

        return resolved_path_str, file_data

    except SyntaxError as e:
        logger.error(f"Syntax error in {resolved_path_str}: {e}")
        return resolved_path_str, {
            "summary": f"Syntax error: {e!s}",
            "folder": file_path.parent.name,
            "functions": [],
            "classes": [],
            "line_count": 0,  # Content might be partially read or unreadable
            "file_type": file_path.suffix,
            "error": True,
        }
    except Exception as e:
        # Catch other potential errors during processing (e.g., AST walking)
        logger.error(f"Error processing {resolved_path_str}: {e}")
        return resolved_path_str, {
            "summary": f"Processing error: {e!s}",
            "folder": file_path.parent.name,
            "functions": [],
            "classes": [],
            "line_count": 0,  # Assume analysis is incomplete
            "file_type": file_path.suffix,
            "error": True,
        }
