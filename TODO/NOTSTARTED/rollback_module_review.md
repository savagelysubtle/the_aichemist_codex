# Rollback Module Review

## 1. Current Implementation

### 1.1 Module Overview

The Rollback Module provides a version management system for files within the
AIChemist Codex. It enables automatic versioning, version restoration, and
management of file history, forming an essential part of the system's data
protection and change management capabilities.

### 1.2 Key Components

- **RollbackManagerImpl**: Core implementation class that manages file versions
- **Version**: Data model representing a versioned file with metadata
- **VersionScheduler**: Manages automatic versioning based on configurable
  policies
- **Database Schema**: (Implied but not directly visible in the provided code)
  For persistent storage of versions

### 1.3 Current Functionality

- File version creation and management
- Version restoration (rollback to previous versions)
- Automatic versioning based on configurable schedules
- Version tagging and metadata
- Configurable watched paths for auto-versioning
- Time-based version scheduling

## 2. Architectural Compliance

The rollback module demonstrates strong alignment with the architecture
guidelines:

| Architectural Principle | Status | Notes                                            |
| ----------------------- | ------ | ------------------------------------------------ |
| Layered Architecture    | ✅     | Properly positioned in the domain layer          |
| Registry Pattern        | ✅     | Uses registry for dependencies                   |
| Interface-Based Design  | ✅     | Implements RollbackManager interface             |
| Import Strategy         | ✅     | Follows project import guidelines                |
| Asynchronous Design     | ✅     | Uses async/await throughout                      |
| Error Handling          | ✅     | Uses specific RollbackError with context         |
| DI Principle            | ✅     | Receives dependencies via registry               |
| Modular Structure       | ✅     | Well-organized with clear separation of concerns |

## 3. Areas for Improvement

While the rollback module is well-structured and follows architectural
principles, several areas could benefit from enhancement:

| Area                     | Status | Notes                                                        |
| ------------------------ | ------ | ------------------------------------------------------------ |
| Storage Efficiency       | ⚠️     | No apparent optimization for storage space                   |
| Version Comparison       | ❌     | Lacks tools for comparing versions                           |
| Content-Based Versioning | ❌     | Versions based on time rather than content changes           |
| Selective Versioning     | ⚠️     | Limited filtering of what content gets versioned             |
| Version Pruning          | ❌     | No automatic cleanup of old versions                         |
| Differential Storage     | ❌     | Appears to store complete files rather than diffs            |
| Integration              | ⚠️     | Limited integration with other modules (e.g., notifications) |
| Batch Operations         | ❌     | No batch version operations support                          |

## 4. Recommendations

### 4.1 Differential Storage for Versions

Implement a space-efficient storage mechanism using file differentials:

