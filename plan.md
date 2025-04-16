# AIchemist Codex Refactoring Plan - Agent Execution Instructions

> **PROGRESS MARKER**: Plan review completed. Execution not yet started. Next step is Phase 1.1.

## Overview

This is a step-by-step execution guide for AIchemist Codex refactoring. Each instruction is designed to be atomic, verifiable, and requires minimal reasoning. Execute steps IN SEQUENCE and report any failures immediately.

**IMPORTANT: When a verification step fails, STOP and report the exact error before proceeding.**


**Phase 1: Implement Application Layer & Relocate Services**




### 1.3. Move Code Analysis Service

**PRE-CHECK**: Run:
```bash
ls -la src/the_aichemist_codex/infrastructure/analysis/code_analysis_service.py
```
**FAILURE**: If file doesn't exist, STOP and report error.

```bash
git mv src/the_aichemist_codex/infrastructure/analysis/code_analysis_service.py src/the_aichemist_codex/application/services/code_analysis_service.py
```

**VERIFICATION**: Run:
```bash
ls -la src/the_aichemist_codex/application/services/code_analysis_service.py && [ ! -f src/the_aichemist_codex/infrastructure/analysis/code_analysis_service.py ]
```
**SUCCESS**: New file exists and old file doesn't
**FAILURE**: If verification fails, STOP and report error.

### 1.4. Create CodeAnalysisServiceInterface

**PRE-CHECK**: Run:
```bash
mkdir -p src/the_aichemist_codex/domain/services/interfaces
touch src/the_aichemist_codex/domain/services/interfaces/__init__.py
```

**STEP**: Create interface file:
```bash
cat > src/the_aichemist_codex/domain/services/interfaces/code_analysis_service.py << 'EOL'
from typing import Any, Protocol
from pathlib import Path
from uuid import UUID

class CodeAnalysisServiceInterface(Protocol):
    """Interface for code analysis services."""

    async def calculate_complexity(self, artifact_id: UUID) -> float:
        """Calculate complexity of a code artifact."""
        ...

    async def extract_knowledge(self, artifact_id: UUID, max_items: int = 10) -> list[dict[str, Any]]:
        """Extract knowledge items from a code artifact."""
        ...

    async def get_summary(self, artifact_id: UUID) -> str:
        """Get a summary of a code artifact."""
        ...

    async def get_structure(self, artifact_id: UUID) -> dict[str, list[dict[str, Any]]]:
        """Get the structure of a code artifact."""
        ...
EOL
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.domain.services.interfaces.code_analysis_service import CodeAnalysisServiceInterface; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 1.5. Update Domain Services __init__.py

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/services/interfaces/__init__.py ]
```
**FAILURE**: If file doesn't exist, STOP and report error.

```bash
cat > src/the_aichemist_codex/domain/services/interfaces/__init__.py << 'EOL'
from .code_analysis_service import CodeAnalysisServiceInterface

__all__ = ["CodeAnalysisServiceInterface"]
EOL
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.domain.services.interfaces import CodeAnalysisServiceInterface; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 1.6. Create AnalysisResultDTO

```bash
cat > src/the_aichemist_codex/application/dto/__init__.py << 'EOL'
from .analysis_result_dto import AnalysisResultDTO

__all__ = ["AnalysisResultDTO"]
EOL

cat > src/the_aichemist_codex/application/dto/analysis_result_dto.py << 'EOL'
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

@dataclass
class AnalysisResultDTO:
    """Data Transfer Object for analysis results."""

    artifact_id: UUID
    complexity: Optional[float] = None
    summary: Optional[str] = None
    knowledge_items: Optional[list[dict[str, Any]]] = None
    structure: Optional[dict[str, list[dict[str, Any]]]] = None
EOL
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.application.dto import AnalysisResultDTO; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 1.7. Implement TechnicalCodeAnalyzer

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/infrastructure/analysis/technical_analyzer.py ]
```
**FAILURE**: If file doesn't exist, STOP and report error.

```bash
cat > temp_script.py << 'EOL'
import os
import re

# Define the file path
filepath = 'src/the_aichemist_codex/infrastructure/analysis/technical_analyzer.py'

# Read the existing file
with open(filepath, 'r') as file:
    content = file.read()

# Create the class implementation to add at the top
implementation = """from the_aichemist_codex.domain.services.interfaces.code_analysis_service import CodeAnalysisServiceInterface
from uuid import UUID

class TechnicalCodeAnalyzer(CodeAnalysisServiceInterface):
    \"\"\"Implementation of the CodeAnalysisServiceInterface.\"\"\"

    def __init__(self, repository):
        \"\"\"Initialize with a repository to access artifacts.\"\"\"
        self.repository = repository

    async def calculate_complexity(self, artifact_id: UUID) -> float:
        \"\"\"Calculate complexity of a code artifact.\"\"\"
        artifact = await self.repository.get_by_id(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact with id {artifact_id} not found")

        return calculate_python_complexity(artifact.content)

    async def extract_knowledge(self, artifact_id: UUID, max_items: int = 10) -> list[dict[str, str]]:
        \"\"\"Extract knowledge items from a code artifact.\"\"\"
        artifact = await self.repository.get_by_id(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact with id {artifact_id} not found")

        return extract_knowledge_from_content(artifact.content, max_items=max_items)

    async def get_summary(self, artifact_id: UUID) -> str:
        \"\"\"Get a summary of a code artifact.\"\"\"
        artifact = await self.repository.get_by_id(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact with id {artifact_id} not found")

        return summarize_code(artifact.content)

    async def get_structure(self, artifact_id: UUID) -> dict[str, list[dict[str, str]]]:
        \"\"\"Get the structure of a code artifact.\"\"\"
        artifact = await self.repository.get_by_id(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact with id {artifact_id} not found")

        return analyze_structure(artifact.content)
"""

