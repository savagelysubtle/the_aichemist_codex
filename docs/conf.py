# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup and mocking configuration -------------------------------------
import os
import sys
from unittest.mock import MagicMock

# Add the project root and src directories to the Python path
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../src"))


# Define a smarter mock class that avoids recursion issues
class BetterMock(MagicMock):
    """A smarter mock class that prevents recursion and circular imports."""

    _recursion_depth = 0
    _max_recursion = 5  # Limit recursion to avoid infinite loops

    @classmethod
    def __getattr__(cls, name):
        # Prevent recursion by tracking depth
        cls._recursion_depth += 1
        if cls._recursion_depth > cls._max_recursion:
            cls._recursion_depth = 0
            return MagicMock()

        result = MagicMock()
        cls._recursion_depth = 0
        return result


# List of modules to mock for autodoc
MOCK_MODULES = [
    # External libraries
    "rapidfuzz",
    "whoosh",
    "faiss",
    "faiss_cpu",
    "numpy",
    "transformers",
    "sklearn",
    "pandas",
    "sentence_transformers",
    "torch",
    "nltk",
    "sklearn.metrics",
    # Add any other external libraries your code imports
]

# Set up autodoc_mock_imports for simple external dependencies
autodoc_mock_imports = MOCK_MODULES

# Specific modules that cause circular imports
CIRCULAR_MODULES = [
    # Core modules
    "the_aichemist_codex.backend.core.interfaces",
    "the_aichemist_codex.backend.core.models",
    "the_aichemist_codex.backend.core.constants",
    "the_aichemist_codex.backend.core.exceptions",
    "the_aichemist_codex.backend.core.utils",
    # Domain modules
    "the_aichemist_codex.backend.domain.file_reader",
    "the_aichemist_codex.backend.domain.file_writer",
    "the_aichemist_codex.backend.domain.file_manager",
    "the_aichemist_codex.backend.domain.search",
    "the_aichemist_codex.backend.domain.metadata",
    "the_aichemist_codex.backend.domain.relationships",
    # Infrastructure modules
    "the_aichemist_codex.backend.infrastructure.config",
    "the_aichemist_codex.backend.infrastructure.paths",
    # Registry
    "the_aichemist_codex.backend.registry",
]

# Apply mocks to specific modules that cause circular imports
for mod_name in CIRCULAR_MODULES:
    sys.modules[mod_name] = BetterMock()
    # Also mock submodules to avoid import errors
    parts = mod_name.split(".")
    for i in range(1, len(parts)):
        parent_mod = ".".join(parts[:i])
        if parent_mod not in sys.modules:
            sys.modules[parent_mod] = BetterMock()

print("Using autodoc with mocking for circular imports and external dependencies.")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "The Aichemist Codex"
copyright_text = "2025, Steve Oatman"  # Renamed to avoid shadowing Python's copyright
author = "Steve Oatman"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # List other extensions before and after as needed
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    # Disable this extension which causes problems with MagicMock objects
    # "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
]

# Enable autosummary
autosummary_generate = True  # Generate stub files
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "ignore-module-all": False,  # Use __all__ if defined to determine what to document
    "imported-members": True,
    "special-members": "__init__",  # Document initialization methods
    "private-members": False,  # Don't document private members by default
    "member-order": "groupwise",  # Group members by type
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Don't warn about missing references - will help with mocked modules
nitpicky = False

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The suffix(es) of source filenames.
source_suffix = [".rst"]

# If myst_parser is available, enable markdown support
try:
    import importlib.util

    if importlib.util.find_spec("myst_parser"):
        source_suffix.append(".md")
        extensions.append("myst_parser")
        print("Markdown support enabled via myst_parser")
    else:
        print(
            "Warning: myst_parser not available. Markdown support limited to RST only."
        )
except ImportError:
    print(
        "Warning: importlib.util not available. Markdown support limited to RST only."
    )

# Define the master document
master_doc = "index"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# Theme configuration
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#32cd32",
        "color-brand-content": "#32cd32",
        "color-background-secondary": "#f8f9fa",
        "color-background-hover": "#ebedef",
        "color-link": "#1d8311",
        "color-link-hover": "#32cd32",
        "color-sidebar-link-text": "#2b2b2b",
        "color-sidebar-link-text--top-level": "#262626",
        "color-sidebar-item-background--current": "#e3ffe3",
        "color-sidebar-item-background--hover": "#f0f8f0",
        "color-foreground-secondary": "#363636",
        "color-foreground-muted": "#646464",
        "color-foreground-border": "#d0d0d0",
        "color-inline-code-background": "#f5f5f5",
        "color-highlighted-background": "#fdffe2",
        "color-api-background": "#f5f7f9",
        "color-api-border": "#e1e4e5",
    },
    "dark_css_variables": {
        "color-brand-primary": "#32cd32",
        "color-brand-content": "#32cd32",
        "color-background-primary": "#131313",
        "color-background-secondary": "#1a1a1a",
        "color-background-hover": "#292929",
        "color-link": "#5fff5f",
        "color-link-hover": "#32cd32",
        "color-sidebar-background": "#1a1a1a",
        "color-sidebar-link-text": "#bebebe",
        "color-sidebar-link-text--top-level": "#e0e0e0",
        "color-sidebar-item-background--current": "#0f3b0f",
        "color-sidebar-item-background--hover": "#1f2f1f",
        "color-foreground-primary": "#e0e0e0",
        "color-foreground-secondary": "#bebebe",
        "color-foreground-muted": "#949494",
        "color-foreground-border": "#4c4c4c",
        "color-inline-code-background": "#2b2b2b",
        "color-highlighted-background": "#262410",
        "color-api-background": "#1a1a1a",
        "color-api-border": "#303030",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/your-username/the-aichemist-codex",
            # Split SVG into multiple lines to avoid line length issues
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0"
                     viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53
                    5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23
                    -.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87
                    2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                    -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
                    1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
                    1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
                    1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z">
                    </path>
                </svg>
            """,
        },
    ],
}

# Use landing page template for the index page
html_additional_pages = {
    "index": "landing.html",
}

html_title = "The Aichemist Codex"
html_favicon = "_static/favicon.svg"
html_logo = "_static/logo-lime.svg"
html_show_sourcelink = False
html_copy_source = False

# -- Extension configuration -------------------------------------------------
autoclass_content = "both"  # Use both class and __init__ docstrings
autodoc_member_order = "groupwise"
autodoc_typehints = "description"  # Put typehints in descriptions to avoid issues

# -- Options for HTML help output -------------------------------------------------
htmlhelp_basename = "TheAichemistCodexdoc"

# -- Options for LaTeX output -------------------------------------------------
latex_elements: dict = {}

latex_documents = [
    (
        master_doc,
        "TheAichemistCodex.tex",
        "The Aichemist Codex Documentation",
        "Steve Oatman",
        "manual",
    ),
]

# -- Intersphinx configuration -------------------------------------------------
# Configure external documentation references
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "sklearn": ("https://scikit-learn.org/stable/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}

# Configure intersphinx settings
intersphinx_cache_limit = 5  # days to cache
intersphinx_timeout = 30  # seconds for timeout

# -- Autodoc-typehints configuration -----------------------------------------
# Settings for sphinx-autodoc-typehints extension (if re-enabled)
set_type_checking_flag = True
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# Make autodoc warnings non-fatal
autodoc_warningiserror = False