```python
import difflib
from pathlib import Path
from typing import Dict, Any, Optional

class DiffVersion:
    """
    Version implementation that stores differences rather than full files.

    This class optimizes storage by keeping only the differences between versions
    instead of complete file copies.
    """

    def __init__(self, rollback_manager, version_store_path: Path):
        """Initialize the diff versioning system."""
        self._rollback_manager = rollback_manager
        self._version_store = version_store_path
        self._registry = rollback_manager._registry
        self._file_reader = self._registry.file_reader
        self._file_writer = self._registry.file_writer

    async def create_diff_version(
        self,
        file_path: Path,
        version_name: str,
        metadata: Dict[str, Any] = None,
        tags: list[str] = None
    ) -> str:
        """
        Create a differential version of a file.

        Args:
            file_path: Path to the file to version
            version_name: Name to identify this version
            metadata: Additional version metadata
            tags: Optional tags for the version

        Returns:
            The ID of the newly created version
        """
        # Ensure file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File to version does not exist: {file_path}")

        # Get file content
        current_content = await self._file_reader.read_text(str(file_path))

        # Get the most recent version to compare against
        base_content = ""
        base_version_id = None

        versions = await self._rollback_manager.get_file_versions(file_path, limit=1)
        if versions:
            # Get the content of the most recent version
            base_version_id = versions[0]["id"]
            base_version_path = Path(versions[0]["version_path"])
            if base_version_path.exists():
                base_content = await self._file_reader.read_text(str(base_version_path))

        # Only create a version if there are changes
        if not base_version_id or current_content != base_content:
            # Generate a diff
            diff = list(difflib.unified_diff(
                base_content.splitlines(True) if base_content else [],
                current_content.splitlines(True),
                fromfile=f"version_{base_version_id}" if base_version_id else "initial",
                tofile=f"version_{version_name}"
            ))

            # Check if we have meaningful changes (beyond metadata)
            if not diff:
                return base_version_id

            # Create a new version using the diff
            diff_text = "".join(diff)

            # Create metadata with reference to base version
            complete_metadata = metadata or {}
            if base_version_id:
                complete_metadata["base_version_id"] = base_version_id
                complete_metadata["storage_type"] = "differential"
            else:
                complete_metadata["storage_type"] = "full"

            # Store the diff or full content
            version_id = await self._rollback_manager.create_version(
                file_path,
                version_name=version_name,
                metadata=complete_metadata,
                tags=tags,
                content=diff_text if base_version_id else current_content
            )

            return version_id
        else:
            # No changes, return the existing version ID
            return base_version_id

    async def restore_from_diff_version(self, version_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Restore a file from a differential version.

        Args:
            version_id: ID of the version to restore
            output_path: Optional path to restore to (uses original path if None)

        Returns:
            Path to the restored file
        """
        # Get the version information
        version_info = await self._rollback_manager.get_version(version_id)
        if not version_info:
            raise ValueError(f"Version not found: {version_id}")

        original_path = Path(version_info["original_path"])
        version_path = Path(version_info["version_path"])

        # Determine if this is a differential version
        is_differential = version_info.get("metadata", {}).get("storage_type") == "differential"

        if not is_differential:
            # This is a full version, restore directly
            return await self._rollback_manager.restore_version(
                version_id, output_path=output_path
            )

        # This is a differential version, need to reconstruct
        base_version_id = version_info["metadata"].get("base_version_id")
        if not base_version_id:
            raise ValueError(f"Differential version missing base version: {version_id}")

        # Get the diff content
        diff_content = await self._file_reader.read_text(str(version_path))

        # Recursively restore the base version to a temporary file
        base_restored_path = await self.restore_from_diff_version(
            base_version_id,
            output_path=self._version_store / f"temp_base_{version_id}"
        )

        # Get base content
        base_content = await self._file_reader.read_text(str(base_restored_path))

        # Apply the diff to get the restored content
        # This is a simplified implementation - would need a proper patch function
        patched_content = self._apply_patch(base_content, diff_content)

        # Determine output path
        final_path = output_path if output_path else original_path

        # Write the restored content
        await self._file_writer.write_text(str(final_path), patched_content)

        # Cleanup temporary files
        if base_restored_path.name.startswith("temp_base_"):
            try:
                base_restored_path.unlink()
            except:
                pass

        return final_path

    def _apply_patch(self, base_content: str, diff_content: str) -> str:
        """
        Apply a unified diff to base content.

        Args:
            base_content: Original content
            diff_content: Unified diff to apply

        Returns:
            Patched content
        """
        # In a real implementation, you would use a proper patch library
        # This is a placeholder for the concept
        import patch
        return patch.apply_unified_diff(base_content, diff_content)
```

### 4.2 Version Comparison Tools

Implement tools for comparing different versions of files:

```python
import difflib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

class VersionComparer:
    """
    Provides tools for comparing file versions.

    This class implements various comparison methods for analyzing
    differences between versions.
    """

    def __init__(self, rollback_manager):
        """Initialize the version comparer."""
        self._rollback_manager = rollback_manager
        self._registry = rollback_manager._registry
        self._file_reader = self._registry.file_reader

    async def compare_versions(
        self,
        version_id1: str,
        version_id2: str,
        context_lines: int = 3,
        output_format: str = "unified"
    ) -> Dict[str, Any]:
        """
        Compare two versions and generate a diff.

        Args:
            version_id1: ID of the first version
            version_id2: ID of the second version
            context_lines: Number of context lines to include in the diff
            output_format: Format of diff output ("unified" or "html")

        Returns:
            Dictionary with comparison results
        """
        # Get version information
        v1_info = await self._rollback_manager.get_version(version_id1)
        v2_info = await self._rollback_manager.get_version(version_id2)

        if not v1_info or not v2_info:
            missing = version_id1 if not v1_info else version_id2
            raise ValueError(f"Version not found: {missing}")

        # Get version content
        v1_path = Path(v1_info["version_path"])
        v2_path = Path(v2_info["version_path"])

        v1_content = await self._file_reader.read_text(str(v1_path))
        v2_content = await self._file_reader.read_text(str(v2_path))

        # Generate the diff
        v1_lines = v1_content.splitlines(True)
        v2_lines = v2_content.splitlines(True)

        if output_format == "unified":
            diff = list(difflib.unified_diff(
                v1_lines,
                v2_lines,
                fromfile=f"Version {v1_info['version_name']}",
                tofile=f"Version {v2_info['version_name']}",
                n=context_lines
            ))
            diff_text = "".join(diff)
        elif output_format == "html":
            diff_html = difflib.HtmlDiff().make_file(
                v1_lines,
                v2_lines,
                f"Version {v1_info['version_name']}",
                f"Version {v2_info['version_name']}"
            )
            diff_text = diff_html
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        # Compute statistics about the diff
        changes = self._analyze_diff(v1_lines, v2_lines)

        return {
            "diff": diff_text,
            "format": output_format,
            "stats": {
                "lines_added": changes["added"],
                "lines_deleted": changes["deleted"],
                "lines_modified": changes["modified"],
                "total_changes": changes["added"] + changes["deleted"] + changes["modified"]
            },
            "version1": {
                "id": version_id1,
                "name": v1_info["version_name"],
                "timestamp": v1_info["timestamp"]
            },
            "version2": {
                "id": version_id2,
                "name": v2_info["version_name"],
                "timestamp": v2_info["timestamp"]
            }
        }

    async def find_version_with_line(
        self,
        file_path: Path,
        line_content: str,
        max_versions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find versions that contain a specific line.

        Args:
            file_path: Path of the file to search in versions
            line_content: Line content to search for
            max_versions: Maximum number of versions to check

        Returns:
            List of versions containing the line
        """
        # Get versions for the file
        versions = await self._rollback_manager.get_file_versions(
            file_path, limit=max_versions
        )

        matching_versions = []

        for version in versions:
            version_path = Path(version["version_path"])
            if version_path.exists():
                content = await self._file_reader.read_text(str(version_path))
                if line_content in content:
                    matching_versions.append({
                        "id": version["id"],
                        "name": version["version_name"],
                        "timestamp": version["timestamp"]
                    })

        return matching_versions

    def _analyze_diff(self, a_lines: List[str], b_lines: List[str]) -> Dict[str, int]:
        """
        Analyze differences between two sets of lines.

        Args:
            a_lines: Lines from first version
            b_lines: Lines from second version

        Returns:
            Dictionary with counts of added, deleted, and modified lines
        """
        # Use SequenceMatcher to get detailed operations
        matcher = difflib.SequenceMatcher(None, a_lines, b_lines)

        added = 0
        deleted = 0
        modified = 0

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'insert':
                added += (j2 - j1)
            elif op == 'delete':
                deleted += (i2 - i1)
            elif op == 'replace':
                # Count as modified (it's both a deletion and addition)
                modified += min(i2 - i1, j2 - j1)
                # If uneven, count remainder as added or deleted
                if (i2 - i1) > (j2 - j1):
                    deleted += (i2 - i1) - (j2 - j1)
                elif (j2 - j1) > (i2 - i1):
                    added += (j2 - j1) - (i2 - i1)

        return {
            "added": added,
            "deleted": deleted,
            "modified": modified
        }
```

### 4.3 Content-Based Versioning

Implement versioning that triggers based on content changes rather than just
time:

```python
class ContentVersioningPolicy:
    """
    Policy for content-based versioning.

    This class determines when to create versions based on the nature
    and significance of content changes.
    """

    def __init__(self, rollback_manager):
        """Initialize the content versioning policy."""
        self._rollback_manager = rollback_manager
        self._registry = rollback_manager._registry
        self._file_reader = self._registry.file_reader

        # Default thresholds
        self.min_change_percentage = 5.0  # Minimum change % to trigger version
        self.max_time_between_versions = 24 * 60 * 60  # 24 hours in seconds
        self.significant_change_words = [
            "BREAKING", "IMPORTANT", "FIX:", "SECURITY", "CRITICAL"
        ]

    async def should_create_version(
        self,
        file_path: Path,
        current_content: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Determine if a new version should be created based on content changes.

        Args:
            file_path: Path to the file
            current_content: Current file content (read from file if None)

        Returns:
            Tuple of (should_create_version, reason_data)
        """
        # Get current content if not provided
        if current_content is None:
            if not file_path.exists():
                return False, {"reason": "file_not_found"}
            current_content = await self._file_reader.read_text(str(file_path))

        # Get most recent version
        versions = await self._rollback_manager.get_file_versions(file_path, limit=1)

        # If no versions exist, always create one
        if not versions:
            return True, {"reason": "first_version"}

        recent_version = versions[0]
        recent_version_path = Path(recent_version["version_path"])

        # Check if recent version exists on disk
        if not recent_version_path.exists():
            return True, {"reason": "previous_version_missing"}

        # Check time-based threshold
        import time
        from datetime import datetime

        recent_time = datetime.fromisoformat(recent_version["timestamp"])
        current_time = datetime.now()
        time_diff = (current_time - recent_time).total_seconds()

        if time_diff > self.max_time_between_versions:
            return True, {"reason": "time_threshold_exceeded"}

        # Compare content
        recent_content = await self._file_reader.read_text(str(recent_version_path))

        # Quick check: if content unchanged, no version needed
        if current_content == recent_content:
            return False, {"reason": "content_unchanged"}

        # Calculate change percentage
        change_percentage = self._calculate_change_percentage(recent_content, current_content)

        if change_percentage >= self.min_change_percentage:
            return True, {
                "reason": "change_threshold_exceeded",
                "change_percentage": change_percentage
            }

        # Check for significant keywords
        if self._contains_significant_changes(recent_content, current_content):
            return True, {"reason": "significant_keywords"}

        # No version needed by default
        return False, {"reason": "insufficient_changes"}

    def _calculate_change_percentage(self, old_content: str, new_content: str) -> float:
        """
        Calculate the percentage of content that has changed.

        Args:
            old_content: Previous content
            new_content: Current content

        Returns:
            Percentage of changed content (0-100)
        """
        if not old_content:
            return 100.0

        # Use SequenceMatcher to compare
        matcher = difflib.SequenceMatcher(None, old_content, new_content)
        similarity = matcher.ratio()

        # Convert similarity to change percentage
        return (1 - similarity) * 100

    def _contains_significant_changes(self, old_content: str, new_content: str) -> bool:
        """
        Check if changes contain significant keywords.

        Args:
            old_content: Previous content
            new_content: Current content

        Returns:
            True if significant keywords are found in changes
        """
        # Get changed lines
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        # Find lines present in new but not in old
        added_lines = set(new_lines) - set(old_lines)

        # Check for significant words
        for line in added_lines:
            for word in self.significant_change_words:
                if word in line:
                    return True

        return False
```

### 4.4 Version Pruning System

Implement automatic cleanup of old or redundant versions:

```python
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

class VersionPruner:
    """
    System for automatically pruning old versions.

    This class implements different strategies for cleaning up versions
    to manage storage efficiently.
    """

    def __init__(self, rollback_manager):
        """Initialize the version pruner."""
        self._rollback_manager = rollback_manager
        self._registry = rollback_manager._registry

    async def prune_versions(
        self,
        strategy: str = "time_based",
        params: Dict[str, Any] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Prune versions according to the specified strategy.

        Args:
            strategy: Pruning strategy ("time_based", "count_based", or "hybrid")
            params: Strategy-specific parameters
            dry_run: If True, report but don't delete versions

        Returns:
            Dictionary with pruning results
        """
        if strategy == "time_based":
            return await self._prune_time_based(params or {}, dry_run)
        elif strategy == "count_based":
            return await self._prune_count_based(params or {}, dry_run)
        elif strategy == "hybrid":
            return await self._prune_hybrid(params or {}, dry_run)
        else:
            raise ValueError(f"Unsupported pruning strategy: {strategy}")

    async def _prune_time_based(
        self, params: Dict[str, Any], dry_run: bool
    ) -> Dict[str, Any]:
        """
        Prune versions based on age.

        Args:
            params: Time-based parameters
            dry_run: If True, report but don't delete

        Returns:
            Dictionary with pruning results
        """
        # Get parameters with defaults
        max_age_days = params.get("max_age_days", 90)
        keep_tagged = params.get("keep_tagged", True)
        exclude_tags = set(params.get("exclude_tags", ["important", "keep"]))

        # Get all versions
        all_versions = await self._get_all_versions()

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        # Find versions to prune
        to_prune = []

        for version in all_versions:
            # Skip if has excluded tag
            if keep_tagged and any(tag in exclude_tags for tag in version.get("tags", [])):
                continue

            # Check if older than cutoff
            version_date = datetime.fromisoformat(version["timestamp"])
            if version_date < cutoff_date:
                to_prune.append(version)

        # Delete versions if not dry run
        pruned_versions = []

        if not dry_run:
            for version in to_prune:
                try:
                    await self._rollback_manager.delete_version(version["id"])
                    pruned_versions.append(version["id"])
                except Exception as e:
                    logger.warning(f"Failed to prune version {version['id']}: {e}")

        return {
            "strategy": "time_based",
            "params": params,
            "versions_pruned": len(pruned_versions) if not dry_run else 0,
            "candidates": len(to_prune),
            "pruned_ids": pruned_versions if not dry_run else [],
            "dry_run": dry_run
        }

    async def _prune_count_based(
        self, params: Dict[str, Any], dry_run: bool
    ) -> Dict[str, Any]:
        """
        Prune versions to keep a maximum number per file.

        Args:
            params: Count-based parameters
            dry_run: If True, report but don't delete

        Returns:
            Dictionary with pruning results
        """
        # Get parameters with defaults
        max_versions_per_file = params.get("max_versions_per_file", 10)
        keep_tagged = params.get("keep_tagged", True)
        exclude_tags = set(params.get("exclude_tags", ["important", "keep"]))

        # Get all versions grouped by file
        file_versions = await self._get_versions_by_file()

        # Find versions to prune
        to_prune = []

        for file_path, versions in file_versions.items():
            # Sort by timestamp (newest first)
            sorted_versions = sorted(
                versions,
                key=lambda v: datetime.fromisoformat(v["timestamp"]),
                reverse=True
            )

            # Determine which to keep
            keep_count = 0
            for version in sorted_versions:
                # Always keep tagged versions if specified
                if keep_tagged and any(tag in exclude_tags for tag in version.get("tags", [])):
                    keep_count += 1
                    continue

                # Keep up to max_versions_per_file
                if keep_count < max_versions_per_file:
                    keep_count += 1
                    continue

                # Prune the rest
                to_prune.append(version)

        # Delete versions if not dry run
        pruned_versions = []

        if not dry_run:
            for version in to_prune:
                try:
                    await self._rollback_manager.delete_version(version["id"])
                    pruned_versions.append(version["id"])
                except Exception as e:
                    logger.warning(f"Failed to prune version {version['id']}: {e}")

        return {
            "strategy": "count_based",
            "params": params,
            "versions_pruned": len(pruned_versions) if not dry_run else 0,
            "candidates": len(to_prune),
            "pruned_ids": pruned_versions if not dry_run else [],
            "dry_run": dry_run
        }

    async def _prune_hybrid(
        self, params: Dict[str, Any], dry_run: bool
    ) -> Dict[str, Any]:
        """
        Hybrid pruning strategy combining time and count approaches.

        Args:
            params: Hybrid parameters
            dry_run: If True, report but don't delete

        Returns:
            Dictionary with pruning results
        """
        # Hybrid strategy: keep more recent versions, fewer older ones
        retention_policy = params.get("retention_policy", [
            {"age_days": 7, "keep": 10},    # Keep 10 versions within the last week
            {"age_days": 30, "keep": 5},    # Keep 5 versions from last week to last month
            {"age_days": 90, "keep": 2},    # Keep 2 versions from last month to 3 months
            {"age_days": 365, "keep": 1},   # Keep 1 version older than 3 months up to a year
        ])

        keep_tagged = params.get("keep_tagged", True)
        exclude_tags = set(params.get("exclude_tags", ["important", "keep"]))

        # Get versions by file
        file_versions = await self._get_versions_by_file()

        # Find versions to prune
        to_prune = []
        now = datetime.now()

        for file_path, versions in file_versions.items():
            # Sort by timestamp (newest first)
            sorted_versions = sorted(
                versions,
                key=lambda v: datetime.fromisoformat(v["timestamp"]),
                reverse=True
            )

            # Categorize versions by age
            categorized = {}
            for policy in retention_policy:
                age_days = policy["age_days"]
                cutoff = now - timedelta(days=age_days)
                categorized[age_days] = []

            # Special category for older than the oldest policy
            oldest_policy_days = max(p["age_days"] for p in retention_policy)
            categorized["older"] = []

            # Categorize each version
            for version in sorted_versions:
                # Skip tagged versions if configured
                if keep_tagged and any(tag in exclude_tags for tag in version.get("tags", [])):
                    continue

                version_date = datetime.fromisoformat(version["timestamp"])
                age_days = (now - version_date).days

                # Find appropriate category
                category = "older"
                for policy in sorted(retention_policy, key=lambda p: p["age_days"]):
                    if age_days <= policy["age_days"]:
                        category = policy["age_days"]
                        break

                categorized[category].append(version)

            # Determine which to prune
            for policy in retention_policy:
                category = policy["age_days"]
                keep_count = policy["keep"]
                if len(categorized[category]) > keep_count:
                    to_prune.extend(categorized[category][keep_count:])

            # Prune all in the "older" category
            to_prune.extend(categorized["older"])

        # Delete versions if not dry run
        pruned_versions = []

        if not dry_run:
            for version in to_prune:
                try:
                    await self._rollback_manager.delete_version(version["id"])
                    pruned_versions.append(version["id"])
                except Exception as e:
                    logger.warning(f"Failed to prune version {version['id']}: {e}")

        return {
            "strategy": "hybrid",
            "params": params,
            "versions_pruned": len(pruned_versions) if not dry_run else 0,
            "candidates": len(to_prune),
            "pruned_ids": pruned_versions if not dry_run else [],
            "dry_run": dry_run
        }

    async def _get_all_versions(self) -> List[Dict[str, Any]]:
        """Get all versions in the system."""
        # This is a conceptual implementation
        # In practice, you would query the database directly
        return await self._rollback_manager.list_all_versions()

    async def _get_versions_by_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get versions grouped by file path."""
        all_versions = await self._get_all_versions()

        # Group by original file path
        by_file = {}

        for version in all_versions:
            file_path = version["original_path"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(version)

        return by_file
```