# Find the imports section to place our new import
import_match = re.search(r'import.*?\n\n', content, re.DOTALL)
if import_match:
    # Insert the implementation after the imports
    position = import_match.end()
    new_content = content[:position] + implementation + "\n\n" + content[position:]
else:
    # If imports pattern not found, just add at the top
    new_content = implementation + "\n\n" + content

# Write back to the file
with open(filepath, 'w') as file:
    file.write(new_content)

print("TechnicalCodeAnalyzer implementation added to technical_analyzer.py")
EOL

python temp_script.py
rm temp_script.py
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.infrastructure.analysis.technical_analyzer import TechnicalCodeAnalyzer; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 1.8. Update Application CodeAnalysisService

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/application/services/code_analysis_service.py ]
```
**FAILURE**: If file doesn't exist, STOP and report error.

```bash
cat > temp_script.py << 'EOL'
import re

filepath = 'src/the_aichemist_codex/application/services/code_analysis_service.py'

with open(filepath, 'r') as file:
    content = file.read()

# 1. Update imports
imports = """from typing import Any, Optional
from uuid import UUID

from the_aichemist_codex.domain.repositories.code_artifact_repository import CodeArtifactRepository
from the_aichemist_codex.domain.services.interfaces.code_analysis_service import CodeAnalysisServiceInterface
from the_aichemist_codex.application.dto.analysis_result_dto import AnalysisResultDTO
"""

# Replace existing imports
content = re.sub(r'from.*?import.*?\n\n', imports + "\n\n", content, flags=re.DOTALL, count=1)

# 2. Update the class definition and __init__ method
class_def = """class ApplicationCodeAnalysisService:
    \"\"\"Application service for code analysis operations.\"\"\"

    def __init__(self, repository: CodeArtifactRepository, technical_analyzer: CodeAnalysisServiceInterface) -> None:
        \"\"\"Initialize with the required dependencies.\"\"\"
        self.repository = repository
        self.technical_analyzer = technical_analyzer
"""

# Replace existing class definition and __init__
content = re.sub(r'class ApplicationCodeAnalysisService:.*?def __init__.*?:.*?\n(\s+).*?\n\n',
                class_def + "\n\n", content, flags=re.DOTALL)

# 3. Add the get_artifact_analysis method
method_def = """    async def get_artifact_analysis(self, artifact_id: UUID, include_structure: bool = False,
                          max_knowledge_items: int = 10) -> AnalysisResultDTO:
        \"\"\"Get comprehensive analysis of an artifact.

        Args:
            artifact_id: The unique ID of the artifact to analyze
            include_structure: Whether to include structure analysis (more expensive)
            max_knowledge_items: Maximum number of knowledge items to extract

        Returns:
            A data transfer object with the analysis results

        Raises:
            ValueError: If the artifact doesn't exist
        \"\"\"
        # Verify artifact exists
        artifact = await self.repository.get_by_id(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact with id {artifact_id} not found")

        # Collect analysis tasks
        complexity = await self.technical_analyzer.calculate_complexity(artifact_id)
        summary = await self.technical_analyzer.get_summary(artifact_id)
        knowledge_items = await self.technical_analyzer.extract_knowledge(
            artifact_id, max_items=max_knowledge_items
        )

        # Structure analysis is optional (more expensive)
        structure = None
        if include_structure:
            structure = await self.technical_analyzer.get_structure(artifact_id)

        # Create and return the DTO
        return AnalysisResultDTO(
            artifact_id=artifact_id,
            complexity=complexity,
            summary=summary,
            knowledge_items=knowledge_items,
            structure=structure
        )
"""

# Add the new method before the last method in the class
last_method = re.search(r'    async def \w+.*?(?=\n\n)', content, flags=re.DOTALL)
if last_method:
    position = last_method.start()
    content = content[:position] + method_def + "\n" + content[position:]
else:
    # If no existing methods found, add it after class definition
    class_end = re.search(r'class ApplicationCodeAnalysisService:.*?self.technical_analyzer = technical_analyzer\n',
                         content, flags=re.DOTALL)
    if class_end:
        position = class_end.end()
        content = content[:position] + "\n" + method_def + content[position:]

with open(filepath, 'w') as file:
    file.write(content)

print("Updated ApplicationCodeAnalysisService successfully.")
EOL

python temp_script.py
rm temp_script.py
```

**VERIFICATION**: Run:
```bash
ruff check src/the_aichemist_codex/application/services/code_analysis_service.py
```
**SUCCESS**: No critical errors (warnings are acceptable)
**FAILURE**: If critical errors occur, STOP and report error.

### 1.9. Update CLI Analysis Command **DONE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/interfaces/cli/commands/analysis.py ]
```
**FAILURE**: If file doesn't exist, STOP and report error.

