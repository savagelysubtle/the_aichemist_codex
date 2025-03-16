# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the backend/src directory to the Python path
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../backend/src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "The Aichemist Codex"
copyright = "2025, Steve Oatman"
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
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

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
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
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
# autoclass_content = 'both'
autodoc_member_order = "groupwise"
autodoc_typehints = "description"
autoclass_content = "both"

# -- Options for HTML help output -------------------------------------------------
htmlhelp_basename = "TheAichemistCodexdoc"

# -- Options for LaTeX output -------------------------------------------------
latex_elements = {}

latex_documents = [
    (
        master_doc,
        "TheAichemistCodex.tex",
        "The Aichemist Codex Documentation",
        "Steve Oatman",
        "manual",
    ),
]
