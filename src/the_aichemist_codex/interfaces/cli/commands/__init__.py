"""Command modules for the AIchemist Codex CLI."""

# Import command modules so they can be imported from the package
try:
    from . import (
        analysis,
        artifacts,
        config,
        fs,
        ingest,
        memory,
        relationships,
        search,
        tagging,
        version,
    )
except ImportError:
    # During development, some modules might not exist yet
    pass