```bash
cat > temp_script.py << 'EOL'
import re

filepath = 'src/the_aichemist_codex/interfaces/cli/commands/analysis.py'

with open(filepath, 'r') as file:
    content = file.read()

# Find the analyze_artifact command function
analyze_func_match = re.search(r'def analyze_artifact.*?def', content, flags=re.DOTALL)
if not analyze_func_match:
    print("Could not find analyze_artifact function in analysis.py")
    exit(1)

analyze_func = analyze_func_match.group(0)
# Remove the trailing 'def' that was captured
analyze_func = analyze_func[:-3].strip()

# Create the updated function
updated_func = """def analyze_artifact(
    artifact_id: str = typer.Argument(..., help="ID of the artifact to analyze"),
    include_structure: bool = typer.Option(False, "--structure", "-s", help="Include code structure analysis"),
    max_knowledge: int = typer.Option(10, "--max-knowledge", "-k", help="Maximum knowledge items to extract"),
) -> None:
    \"\"\"Analyze a code artifact by ID.\"\"\"
    try:
        # Convert string ID to UUID
        art_id = UUID(artifact_id)

        # Get the analysis results from the application service
        analysis_result = asyncio.run(_service.get_artifact_analysis(
            artifact_id=art_id,
            include_structure=include_structure,
            max_knowledge_items=max_knowledge
        ))

        # Format and display the results
        console = get_console()

        console.print()
        console.print(f"[bold green]Analysis Results for Artifact:[/] {artifact_id}")
        console.print()

        # Complexity
        if analysis_result.complexity is not None:
            console.print(f"[bold]Complexity Score:[/] {analysis_result.complexity:.2f}")
            console.print()

        # Summary
        if analysis_result.summary:
            console.print("[bold]Summary:[/]")
            console.print(analysis_result.summary)
            console.print()

        # Knowledge Items
        if analysis_result.knowledge_items and len(analysis_result.knowledge_items) > 0:
            console.print("[bold]Knowledge Extracted:[/]")
            for item in analysis_result.knowledge_items:
                console.print(f"- {item.get('item', 'Unknown item')}")
            console.print()

        # Structure (conditionally included)
        if analysis_result.structure:
            console.print("[bold]Code Structure:[/]")
            for section, elements in analysis_result.structure.items():
                console.print(f"[bold]{section}:[/]")
                for element in elements:
                    console.print(f"  - {element.get('name', 'Unnamed')}: {element.get('type', 'Unknown type')}")
            console.print()

    except ValueError as e:
        console = get_console()
        console.print(f"[bold red]Error:[/] {str(e)}")
    except Exception as e:
        console = get_console()
        console.print(f"[bold red]Unexpected error:[/] {str(e)}")
"""

# Replace the old function with the updated one
content = content.replace(analyze_func, updated_func)

with open(filepath, 'w') as file:
    file.write(content)

print("Updated analyze_artifact function in analysis.py successfully.")
EOL

python temp_script.py
rm temp_script.py
```

**VERIFICATION**: Run:
```bash
ruff check src/the_aichemist_codex/interfaces/cli/commands/analysis.py
```
**SUCCESS**: No critical errors (warnings are acceptable)
**FAILURE**: If critical errors occur, STOP and report error.

### 1.10. Run Type and Style Checks

```bash
mypy src/the_aichemist_codex/application/services/ src/the_aichemist_codex/domain/services/interfaces/ src/the_aichemist_codex/infrastructure/analysis/technical_analyzer.py
```
**NOTE**: Record any errors but proceed.

```bash
ruff check src/the_aichemist_codex/application/ src/the_aichemist_codex/domain/services/interfaces/ src/the_aichemist_codex/infrastructure/analysis/technical_analyzer.py
```
**NOTE**: Record any errors but proceed.

### 1.11. Verification Test

```bash
pytest -xvs tests/unit/application/ tests/interfaces/cli/ || echo "Tests currently failing, proceed anyway"
```
**NOTE**: Record test results but proceed regardless.


## **Phase 1 COMPLETE**

---


## **Phase 2: Fix Dependencies & Integrate Loose Code**


### 2.1. Create FileDataForTagging Value Object **COMPLETE**

**PRE-CHECK**: Run:
```bash
mkdir -p src/the_aichemist_codex/domain/value_objects
```
**FAILURE**: If directory creation fails, STOP and report error.

```bash
cat > src/the_aichemist_codex/domain/value_objects/tagging_data.py << 'EOL'
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

@dataclass
class FileDataForTagging:
    """Value object containing file data needed for tag suggestion."""

    path: Path
    mime_type: str
    keywords: List[str] = field(default_factory=list)
    topics: List[Dict[str, Any]] = field(default_factory=list)
    content_sample: Optional[str] = None

    def __post_init__(self):
        """Ensure path is a Path object."""
        if isinstance(self.path, str):
            self.path = Path(self.path)
EOL
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.domain.value_objects.tagging_data import FileDataForTagging; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 2.2. Update Value Objects __init__.py **COMPLETE**

**PRE-CHECK**: Run:
```bash
touch src/the_aichemist_codex/domain/value_objects/__init__.py
```

```bash
cat > src/the_aichemist_codex/domain/value_objects/__init__.py << 'EOL'
from .tagging_data import FileDataForTagging

__all__ = ["FileDataForTagging"]
EOL
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.domain.value_objects import FileDataForTagging; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 2.3. Update TagSuggester Domain Service **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/tagging/suggester.py ]
```
**FAILURE**: If file doesn't exist, STOP and report error.

```bash
cat > temp_script.py << 'EOL'
import re

filepath = 'src/the_aichemist_codex/domain/tagging/suggester.py'

with open(filepath, 'r') as file:
    content = file.read()

# 1. Update imports
# Add FileDataForTagging import and remove FileMetadata import
new_imports = """from typing import List, Optional, Set
from pathlib import Path

from the_aichemist_codex.domain.value_objects import FileDataForTagging
"""

# Replace existing imports pattern
content = re.sub(r'from typing.*?from the_aichemist_codex.infrastructure.fs.file_metadata import FileMetadata',
                 new_imports, content, flags=re.DOTALL)

# 2. Update suggest_tags method signature and implementation
old_method_pattern = r'def suggest_tags\(file_metadata: FileMetadata\).*?return suggested_tags'
new_method = """def suggest_tags(tagging_data: FileDataForTagging) -> Set[str]:
    \"\"\"Suggest tags based on file data.

    Args:
        tagging_data: Value object containing file data for tagging

    Returns:
        A set of suggested tags
    \"\"\"
    suggested_tags: Set[str] = set()

    # Add tags based on mime type
    mime_tags = _suggest_tags_from_mime_type(tagging_data.mime_type)
    suggested_tags.update(mime_tags)

    # Add tags based on file extension
    ext_tags = _suggest_tags_from_extension(tagging_data.path.suffix)
    suggested_tags.update(ext_tags)

    # Add tags based on keywords if available
    if tagging_data.keywords:
        keyword_tags = _suggest_tags_from_keywords(tagging_data.keywords)
        suggested_tags.update(keyword_tags)

    # Add tags based on topics if available
    if tagging_data.topics:
        topic_tags = _suggest_tags_from_topics(tagging_data.topics)
        suggested_tags.update(topic_tags)

    return suggested_tags"""

