# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile autodoc clean

# Generate API documentation
autodoc:
	@echo "Generating API documentation..."
	@python scripts/generate_api_docs.py

# Run the full build script
docsbuild:
	@echo "Building documentation using build_docs.py..."
	@python scripts/build_docs.py --clean

# Clean the build directory and generated API files
clean:
	@echo "Cleaning build directory..."
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Removing generated API directory contents..."
	@rm -rf $(SOURCEDIR)/api 2>/dev/null || true
	@echo "Removing any misplaced generated API files in scripts..."
	@rm -rf $(SOURCEDIR)/scripts/api 2>/dev/null || true

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
