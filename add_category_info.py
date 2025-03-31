import datetime
from pathlib import Path


# ANSI color codes for output formatting
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {message} ==={Colors.END}\n")


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


# Define the target memory bank
memory_bank_path = Path("memory-bank/memory-bank")

# Category types and their descriptions
category_types = {
    "core": "Core system files essential for operation",
    "active": "Currently active and in-use files",
    "short-term": "Files relevant for current work session",
    "long-term": "Archived knowledge for reference",
    "episodic": "Records of specific events or sessions",
    "semantic": "Conceptual and domain knowledge",
    "procedural": "Process and methodology documentation",
    "creative": "Ideation and design concepts",
    "features": "Feature specifications and documentation",
    "integration": "Integration points and external systems",
    "plans": "Planning and roadmap documentation",
}

# Special directories to exclude from processing (they already have special handling)
exclude_dirs = [".git", ".cursor", "__pycache__"]


def get_category_description(folder_name):
    """Generate a description for a category based on its name."""
    folder_name = folder_name.lower()

    # Check for standard categories
    if folder_name in category_types:
        return category_types[folder_name]

    # Generate descriptions for other directories
    if "protocol" in folder_name:
        return "Protocol documentation and implementation files"
    elif "tool" in folder_name:
        return "Tools and utilities for system operation"
    elif "analytics" in folder_name:
        return "Analytics and reporting components"
    elif "metadata" in folder_name:
        return "Metadata about the memory system"
    elif "config" in folder_name:
        return "Configuration files and settings"
    elif "template" in folder_name:
        return "Template files for system use"
    else:
        # Capitalize the first letter of each word and add generic description
        capitalized = " ".join(word.capitalize() for word in folder_name.split("-"))
        return f"{capitalized} related documentation and resources"


def get_category_type(folder_name):
    """Determine the category type based on the folder name."""
    folder_name = folder_name.lower()

    if folder_name in ["active", "short-term", "long-term"]:
        return "Memory"
    elif folder_name in ["episodic", "semantic", "procedural", "creative"]:
        return "Cognitive"
    elif folder_name in ["features", "integration", "plans"]:
        return "Project"
    else:
        return "Standard"


def create_category_info_file(directory):
    """Create a .category_info.md file in the given directory."""
    folder_name = directory.name
    category_info_path = directory / ".category_info.md"

    # Skip if the file already exists
    if category_info_path.exists():
        return False

    # Generate metadata
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    category_type = get_category_type(folder_name)

    # Create the category title (capitalize words and remove hyphens)
    category_title = " ".join(
        word.capitalize() for word in folder_name.replace("-", " ").split()
    )

    # Generate the content
    content = f"""# {category_title} Category

{get_category_description(folder_name)}

## Contents

Files in this category contain information related to {folder_name.lower()}.

## Metadata

* Created: {now}
* Last Updated: {now}
* Category Type: {category_type}
"""

    # Write the file
    try:
        with open(category_info_path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        print_error(f"Failed to create {category_info_path}: {str(e)}")
        return False


def process_directory(directory, recursive=True):
    """Process a directory to add .category_info.md files."""
    directory = Path(directory)

    # Skip excluded directories
    if directory.name in exclude_dirs:
        return 0

    # Skip hidden directories (starting with .)
    if directory.name.startswith(".") and directory.name != ".category_info.md":
        return 0

    # Create the category info file for this directory
    created = create_category_info_file(directory)
    count = 1 if created else 0

    if created:
        print_success(
            f"Created category info for: {directory.relative_to(memory_bank_path.parent)}"
        )

    # Process subdirectories if recursive
    if recursive:
        for item in directory.glob("*"):
            if item.is_dir():
                count += process_directory(item)

    return count


def main():
    print_header("BIG BRAIN CATEGORY INFO GENERATOR")
    print(f"Adding .category_info.md files to memory bank at: {memory_bank_path}")

    if not memory_bank_path.exists():
        print_error(f"Memory bank directory not found: {memory_bank_path}")
        return

    # Keep track of created files
    created_count = 0

    # Process the root directory
    created_count += process_directory(memory_bank_path)

    print_header("GENERATION COMPLETE")
    print(f"Created {created_count} .category_info.md files")

    if created_count > 0:
        print_success("Successfully implemented memory rule for category info files.")
    else:
        print_warning(
            "No new category info files were created. All directories may already have them."
        )


if __name__ == "__main__":
    main()