# Replace the old method with the new one
content = re.sub(old_method_pattern, new_method, content, flags=re.DOTALL)

# 3. Update method implementations to use new parameter types where needed
# This is a bit more complex as we need to find and update helper methods

# For _suggest_tags_from_extension method
content = re.sub(r'def _suggest_tags_from_extension\(file_path: Path\)',
                 'def _suggest_tags_from_extension(extension: str)',
                 content)

# If there's a line like: extension = file_path.suffix, replace it
content = re.sub(r'extension = file_path.suffix',
                 '# extension is now passed directly',
                 content)

with open(filepath, 'w') as file:
    file.write(content)

print("Updated TagSuggester to use FileDataForTagging instead of FileMetadata")
EOL

python temp_script.py
rm temp_script.py
```

**VERIFICATION**: Run:
```bash
ruff check src/the_aichemist_codex/domain/tagging/suggester.py
```
**SUCCESS**: No critical errors (warnings are acceptable)
**FAILURE**: If critical errors occur, STOP and report error.

### 2.4. Move Association Utils from Unsorted to Domain Services **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/unsorted/memory/association_utils.py ]
```
**FAILURE**: If file doesn't exist, skip this step and move to 2.5.

```bash
mkdir -p src/the_aichemist_codex/domain/services/utils
touch src/the_aichemist_codex/domain/services/utils/__init__.py
git mv src/the_aichemist_codex/domain/unsorted/memory/association_utils.py src/the_aichemist_codex/domain/services/utils/association_utils.py
```