### 4.5 Integration with Notification System

Enhance integration with the notification system for version events:

```python
class VersionNotifier:
    """
    Notifies users of version events.

    This class integrates the rollback system with the notification
    system to alert users about version creation, restoration, etc.
    """

    def __init__(self, rollback_manager):
        """Initialize the version notifier."""
        self._rollback_manager = rollback_manager
        self._registry = rollback_manager._registry
        self._notification_manager = self._registry.notification_manager

    async def notify_version_created(
        self,
        version_id: str,
        is_auto: bool = False
    ) -> None:
        """
        Send notification about a new version being created.

        Args:
            version_id: ID of the created version
            is_auto: Whether the version was created automatically
        """
        # Get version details
        version_info = await self._rollback_manager.get_version(version_id)
        if not version_info:
            return

        # Prepare notification
        original_path = version_info["original_path"]
        version_name = version_info["version_name"]

        if is_auto:
            message = f"Automatic version '{version_name}' created for {original_path}"
        else:
            message = f"Version '{version_name}' created for {original_path}"

        # Send notification
        await self._notification_manager.send_notification(
            message=message,
            level="INFO",
            metadata={
                "version_id": version_id,
                "file_path": original_path,
                "version_name": version_name,
                "is_auto": is_auto,
                "timestamp": version_info["timestamp"],
                "size": version_info["size"]
            },
            sender_id="rollback_manager"
        )

    async def notify_version_restored(
        self,
        version_id: str,
        restored_path: str
    ) -> None:
        """
        Send notification about a version being restored.

        Args:
            version_id: ID of the restored version
            restored_path: Path where the version was restored
        """
        # Get version details
        version_info = await self._rollback_manager.get_version(version_id)
        if not version_info:
            return

        # Prepare notification
        original_path = version_info["original_path"]
        version_name = version_info["version_name"]

        message = f"Restored version '{version_name}' to {restored_path}"

        # Send notification
        await self._notification_manager.send_notification(
            message=message,
            level="INFO",
            metadata={
                "version_id": version_id,
                "original_path": original_path,
                "restored_path": restored_path,
                "version_name": version_name,
                "timestamp": version_info["timestamp"]
            },
            sender_id="rollback_manager"
        )

    async def notify_versions_pruned(
        self,
        pruning_result: Dict[str, Any]
    ) -> None:
        """
        Send notification about versions being pruned.

        Args:
            pruning_result: Result of pruning operation
        """
        if pruning_result.get("dry_run", True):
            return

        count = pruning_result.get("versions_pruned", 0)
        if count == 0:
            return

        # Prepare notification
        strategy = pruning_result.get("strategy", "unknown")

        message = f"Pruned {count} old versions using {strategy} strategy"

        # Send notification
        await self._notification_manager.send_notification(
            message=message,
            level="INFO",
            metadata={
                "pruning_strategy": strategy,
                "versions_pruned": count,
                "timestamp": datetime.now().isoformat()
            },
            sender_id="rollback_manager"
        )
```

