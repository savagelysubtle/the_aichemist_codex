"""Global configuration settings for The Aichemist Codex."""

from pathlib import Path

# Define base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
EXPORT_DIR = DATA_DIR / "exports"
CACHE_DIR = DATA_DIR / "cache"

# File settings
DEFAULT_JSON_INDENT = 4
DEFAULT_IGNORE_PATTERNS: list[str] = [
    # Python
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    ".pytest_cache",
    ".coverage",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "poetry.lock",
    "Pipfile.lock",
    # JavaScript/Node
    "node_modules",
    "bower_components",
    "package-lock.json",
    "yarn.lock",
    ".npm",
    ".yarn",
    ".pnpm-store",
    # Java
    "*.class",
    "*.jar",
    "*.war",
    "*.ear",
    "*.nar",
    "target/",
    ".gradle/",
    "build/",
    ".settings/",
    ".project",
    ".classpath",
    "gradle-app.setting",
    "*.gradle",
    # C/C++
    "*.o",
    "*.obj",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.exe",
    "*.lib",
    "*.out",
    "*.a",
    "*.pdb",
    # Swift/Xcode
    ".build/",
    "*.xcodeproj/",
    "*.xcworkspace/",
    "*.pbxuser",
    "*.mode1v3",
    "*.mode2v3",
    "*.perspectivev3",
    "*.xcuserstate",
    "xcuserdata/",
    ".swiftpm/",
    # Ruby
    "*.gem",
    ".bundle/",
    "vendor/bundle",
    "Gemfile.lock",
    ".ruby-version",
    ".ruby-gemset",
    ".rvmrc",
    # Rust
    "target/",
    "Cargo.lock",
    "**/*.rs.bk",
    # Go
    "bin/",
    "pkg/",
    # .NET/C#
    "bin/",
    "obj/",
    "*.suo",
    "*.user",
    "*.userosscache",
    "*.sln.docstates",
    "packages/",
    "*.nupkg",
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    # Images and media
    "*.svg",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.pdf",
    "*.mov",
    "*.mp4",
    "*.mp3",
    "*.wav",
    # Virtual environments
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    # IDEs and editors
    ".idea",
    ".vscode",
    ".vs",
    "*.swp",
    "*.swo",
    "*.swn",
    ".settings",
    ".project",
    ".classpath",
    "*.sublime-*",
    # Temporary and cache files
    "*.log",
    "*.bak",
    "*.swp",
    "*.tmp",
    "*.temp",
    ".cache",
    ".sass-cache",
    ".eslintcache",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    # Build directories and artifacts
    "build",
    "dist",
    "target",
    "out",
    "*.egg-info",
    "*.egg",
    "*.whl",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.class",
    # Documentation
    "site-packages",
    ".docusaurus",
    ".next",
    ".nuxt",
    # Other common patterns
    ## Minified files
    "*.min.js",
    "*.min.css",
    ## Source maps
    "*.map",
    ## Terraform
    ".terraform",
    "*.tfstate*",
    ## Dependencies in various languages
    "vendor/",
]


# Application Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB file limit
MAX_TOKENS = 8000  # Token limit for analysis