**VERIFICATION**: Run:
```bash
[ -f src/the_aichemist_codex/domain/services/utils/association_utils.py ] && [ ! -f src/the_aichemist_codex/domain/unsorted/memory/association_utils.py ]
```
**SUCCESS**: Command exits with status 0 (new file exists, old file doesn't)
**FAILURE**: If verification fails, STOP and report error.

### 2.5. Update Association Utils Imports **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/services/utils/association_utils.py ]
```
**FAILURE**: If file doesn't exist, skip this step and move to 2.6.

```bash
cat > temp_script.py << 'EOL'
import os
import re

# Define file path
filepath = 'src/the_aichemist_codex/domain/services/utils/association_utils.py'

# Read the existing file
with open(filepath, 'r') as file:
    content = file.read()

# Update import paths from unsorted to their new locations
content = re.sub(r'from .*?\.domain\.unsorted\.domain\.entities',
                 'from the_aichemist_codex.domain.entities',
                 content)

# Write back to the file
with open(filepath, 'w') as file:
    file.write(content)

print(f"Updated imports in {filepath}")
EOL

python temp_script.py
rm temp_script.py
```

**VERIFICATION**: Run:
```bash
ruff check src/the_aichemist_codex/domain/services/utils/association_utils.py
```
**SUCCESS**: No import errors (other warnings are acceptable)
**FAILURE**: If import errors occur, STOP and report error.

### 2.6. Update Domain Services __init__.py for Utils **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/services/utils/__init__.py ]
```
**FAILURE**: If file doesn't exist, create it with `touch`.

```bash
cat > src/the_aichemist_codex/domain/services/utils/__init__.py << 'EOL'
from .association_utils import calculate_association_strength, create_association

__all__ = ["calculate_association_strength", "create_association"]
EOL
```

**VERIFICATION**: Run:
```bash
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.domain.services.utils import calculate_association_strength, create_association; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 2.7. Compare and Merge Memory Entities **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/unsorted/domain/entities/memory.py ] && [ -f src/the_aichemist_codex/domain/entities/memory.py ]
```
**FAILURE**: If either file doesn't exist, skip this step and move to 2.8.

```bash
cat > temp_script.py << 'EOL'
import os
import difflib

# Define file paths
source_file = 'src/the_aichemist_codex/domain/unsorted/domain/entities/memory.py'
target_file = 'src/the_aichemist_codex/domain/entities/memory.py'

# Read the files
with open(source_file, 'r') as file:
    source_content = file.readlines()

with open(target_file, 'r') as file:
    target_content = file.readlines()

# Create a diff
diff = difflib.unified_diff(target_content, source_content,
                            fromfile=target_file, tofile=source_file)

# Save the diff
diff_file = 'memory_diff.txt'
with open(diff_file, 'w') as file:
    file.writelines(diff)

print(f"Diff between files saved to {diff_file}")
print("Please review the diff manually and merge any valuable additions from")
print(f"{source_file} into {target_file}")
EOL

python temp_script.py
rm temp_script.py
```

**NOTE**: You must manually review `memory_diff.txt` and decide what to merge.
This requires human judgment. If you can't make this decision, STOP and report that human review is needed.

### 2.8. Evaluate and Move Schemas **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -f src/the_aichemist_codex/domain/unsorted/schemas.py ]
```
**FAILURE**: If file doesn't exist, skip this step and move to 2.9.

```bash
mkdir -p src/the_aichemist_codex/infrastructure/validation
touch src/the_aichemist_codex/infrastructure/validation/__init__.py
git mv src/the_aichemist_codex/domain/unsorted/schemas.py src/the_aichemist_codex/infrastructure/validation/schemas.py
```

**VERIFICATION**: Run:
```bash
[ -f src/the_aichemist_codex/infrastructure/validation/schemas.py ] && [ ! -f src/the_aichemist_codex/domain/unsorted/schemas.py ]
```
**SUCCESS**: Command exits with status 0 (new file exists, old file doesn't)
**FAILURE**: If verification fails, STOP and report error.

### 2.9. Remove Unsorted Directory **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -d src/the_aichemist_codex/domain/unsorted ]
```
**FAILURE**: If directory doesn't exist, skip this step and move to 2.10.

```bash
git rm -r src/the_aichemist_codex/domain/unsorted
```

**VERIFICATION**: Run:
```bash
[ ! -d src/the_aichemist_codex/domain/unsorted ]
```
**SUCCESS**: Command exits with status 0 (directory doesn't exist)
**FAILURE**: If verification fails, STOP and report error.

### 2.10. Remove ToSort Directory **COMPLETE**

**PRE-CHECK**: Run:
```bash
[ -d src/the_aichemist_codex/interfaces/ToSort ]
```
**FAILURE**: If directory doesn't exist, skip this step and move to 2.11.

```bash
git rm -r src/the_aichemist_codex/interfaces/ToSort
```

**VERIFICATION**: Run:
```bash
[ ! -d src/the_aichemist_codex/interfaces/ToSort ]
```
**SUCCESS**: Command exits with status 0 (directory doesn't exist)
**FAILURE**: If verification fails, STOP and report error.

### 2.11. Verification of Dependencies Fix

```bash
ruff check src/the_aichemist_codex/domain/tagging/ src/the_aichemist_codex/domain/value_objects/ src/the_aichemist_codex/domain/services/utils/
```
**NOTE**: Record any errors but proceed.

```bash
mypy src/the_aichemist_codex/domain/tagging/ src/the_aichemist_codex/domain/value_objects/ src/the_aichemist_codex/domain/services/utils/
```
**NOTE**: Record any errors but proceed.

```bash
pytest tests/unit/domain/ -k "tagging or value_objects" || echo "Tests might be failing, proceed anyway"
```
**NOTE**: Record test results but proceed regardless.

## **Phase 2 COMPLETE**

---

# **Phase 3: Code Cleanup & Consolidation**

### 3.1. Identify Infrastructure Utils Files

```powershell
Get-ChildItem -Path src/the_aichemist_codex/infrastructure/utils -File -Exclude '__init__.py' -Filter '*.py' | Sort-Object Name
```
**NOTE**: Record the list of files found in the utils root directory.

### 3.2. Create Utility Script for Moving Utils

```powershell
# (No change: Python script creation remains the same)
cat > move_utils.py << 'EOL'
# ... existing code ...
EOL
```

### 3.3. Edit Utils Mapping and Run Script

**IMPORTANT**: You must edit the `move_utils.py` script to add the actual list of files found in step 3.1 to the `utils_mapping` dictionary. For each file, decide an appropriate subdirectory (like `'cache'`, `'common'`, `'concurrency'`, `'errors'`, `'io'`, `'hashing'`, etc.).

**Example**: If you found `hash_utils.py` and `time_utils.py` in step 3.1, edit `move_utils.py` to include:
```python
utils_mapping = {
    'hash_utils.py': 'hashing',
    'time_utils.py': 'common',
    # Add all other files here with appropriate subdirectories
}
```

**Run the script:**
```powershell
python move_utils.py
```

**VERIFICATION**: Run:
```powershell
Get-ChildItem -Path src/the_aichemist_codex/infrastructure/utils/*/ | Format-Table
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.infrastructure.utils import *; print('Success')"
```
**SUCCESS**: Files are organized into subdirectories and import succeeds
**FAILURE**: If import fails, STOP and report error.

### 3.4. Update Codebase to Use New Import Paths

```powershell
# (No change: Python script creation remains the same)
cat > update_imports.py << 'EOL'
# ... existing code ...
EOL
```

**IMPORTANT**: You must edit the `update_imports.py` script to add the actual import paths for files moved in step 3.3. For each file moved, add an entry to the `import_replacements` dictionary mapping the old import path to the new one.

**Example**: If you moved `hash_utils.py` to the `hashing` subdirectory, add:
```python
import_replacements = {
    'the_aichemist_codex.infrastructure.utils.hash_utils': 'the_aichemist_codex.infrastructure.utils.hashing.hash_utils',
    # Add all other moved modules here
}
```

**Run the script:**
```powershell
python update_imports.py
```

**VERIFICATION**: Run:
```powershell
ruff check src/the_aichemist_codex --select F401,F404,E402
```
**SUCCESS**: No import errors (other warnings are acceptable)
**FAILURE**: If import errors occur, fix them manually by updating import statements in the files.

### 3.5. Delete Original Files from Utils Root

**WARNING**: Only proceed when you've verified the code imports correctly!

```powershell
Get-ChildItem -Path src/the_aichemist_codex/infrastructure/utils -File -Exclude '__init__.py' -Filter '*.py' | ForEach-Object { git rm $_.FullName }
```

**VERIFICATION**: Run:
```powershell
(Get-ChildItem -Path src/the_aichemist_codex/infrastructure/utils -File -Exclude '__init__.py' -Filter '*.py').Count
```
**SUCCESS**: Count is 0 (no files other than __init__.py in root)
**FAILURE**: If count is not 0, delete remaining files manually.

### 3.6. Verify Config Loader Location

**PRE-CHECK**: Run:
```powershell
Test-Path src/the_aichemist_codex/infrastructure/config/loader/config_loader.py
```
**FAILURE**: If file doesn't exist, STOP and report error.

```powershell
Select-String -Pattern 'get_codex_config' -Path src/the_aichemist_codex/infrastructure/config/loader/config_loader.py
```
**VERIFICATION**: Check if `get_codex_config` function exists in the output.
**FAILURE**: If function not found, STOP and report error.

### 3.7. Create Default Config Directory

```powershell
New-Item -Path src/the_aichemist_codex/infrastructure/config/defaults -ItemType Directory -Force
```

**VERIFICATION**: Run:
```powershell
Test-Path src/the_aichemist_codex/infrastructure/config/defaults
```
**SUCCESS**: Command returns True (directory exists)
**FAILURE**: If verification fails, STOP and report error.

### 3.8. Move Settings File to Default Config

**PRE-CHECK**: Run:
```powershell
Test-Path config/settings.yaml
```
**FAILURE**: If file doesn't exist, skip this step and move to 3.9.

```powershell
Copy-Item config/settings.yaml src/the_aichemist_codex/infrastructure/config/defaults/settings.yaml -Force
```

**VERIFICATION**: Run:
```powershell
Test-Path src/the_aichemist_codex/infrastructure/config/defaults/settings.yaml
```
**SUCCESS**: Command returns True (file exists)
**FAILURE**: If verification fails, STOP and report error.

### 3.9. Update Config Loader Path Reference

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
ruff check src/the_aichemist_codex/infrastructure/config/loader/config_loader.py
```
**SUCCESS**: No critical errors (warnings are acceptable)
**FAILURE**: If critical errors occur, fix them manually.

### 3.10. Move Other Config Files if Needed

**PRE-CHECK**: Run:
```powershell
Get-ChildItem config
```

For each YAML file found (e.g., `sorting_rules.yaml`, `logging.yaml`), decide if it should be a default or an example:

**For default files**:
```powershell
Copy-Item config/FILE_NAME.yaml src/the_aichemist_codex/infrastructure/config/defaults/FILE_NAME.yaml -Force
```

**For example files**:
```powershell
New-Item -Path docs/examples/config -ItemType Directory -Force
Copy-Item config/FILE_NAME.yaml docs/examples/config/FILE_NAME.yaml -Force
```

### 3.11. Update Docs to Reflect New Config Location

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

### 3.12. Remove Root Config Directory

```powershell
git rm -r config/
```

**VERIFICATION**: Run:
```powershell
Test-Path config
```
**SUCCESS**: Command returns False (directory doesn't exist)
**FAILURE**: If verification fails, STOP and report error.

### 3.13. Verify Configuration Works

```powershell
# (No change: Python script creation remains the same)
cat > config_test.py << 'EOL'
# ... existing code ...
EOL

python config_test.py
Remove-Item config_test.py
```

**VERIFICATION**: Check that config sections are printed (e.g., "logging", "application", etc.)
**FAILURE**: If config doesn't load, fix the issue before proceeding.

### 3.14. Run Verification Checks

```powershell
ruff check src/the_aichemist_codex/infrastructure/utils/ src/the_aichemist_codex/infrastructure/config/
```
**NOTE**: Record any errors but proceed.

```powershell
mypy src/the_aichemist_codex/infrastructure/utils/ src/the_aichemist_codex/infrastructure/config/
```
**NOTE**: Record any errors but proceed.

---

**Phase 4: Enhancements & Best Practices**

### 4.1. Locate Entry Point File

```powershell
Get-ChildItem -Path src/the_aichemist_codex -Recurse -Include main.py,cli.py -File | Where-Object { $_.FullName -notmatch '__pycache__' }
```

**NOTE**: Record the path to the main entry point file(s) found. For the following steps,
replace `ENTRY_POINT_FILE` with the appropriate file path (e.g., `src/the_aichemist_codex/main.py`
or `src/the_aichemist_codex/interfaces/cli/cli.py`).

### 4.2. Fix Logging Initialization

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
ruff check ENTRY_POINT_FILE
```
**SUCCESS**: No critical errors (warnings are acceptable)
**FAILURE**: If critical errors occur, fix them manually.

### 4.3. Create Logging Configuration Module

**PRE-CHECK**: Run:
```powershell
Test-Path src/the_aichemist_codex/infrastructure/config/logging.py
```
**SUCCESS**: If file exists, skip to step 4.4.

```powershell
# (No change: Python script creation remains the same)
cat > src/the_aichemist_codex/infrastructure/config/logging.py << 'EOL'
# ... existing code ...
EOL
```

**VERIFICATION**: Run:
```powershell
python -c "import sys; sys.path.append('src'); from the_aichemist_codex.infrastructure.config.logging import setup_logging; print('Success')"
```
**SUCCESS**: Output is `Success`
**FAILURE**: If errors occur, STOP and report error.

### 4.4. Check for Loguru Usage

```powershell
Select-String -Pattern 'import loguru' -Path src/**/*.py -Recurse
Select-String -Pattern 'from loguru' -Path src/**/*.py -Recurse
```

**NOTE**: If loguru is found, examine the usage. If it's essential, update the `setup_logging` function above to integrate it. If it's not actively used, proceed to remove it.

### 4.5. Find and Fix Broad Exception Handlers

```powershell
Select-String -Pattern 'except Exception:' -Path src/the_aichemist_codex/**/*.py -Recurse
```

**NOTE**: For each file found, create a script to fix the broad exception. Here's an example for one file:

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

Repeat for each file that needs to be fixed.

### 4.6. Fix Encryption Key Storage

**PRE-CHECK**: Run:
```powershell
Test-Path data/.encryption_key
```
**FAILURE**: If file doesn't exist, skip this step and move to 4.7.

```powershell
git rm data/.encryption_key

# Add to .gitignore
if (-not (Select-String -Path .gitignore -Pattern 'data/.encryption_key' -Quiet)) { Add-Content .gitignore 'data/.encryption_key' }
```

**VERIFICATION**: Run:
```powershell
git status data/.encryption_key; if ($LASTEXITCODE -ne 0) { Write-Output 'Success: file removed from git' }
Select-String -Pattern 'data/.encryption_key' -Path .gitignore
```
**SUCCESS**: First command fails (file not tracked) and second command shows the file is in .gitignore
**FAILURE**: If verification fails, check if file is still in git and/or .gitignore manually.

### 4.7. Update Secure Config Manager

**PRE-CHECK**: Run:
```powershell
Test-Path src/the_aichemist_codex/infrastructure/config/security/secure_config.py
```
**FAILURE**: If file doesn't exist, skip this step and move to 4.8.

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
ruff check src/the_aichemist_codex/infrastructure/config/security/secure_config.py
```
**SUCCESS**: No critical errors (warnings are acceptable)
**FAILURE**: If critical errors occur, fix them manually.

### 4.8. Update README with Encryption Key Information

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
Select-String -Pattern 'AICHEMIST_ENCRYPTION_KEY' -Path README.md,docs/README.md,docs/index.md -SimpleMatch -Context 0,10
```
**SUCCESS**: Output shows encryption key information was added to a README file
**FAILURE**: If information wasn't added, add it manually to the appropriate README file.

### 4.9. Fix MyPy Configuration

```powershell
Copy-Item pyproject.toml pyproject.toml.bak -Force
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
Select-String -Pattern 'ignore_missing_imports' -Path pyproject.toml
```
**SUCCESS**: Output shows the line is commented out or not found
**FAILURE**: If the line still exists and is not commented out, edit the file manually.

### 4.10. Run MyPy and Fix Missing Type Imports

```powershell
mypy . --no-incremental > mypy_errors.txt 2>&1; if ($LASTEXITCODE -ne 0) { Write-Output 'MyPy found errors (expected)' }

# (No change: Python script creation remains the same)
cat > analyze_mypy_errors.py << 'EOL'
# ... existing code ...
EOL

python analyze_mypy_errors.py
Remove-Item analyze_mypy_errors.py
```

**IMPORTANT**: Based on the output:
1. Add any suggested `types-*` packages to your `pyproject.toml` under `[project.optional-dependencies.dev]`.
2. For imports without available typing packages, add `# type: ignore[import]` to the specific import line causing the error.

```powershell
uv sync --dev  # Install new type packages
```

### 4.11. Improve Docstrings with Ruff

```powershell
Copy-Item pyproject.toml pyproject.toml.bak2 -Force
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
Select-String -Pattern '"D' -Path pyproject.toml -Context 0,20
```
**SUCCESS**: Output shows docstring rules are included
**FAILURE**: If docstring rules aren't found, edit the file manually.

### 4.12. Check Python Version Requirement

```powershell
Select-String -Pattern 'requires-python' -Path pyproject.toml
```

**IMPORTANT**: Evaluate if Python 3.13 is actually required. If not, adjust the version:

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

**VERIFICATION**: Run:
```powershell
Select-String -Pattern 'requires-python' -Path pyproject.toml
```
**SUCCESS**: Version requirement is appropriate (3.13 if features are used, 3.11 if not)
**FAILURE**: If version doesn't match your needs, edit manually.

### 4.13. Apply Format and Lint Fixes

```powershell
ruff format . --fix
ruff check . --fix
```

**VERIFICATION**: Run:
```powershell
ruff check . --select D1,E
```
**NOTE**: There will likely still be docstring issues, but code should be well-formatted.

---

### 5.1. Remove 'backend' References in Documentation

```powershell
# (No change: Python script creation remains the same)
cat > update_docs.py << 'EOL'
# ... existing code ...
EOL

python update_docs.py
Remove-Item update_docs.py
```

### 5.2. Update Architecture Overview in README

```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

### 5.3. Create or Update Application Layer Documentation

```powershell
New-Item -Path docs/architecture -ItemType Directory -Force
```

```powershell
# (No change: Python script creation remains the same)
cat > docs/architecture/application_layer.rst << 'EOL'
# ... existing code ...
EOL
```

### 5.4. Update Infrastructure Layer Documentation

```powershell
# (No change: Python script creation remains the same)
cat > docs/architecture/infrastructure_layer.rst << 'EOL'
# ... existing code ...
EOL
```

### 5.5. Update Interfaces Layer Documentation

```powershell
# (No change: Python script creation remains the same)
cat > docs/architecture/interfaces_layer.rst << 'EOL'
# ... existing code ...
EOL
```

### 5.6. Update Architecture Overview

```powershell
# (No change: Python script creation remains the same)
cat > docs/architecture/overview.rst << 'EOL'
# ... existing code ...
EOL
```

### 5.7. Update Architecture Diagrams

```powershell
Get-ChildItem -Path docs -Recurse -Include *.mmd,*.md,*.rst | Select-String -Pattern '```mermaid' | Select-Object -ExpandProperty Path -Unique
```

**MANUAL STEP**: For each diagram file found, you must manually update the diagrams to reflect the new architecture (replacing "backend" with "infrastructure", adding "application", etc.). This requires visual inspection of the current diagrams.

### 5.8. Generate API Documentation

**PRE-CHECK**: Check if the documentation build script exists:

```powershell
Test-Path docs/scripts/build_docs.py; if (-not $?) { Write-Output 'Documentation build script not found' }
```

**If build script exists**:
```powershell
python docs/scripts/build_docs.py --clean
```

**If build script doesn't exist**:
```powershell
New-Item -Path docs/scripts -ItemType Directory -Force
# (No change: Python script creation remains the same)
cat > docs/scripts/build_docs.py << 'EOL'
# ... existing code ...
EOL

Set-ItemProperty -Path docs/scripts/build_docs.py -Name IsReadOnly -Value $false
python docs/scripts/build_docs.py --clean
```

**VERIFICATION**: Check if the docs built successfully:

```powershell
Test-Path docs/_build/html; if ($?) { Write-Output 'Documentation built successfully' } else { Write-Output 'Documentation build failed' }
```
**FAILURE**: If build fails, check error messages and fix issues in documentation files.

### 5.9. Update Refactoring Plan Document

**PRE-CHECK**: Check if the document exists:

```powershell
Test-Path docs/documentation_refactoring_plan.md; if (-not $?) { Write-Output 'Refactoring plan document not found' }
```

**If document exists**:
```powershell
# (No change: Python script creation remains the same)
cat > temp_script.py << 'EOL'
# ... existing code ...
EOL

python temp_script.py
Remove-Item temp_script.py
```

### 5.10. Commit Documentation Changes

```powershell
git add docs/ README.md
git commit -m "docs: Update architecture documentation and remove backend references"
```

**VERIFICATION**: Run:
```powershell
git show | Select-String -Pattern 'docs:' -Context 3
```
**SUCCESS**: Output shows the documentation update commit
**FAILURE**: If verification fails, check git status and try committing again.

---

## Phase 6: Final Testing & Review

### 6.1. Run Full Test Suite

```powershell
pytest
```

**VERIFICATION**: Record the test results (number of passed/failed tests).
**FAILURE**: Note any test failures for later fixing.

### 6.2. Run Full Lint Check

```powershell
ruff check .
```

**VERIFICATION**: Record the lint errors count.
**FAILURE**: Fix any critical errors before proceeding.

### 6.3. Run Format Check

```powershell
ruff format . --check
```

**VERIFICATION**: Record any files that would be reformatted.
**FAILURE**: Run `ruff format .` to fix formatting before proceeding.

### 6.4. Run Full Type Check

```powershell
mypy .
```

**VERIFICATION**: Record the type error count.
**FAILURE**: Fix any critical type errors before proceeding.

### 6.5. Manual Testing of CLI Commands

**PRE-CHECK**: Determine the CLI command name:

```powershell
Select-String -Pattern 'def cli_app' -Path src/the_aichemist_codex/**/*.py -Recurse
```

**NOTE**: Replace `aichemist` in the commands below with the actual CLI command name determined from the grep result.

```powershell
# Test configuration command
python -m the_aichemist_codex config list

# Test version command
python -m the_aichemist_codex version

# If artifacts exist, list them
python -m the_aichemist_codex artifacts list; if ($LASTEXITCODE -ne 0) { Write-Output 'No artifacts found (expected if database is empty)' }

# If a Python file exists, analyze it
Get-ChildItem -Path src -Recurse -Include *.py | Select-Object -First 1 | ForEach-Object { python -m the_aichemist_codex analysis analyze-file $_.FullName }; if ($LASTEXITCODE -ne 0) { Write-Output 'Analysis failed (needs investigation)' }

# If search index exists, search for a term
python -m the_aichemist_codex search files "python"; if ($LASTEXITCODE -ne 0) { Write-Output 'Search failed (may need to build index first)' }

# If tags exist, list them
python -m the_aichemist_codex tag list --all; if ($LASTEXITCODE -ne 0) { Write-Output 'No tags found (expected if database is empty)' }
```

**VERIFICATION**: For each command that runs, verify the output makes sense and doesn't show unexpected errors.
**FAILURE**: For any command that fails unexpectedly, investigate and fix before proceeding.

### 6.6. Final Commit

```powershell
git add .
git commit -m "refactor: Complete Clean Architecture alignment and fixes"
```

**VERIFICATION**: Run:
```powershell
git log -1 --pretty=format:"%s"
```
**SUCCESS**: Output should be "refactor: Complete Clean Architecture alignment and fixes"
**FAILURE**: If verification fails, check git status and try committing again.

### 6.7. Generate Summary Report

```powershell
# (No change: Python script creation remains the same)
cat > refactoring_summary.md << 'EOL'
# ... existing code ...
EOL

# Fill in the test results
(Get-Content refactoring_summary.md) -replace '\[FILL IN PASS/FAIL COUNT\]', "$(pytest --collect-only -q | Measure-Object | %{$_.Count}) tests, results from step 6.1" | Set-Content refactoring_summary.md
(Get-Content refactoring_summary.md) -replace '\[FILL IN ERROR COUNT\]', 'Results from step 6.2' | Set-Content refactoring_summary.md
(Get-Content refactoring_summary.md) -replace '\[FILL IN ERROR COUNT\]', 'Results from step 6.4' | Set-Content refactoring_summary.md
(Get-Content refactoring_summary.md) -replace '\[FILL IN WORKING/FAILING COMMANDS\]', 'Results from step 6.5' | Set-Content refactoring_summary.md
```

**VERIFICATION**: Run:
```powershell
Get-Content refactoring_summary.md
```
**SUCCESS**: Summary report is generated with placeholders filled in
**FAILURE**: If verification fails, edit the file manually to complete the report.

### 6.8. Final Verification

```powershell
# Verify branch
git branch --show-current

# Verify commit count
git rev-list --count HEAD

# Show repository status
git status
```

**VERIFICATION**: Confirm you're on the `refactor/clean-architecture` branch with the expected number of commits.
**SUCCESS**: Repository is in a clean state with all changes committed
**FAILURE**: Add and commit any remaining changes before proceeding.

### 6.9. Report Completion

**MANUAL STEP**: Report that all refactoring steps have been completed, along with:
1. Link to the refactoring_summary.md file
2. Any significant issues encountered
3. Any steps that needed to be modified from the original plan
4. Recommendations for next steps

**NEXT STEPS FOR A MAINTAINER**:
1. Review the changes thoroughly
2. Create a pull request
3. Run CI/CD pipelines
4. Fix any remaining issues identified
5. Merge the changes to the main branch

---
