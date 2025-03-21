"""
Change detector for comparing files and detecting differences.

This module provides functionality for detecting changes between file versions
or content.
"""

import difflib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ChangeDetector:
    """
    Detects changes between file contents.

    This class provides methods for comparing file contents and identifying
    changes such as line additions, removals, and modifications.
    """

    def detect_changes(
        self, current_content: str, reference_content: str
    ) -> dict[str, Any]:
        """
        Detect changes between current content and a reference.

        Args:
            current_content: Current file content
            reference_content: Reference content to compare against

        Returns:
            Dictionary containing changes and statistics
        """
        # Split the content into lines
        current_lines = current_content.splitlines()
        reference_lines = reference_content.splitlines()

        # Compare lines
        diff = difflib.unified_diff(
            reference_lines,
            current_lines,
            lineterm="",
            n=3,  # Context lines
        )

        # Process the diff output
        changes = []
        # Explicitly type the stats dictionary to accept both int and float values
        stats: dict[str, int | float | bool] = {
            "additions": 0,
            "deletions": 0,
            "modifications": 0,
        }
        line_mapping = {}

        for line in diff:
            # Skip the header lines (start with ---, +++ or @@)
            if (
                line.startswith("---")
                or line.startswith("+++")
                or line.startswith("@@")
            ):
                # Extract line numbers from the @@ line
                if line.startswith("@@"):
                    try:
                        # Format is "@@ -start,count +start,count @@"
                        parts = line.split(" ")
                        old_range = parts[1]
                        new_range = parts[2]
                        old_start = int(old_range.split(",")[0][1:])
                        new_start = int(new_range.split(",")[0][1:])
                        line_mapping = {"old_start": old_start, "new_start": new_start}
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Error parsing diff header: {e}")
                continue

            # Process change lines
            if line.startswith("+"):
                changes.append(
                    {
                        "type": "addition",
                        "content": line[1:],
                        "line_number": line_mapping.get("new_start", 0),
                    }
                )
                line_mapping["new_start"] = line_mapping.get("new_start", 0) + 1
                stats["additions"] += 1
            elif line.startswith("-"):
                changes.append(
                    {
                        "type": "deletion",
                        "content": line[1:],
                        "line_number": line_mapping.get("old_start", 0),
                    }
                )
                line_mapping["old_start"] = line_mapping.get("old_start", 0) + 1
                stats["deletions"] += 1
            else:
                # Unchanged context line
                line_mapping["old_start"] = line_mapping.get("old_start", 0) + 1
                line_mapping["new_start"] = line_mapping.get("new_start", 0) + 1

        # Identify modifications by looking for pairs of additions and deletions at same position
        self._identify_modifications(changes, stats)

        # Calculate percentage of change
        total_lines = len(current_lines)
        if total_lines > 0:
            percent_changed = round(
                float(stats["additions"] + stats["deletions"] + stats["modifications"])
                / total_lines
                * 100,
                2,
            )
        else:
            percent_changed = 0

        stats["total_lines"] = total_lines
        stats["percent_changed"] = percent_changed
        stats["has_changed"] = percent_changed > 0

        return {"has_changes": len(changes) > 0, "changes": changes, "stats": stats}

    def _identify_modifications(
        self, changes: list[dict[str, Any]], stats: dict[str, int | float | bool]
    ) -> None:
        """
        Identify modifications in the changes list.

        This method looks for pairs of additions and deletions that are likely
        to be modifications of the same line.

        Args:
            changes: List of change dictionaries
            stats: Statistics dictionary to update
        """
        # Group changes by line number
        deletions_by_line = {}
        i = 0

        while i < len(changes):
            change = changes[i]
            if change["type"] == "deletion":
                line_num = change["line_number"]
                deletions_by_line[line_num] = i
            i += 1

        # Look for additions that match with deletions
        i = 0
        while i < len(changes):
            change = changes[i]
            if change["type"] == "addition":
                # Look for a deletion at the same line number or adjacent
                line_num = change["line_number"]

                # Check exact line match first
                if line_num in deletions_by_line:
                    deletion_idx = deletions_by_line[line_num]
                    deletion = changes[deletion_idx]

                    # Convert the deletion and addition to a modification
                    modification = {
                        "type": "modification",
                        "old_content": deletion["content"],
                        "new_content": change["content"],
                        "line_number": line_num,
                    }

                    # Replace the deletion with the modification and remove the addition
                    changes[deletion_idx] = modification
                    changes.pop(i)

                    # Update stats
                    stats["modifications"] += 1
                    stats["additions"] -= 1
                    stats["deletions"] -= 1

                    # Continue without incrementing i since we removed an element
                    continue

            i += 1