## 5. Implementation Plan

### Phase 1: Storage Optimization (2-3 weeks)

1. **Implement Differential Storage**

   - Create the DiffVersion class
   - Add algorithm for creating and applying diffs
   - Modify version creation and restoration processes
   - Add storage type metadata to versions

2. **Add Version Pruning**
   - Implement the VersionPruner class
   - Add time-based, count-based, and hybrid pruning strategies
   - Create pruning scheduling and automation
   - Add configuration options for pruning policies

### Phase 2: Version Analysis Tools (1-2 weeks)

3. **Implement Comparison Tools**

   - Create the VersionComparer class
   - Add unified diff and HTML diff generation
   - Implement change analysis functionality
   - Create API for version comparison

4. **Content-Based Versioning**
   - Implement the ContentVersioningPolicy class
   - Add change detection and significance evaluation
   - Integrate with the version scheduler
   - Add configuration for content policies

### Phase 3: Integration and Usability (1-2 weeks)

5. **Notification Integration**

   - Implement the VersionNotifier class
   - Add notifications for key version events
   - Create subscription options for version notifications
   - Add notification templates for version events

6. **Batch Operations Support**
   - Add batch version creation
   - Implement batch restoration
   - Support batch comparison
   - Add version search and filtering

## 6. Priority Matrix

| Improvement              | Impact | Effort | Priority |
| ------------------------ | ------ | ------ | -------- |
| Differential Storage     | High   | High   | 1        |
| Version Comparison       | High   | Low    | 1        |
| Version Pruning          | High   | Medium | 2        |
| Content-Based Versioning | Medium | Medium | 2        |
| Notification Integration | Medium | Low    | 3        |
| Batch Operations         | Low    | Medium | 4        |

## 7. Conclusion

The rollback module provides a solid foundation for file versioning in the
AIChemist Codex system. The proposed improvements will enhance its efficiency,
functionality, and integration with other system components while maintaining
alignment with architectural principles.

By implementing differential storage and version pruning, the system can manage
storage space more efficiently while retaining valuable version history. The
addition of content-based versioning and comparison tools will make the rollback
system more intelligent and user-friendly, automatically creating versions when
meaningful changes occur and providing tools to analyze differences between
versions.

The most immediate priorities should be implementing differential storage to
optimize space usage and version comparison tools to enhance usability, as these
will provide the most significant improvements to the system's functionality and
efficiency.
