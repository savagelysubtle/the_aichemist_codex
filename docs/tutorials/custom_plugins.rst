Custom Plugins Tutorial
===================

This tutorial guides you through creating custom plugins for The Aichemist Codex to extend its functionality in specialized ways. Plugins allow you to add new features, integrate with external services, or modify the behavior of existing components.

Understanding the Plugin System
----------------------------

The Aichemist Codex uses a modular plugin architecture that allows you to:

- Create new commands for the CLI
- Add custom file processors for specific file types
- Implement custom tagging algorithms
- Create custom search methods
- Integrate with external services and APIs
- Add custom visualization tools
- Implement custom organization rules

Plugins are Python modules that follow a specific structure and implement defined interfaces to hook into The Aichemist Codex's extension points.

Getting Started
------------

To create a plugin, you'll need:

1. A development installation of The Aichemist Codex
2. Understanding of Python async programming (asyncio)
3. Familiarity with The Aichemist Codex's core concepts

Install the development version of the package:

.. code-block:: bash

   pip install the-aichemist-codex[dev]

Plugin Structure
-------------

A basic plugin consists of:

1. A plugin class that inherits from `CodexPlugin`
2. A plugin manifest (JSON or YAML)
3. Registration with the plugin registry

Here's a minimal plugin structure:

.. code-block:: python

   # my_plugin.py
   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin

   class MyCustomPlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="my_custom_plugin",
               version="0.1.0",
               description="A custom plugin for The Aichemist Codex"
           )

       async def initialize(self):
           """Called when the plugin is loaded."""
           self.logger.info("My Custom Plugin initialized")
           return True

       async def shutdown(self):
           """Called when the plugin is unloaded."""
           self.logger.info("My Custom Plugin shutting down")

   # Register the plugin
   register_plugin(MyCustomPlugin)

Creating Your First Plugin
-----------------------

Let's create a simple plugin that adds a custom command to the CLI.

**Step 1**: Create a new directory for your plugin

.. code-block:: bash

   mkdir -p ~/my_codex_plugins/hello_world

**Step 2**: Create the plugin file structure

.. code-block:: bash

   touch ~/my_codex_plugins/hello_world/__init__.py
   touch ~/my_codex_plugins/hello_world/plugin.py
   touch ~/my_codex_plugins/hello_world/manifest.json

**Step 3**: Create a simple CLI command plugin

.. code-block:: python

   # ~/my_codex_plugins/hello_world/plugin.py
   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.cli.commands import Command

   class HelloWorldCommand(Command):
       name = "hello"
       help = "Displays a friendly greeting"

       def add_arguments(self, parser):
           parser.add_argument("--name", default="world", help="The name to greet")

       async def execute(self, args):
           print(f"Hello, {args.name}!")
           print(f"Welcome to The Aichemist Codex!")
           return 0  # Success exit code

   class HelloWorldPlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="hello_world",
               version="0.1.0",
               description="A plugin that adds a friendly greeting command"
           )
           self.commands = []

       async def initialize(self):
           # Register our command
           self.commands.append(HelloWorldCommand())

           # Register commands with the CLI
           cli = self.codex.get_component("cli")
           if cli:
               for command in self.commands:
                   cli.register_command(command)

           self.logger.info("Hello World plugin initialized")
           return True

       async def shutdown(self):
           # Unregister commands
           cli = self.codex.get_component("cli")
           if cli:
               for command in self.commands:
                   cli.unregister_command(command.name)

           self.logger.info("Hello World plugin shutting down")

   # Import this in __init__.py
   register_plugin(HelloWorldPlugin)

**Step 4**: Create the plugin manifest

.. code-block:: json

   {
     "name": "hello_world",
     "version": "0.1.0",
     "description": "A plugin that adds a friendly greeting command",
     "author": "Your Name",
     "email": "your.email@example.com",
     "requires": {
       "the_aichemist_codex": ">=0.1.0"
     },
     "entry_point": "hello_world.plugin"
   }

**Step 5**: Create the __init__.py file

.. code-block:: python

   # ~/my_codex_plugins/hello_world/__init__.py
   from .plugin import HelloWorldPlugin, register_plugin

**Step 6**: Install the plugin

.. code-block:: bash

   cd ~/my_codex_plugins/hello_world
   pip install -e .

**Step 7**: Test the plugin

.. code-block:: bash

   # Basic usage
   codex hello

   # With a parameter
   codex hello --name "Developer"

Plugin Integration Points
----------------------

The Aichemist Codex offers several integration points for plugins:

1. **CLI Commands**: Add new commands to the command-line interface
2. **File Processors**: Handle specific file types or processing steps
3. **Tagging Providers**: Implement custom tagging algorithms
4. **Search Providers**: Add custom search methods
5. **Content Analyzers**: Extract information from content
6. **Organization Rules**: Implement custom organization strategies
7. **External Integrations**: Connect to external services

Creating a File Processor Plugin
----------------------------

Let's create a plugin that handles a custom file type:

.. code-block:: python

   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.processing import FileProcessor

   class CustomFileProcessor(FileProcessor):
       """Processes .custom files with a specific format"""

       supported_extensions = [".custom"]

       async def can_process(self, file_path):
           """Check if this processor can handle the file"""
           return file_path.suffix.lower() in self.supported_extensions

       async def extract_text(self, file_path):
           """Extract text content from the file"""
           try:
               with open(file_path, 'r', encoding='utf-8') as f:
                   content = f.read()
                   # Process the custom format here
                   # This is just an example - modify for your format
                   if content.startswith("CUSTOM:"):
                       # Extract the text part
                       text_content = content.split("CONTENT:", 1)[1].strip()
                       return text_content
                   return content
           except Exception as e:
               self.logger.error(f"Error extracting text: {e}")
               return ""

       async def extract_metadata(self, file_path):
           """Extract metadata from the file"""
           metadata = {}
           try:
               with open(file_path, 'r', encoding='utf-8') as f:
                   content = f.read()
                   if "META:" in content:
                       meta_section = content.split("META:", 1)[1].split("CONTENT:", 1)[0]
                       for line in meta_section.strip().split("\n"):
                           if ":" in line:
                               key, value = line.split(":", 1)
                               metadata[key.strip()] = value.strip()
           except Exception as e:
               self.logger.error(f"Error extracting metadata: {e}")

           return metadata

   class CustomFilePlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="custom_file_plugin",
               version="0.1.0",
               description="Plugin for processing .custom files"
           )
           self.processor = None

       async def initialize(self):
           # Create and register the processor
           self.processor = CustomFileProcessor()

           # Register with the processing manager
           processing_mgr = self.codex.get_component("processing_manager")
           if processing_mgr:
               processing_mgr.register_processor(self.processor)
               self.logger.info(f"Registered processor for {self.processor.supported_extensions}")
           else:
               self.logger.warning("Processing manager not found")

           return True

       async def shutdown(self):
           # Unregister the processor
           processing_mgr = self.codex.get_component("processing_manager")
           if processing_mgr and self.processor:
               processing_mgr.unregister_processor(self.processor)

           self.logger.info("Custom file plugin shutting down")

   register_plugin(CustomFilePlugin)

Creating a Custom Tagging Provider
-------------------------------

This plugin implements a custom tagging algorithm:

.. code-block:: python

   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.tagging import TagProvider, TagSuggestion

   class KeyphraseTagProvider(TagProvider):
       """Suggests tags based on key phrases in the document"""

       name = "keyphrase_tagger"

       def __init__(self):
           super().__init__()
           # Define key phrases and associated tags
           self.keyphrase_map = {
               "machine learning": ["machine-learning", "ai"],
               "deep learning": ["deep-learning", "neural-networks", "ai"],
               "neural network": ["neural-networks", "deep-learning"],
               "data analysis": ["data-analysis", "statistics"],
               "quantum computing": ["quantum-computing", "quantum"],
               "blockchain": ["blockchain", "cryptocurrency"],
               # Add more mappings as needed
           }

       async def suggest_tags(self, file_path, content=None, metadata=None, **kwargs):
           """Suggest tags based on key phrases in the content"""
           suggestions = []

           # If no content provided, try to read it
           if content is None and file_path:
               try:
                   with open(file_path, 'r', encoding='utf-8') as f:
                       content = f.read()
               except Exception as e:
                   self.logger.error(f"Error reading file: {e}")
                   return []

           if not content:
               return []

           content = content.lower()

           # Count occurrences of key phrases
           for phrase, tags in self.keyphrase_map.items():
               count = content.count(phrase)

               if count > 0:
                   # Calculate score based on frequency
                   score = min(0.95, 0.5 + (count * 0.05))

                   # Add suggestions for each associated tag
                   for tag in tags:
                       suggestions.append(
                           TagSuggestion(
                               tag=tag,
                               confidence=score,
                               source=self.name,
                               metadata={
                                   "phrase": phrase,
                                   "occurrences": count
                               }
                           )
                       )

           # Sort by confidence (highest first)
           suggestions.sort(key=lambda s: s.confidence, reverse=True)

           return suggestions

   class KeyphraseTagPlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="keyphrase_tag_plugin",
               version="0.1.0",
               description="Plugin for tagging based on key phrases"
           )
           self.provider = None

       async def initialize(self):
           # Create and register the tag provider
           self.provider = KeyphraseTagProvider()

           # Register with the tag manager
           tag_mgr = self.codex.get_component("tag_manager")
           if tag_mgr:
               tag_mgr.register_provider(self.provider)
               self.logger.info(f"Registered tag provider: {self.provider.name}")
           else:
               self.logger.warning("Tag manager not found")

           return True

       async def shutdown(self):
           # Unregister the provider
           tag_mgr = self.codex.get_component("tag_manager")
           if tag_mgr and self.provider:
               tag_mgr.unregister_provider(self.provider.name)

           self.logger.info("Keyphrase tag plugin shutting down")

   register_plugin(KeyphraseTagPlugin)

Creating a Visualization Plugin
----------------------------

This plugin adds a custom visualization for document relationships:

.. code-block:: python

   import os
   import tempfile
   import networkx as nx
   import matplotlib.pyplot as plt

   from pathlib import Path
   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.cli.commands import Command

   class VisualizeRelationshipsCommand(Command):
       name = "visualize-relationships"
       help = "Visualizes relationships between documents"

       def add_arguments(self, parser):
           parser.add_argument("--output", help="Output file path for the visualization")
           parser.add_argument("--min-similarity", type=float, default=0.7,
                           help="Minimum similarity score to consider (0.0-1.0)")
           parser.add_argument("--max-documents", type=int, default=50,
                           help="Maximum number of documents to include")
           parser.add_argument("--tag-filter", help="Only include documents with this tag")

       async def execute(self, args):
           print("Generating document relationship visualization...")

           # Get access to codex components
           search_engine = self.plugin.codex.get_component("search_engine")
           file_manager = self.plugin.codex.get_component("file_manager")

           if not search_engine or not file_manager:
               print("Error: Required components not available")
               return 1

           # Get files to analyze
           files = await file_manager.list_files()

           if args.tag_filter:
               tag_manager = self.plugin.codex.get_component("tag_manager")
               if tag_manager:
                   files_with_tag = await tag_manager.find_files_with_tags([args.tag_filter])
                   files = [f for f in files if f.id in files_with_tag]

           # Limit the number of files
           files = files[:args.max_documents]

           if not files:
               print("No files found matching criteria")
               return 1

           print(f"Analyzing relationships between {len(files)} documents...")

           # Create a graph
           G = nx.Graph()

           # Add nodes for each file
           for file in files:
               G.add_node(file.id, label=file.name)

           # Calculate similarities and add edges
           for i, file1 in enumerate(files):
               print(f"Processing file {i+1}/{len(files)}: {file1.name}")

               # Get related documents
               similar_docs = await search_engine.find_similar(
                   file1.path,
                   threshold=args.min_similarity,
                   limit=args.max_documents
               )

               # Add edges for similar documents
               for doc, score in similar_docs:
                   # Find the file ID for this path
                   for file2 in files:
                       if file2.path == doc:
                           # Add edge with similarity weight
                           G.add_edge(file1.id, file2.id, weight=score)
                           break

           # Create the visualization
           plt.figure(figsize=(12, 9))

           # Use different layouts depending on graph size
           if len(files) < 20:
               pos = nx.spring_layout(G, seed=42)
           else:
               pos = nx.kamada_kawai_layout(G)

           # Draw nodes and edges
           nx.draw_networkx_nodes(G, pos, node_size=500, alpha=0.8)

           # Edge weights as colors
           edges = G.edges()
           weights = [G[u][v]['weight'] for u, v in edges]

           nx.draw_networkx_edges(G, pos, width=weights, alpha=0.5,
                               edge_color=weights, edge_cmap=plt.cm.Blues)

           # Draw labels
           labels = {node: G.nodes[node]['label'] for node in G.nodes()}
           nx.draw_networkx_labels(G, pos, labels, font_size=8)

           plt.title("Document Relationship Network")
           plt.axis('off')

           # Save or show the visualization
           if args.output:
               output_path = args.output
           else:
               # Create a temporary file
               with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                   output_path = tmp.name

           plt.savefig(output_path, bbox_inches='tight')
           plt.close()

           print(f"Visualization saved to: {output_path}")

           # Open the file if we're not on a headless system
           if os.name == 'nt':  # Windows
               os.startfile(output_path)
           elif os.name == 'posix':  # macOS, Linux
               if 'DISPLAY' in os.environ:  # Check if we have a display
                   import subprocess
                   subprocess.call(('xdg-open', output_path))

           return 0

   class VisualizationPlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="visualization_plugin",
               version="0.1.0",
               description="Adds visualization capabilities to The Aichemist Codex"
           )
           self.commands = []

       async def initialize(self):
           try:
               import networkx
               import matplotlib
           except ImportError:
               self.logger.error("Required dependencies not found. Please install with: "
                             "pip install networkx matplotlib")
               return False

           # Set the command's plugin reference
           viz_cmd = VisualizeRelationshipsCommand()
           viz_cmd.plugin = self
           self.commands.append(viz_cmd)

           # Register commands with the CLI
           cli = self.codex.get_component("cli")
           if cli:
               for command in self.commands:
                   cli.register_command(command)

           self.logger.info("Visualization plugin initialized")
           return True

       async def shutdown(self):
           # Unregister commands
           cli = self.codex.get_component("cli")
           if cli:
               for command in self.commands:
                   cli.unregister_command(command.name)

           self.logger.info("Visualization plugin shutting down")

   register_plugin(VisualizationPlugin)

Creating an External Integration Plugin
-----------------------------------

This plugin integrates with an external API service:

.. code-block:: python

   import aiohttp
   import asyncio

   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.events import EventListener, EventType

   class ExternalAPIIntegration(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="external_api_integration",
               version="0.1.0",
               description="Integrates with ExampleAPI to enrich document metadata"
           )
           self.api_key = None
           self.api_url = "https://api.example.com/v1"
           self.session = None
           self.listener = None

       async def initialize(self):
           # Check for API key in environment or configuration
           config = self.codex.get_component("config")
           if config and hasattr(config, 'plugins') and 'external_api' in config.plugins:
               self.api_key = config.plugins['external_api'].get('api_key')
               api_url = config.plugins['external_api'].get('api_url')
               if api_url:
                   self.api_url = api_url

           if not self.api_key:
               # Try environment variables
               import os
               self.api_key = os.environ.get('EXAMPLE_API_KEY')

           if not self.api_key:
               self.logger.warning("API key not found. Integration disabled.")
               return False

           # Create HTTP session
           self.session = aiohttp.ClientSession(
               headers={"Authorization": f"Bearer {self.api_key}"}
           )

           # Set up event listener for new files
           self.listener = ExternalAPIEventListener(self)
           self.codex.register_listener(self.listener)

           self.logger.info("External API integration initialized")
           return True

       async def enrich_document(self, file_path, file_id):
           """Send document to API and get enriched metadata"""
           if not self.session:
               return None

           try:
               # Get file content
               with open(file_path, 'rb') as f:
                   file_data = f.read()

               # Call the API
               async with self.session.post(
                   f"{self.api_url}/analyze",
                   data={'file': file_data}
               ) as response:
                   if response.status == 200:
                       result = await response.json()

                       # Extract useful information
                       enriched_data = {
                           'api_processed': True,
                           'topics': result.get('topics', []),
                           'entities': result.get('entities', []),
                           'sentiment': result.get('sentiment', {})
                       }

                       # Update file metadata
                       file_manager = self.codex.get_component("file_manager")
                       if file_manager:
                           await file_manager.update_metadata(
                               file_id,
                               custom_metadata={
                                   'external_api_data': enriched_data
                               }
                           )

                       return enriched_data
                   else:
                       error_text = await response.text()
                       self.logger.error(f"API error: {response.status} - {error_text}")
                       return None
           except Exception as e:
               self.logger.error(f"Error calling external API: {e}")
               return None

       async def shutdown(self):
           # Unregister listener
           if self.listener:
               self.codex.unregister_listener(self.listener)

           # Close HTTP session
           if self.session:
               await self.session.close()

           self.logger.info("External API integration shutting down")

   class ExternalAPIEventListener(EventListener):
       def __init__(self, plugin):
           self.plugin = plugin

       async def on_event(self, event_type, data):
           if event_type == EventType.FILE_ADDED:
               # New file added - process it
               file_path = data.get('file_path')
               file_id = data.get('file_id')

               if file_path and file_id:
                   # Process in background
                   asyncio.create_task(self.plugin.enrich_document(file_path, file_id))

   register_plugin(ExternalAPIIntegration)

Packaging Plugins for Distribution
------------------------------

To package your plugin for distribution:

**Step 1**: Create a setup.py file

.. code-block:: python

   from setuptools import setup, find_packages

   setup(
       name="codex-hello-world",
       version="0.1.0",
       description="A Hello World plugin for The Aichemist Codex",
       author="Your Name",
       author_email="your.email@example.com",
       packages=find_packages(),
       install_requires=[
           "the-aichemist-codex>=0.1.0",
       ],
       entry_points={
           "codex.plugins": [
               "hello_world=hello_world.plugin:HelloWorldPlugin",
           ],
       },
       classifiers=[
           "Development Status :: 3 - Alpha",
           "Intended Audience :: Developers",
           "Programming Language :: Python :: 3",
           "Programming Language :: Python :: 3.8",
           "Programming Language :: Python :: 3.9",
       ],
   )

**Step 2**: Create a README.md

.. code-block:: markdown

   # Hello World Plugin for The Aichemist Codex

   This plugin adds a friendly greeting command to The Aichemist Codex.

   ## Installation

   ```bash
   pip install codex-hello-world
   ```

   ## Usage

   ```bash
   codex hello
   codex hello --name "Your Name"
   ```

   ## Development

   Clone the repository and install in development mode:

   ```bash
   git clone https://github.com/yourusername/codex-hello-world.git
   cd codex-hello-world
   pip install -e .
   ```

**Step 3**: Build and publish the package

.. code-block:: bash

   # Install build tools
   pip install build twine

   # Build the package
   python -m build

   # Upload to PyPI (or use TestPyPI for testing)
   twine upload dist/*

Best Practices for Plugin Development
----------------------------------

1. **Asynchronous Operation**: Use async/await for all operations that might block
2. **Error Handling**: Implement robust error handling to prevent crashes
3. **Resource Management**: Properly initialize and clean up resources
4. **Configuration**: Make your plugin configurable with sensible defaults
5. **Documentation**: Provide clear documentation for your plugin
6. **Versioning**: Use semantic versioning for your plugin
7. **Testing**: Write tests for your plugin functionality
8. **Minimal Dependencies**: Keep external dependencies to a minimum

Example: Complete Custom Analyzer Plugin
-------------------------------------

Here's a complete example of a document analyzer plugin that detects code snippets and programming languages:

.. code-block:: python

   import re
   from pathlib import Path
   from typing import Dict, List, Tuple, Optional

   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.analysis import ContentAnalyzer
   from the_aichemist_codex.backend.cli.commands import Command

   class CodeSnippetAnalyzer(ContentAnalyzer):
       """Analyzes documents for code snippets and programming languages"""

       name = "code_snippet_analyzer"

       def __init__(self):
           super().__init__()
           # Patterns for identifying programming languages
           self.language_patterns = {
               "python": [r"def\s+\w+\s*\(", r"import\s+\w+", r"class\s+\w+\s*\("],
               "javascript": [r"function\s+\w+\s*\(", r"const\s+\w+\s*=", r"let\s+\w+\s*="],
               "java": [r"public\s+class", r"private\s+\w+\s+\w+", r"public\s+static\s+void\s+main"],
               "c": [r"#include", r"int\s+main\s*\(", r"void\s+\w+\s*\("],
               "cpp": [r"#include\s+<\w+>", r"namespace\s+\w+", r"class\s+\w+\s*\{"],
               "ruby": [r"def\s+\w+", r"require\s+['\"]", r"class\s+\w+\s*<"],
               "go": [r"func\s+\w+\s*\(", r"package\s+\w+", r"import\s+\("],
               "rust": [r"fn\s+\w+\s*\(", r"let\s+mut\s+\w+", r"struct\s+\w+"],
               "php": [r"<\?php", r"function\s+\w+\s*\(", r"\$\w+\s*="],
               "html": [r"<html", r"<div", r"<body"],
               "css": [r"\.\w+\s*\{", r"#\w+\s*\{", r"@media"],
               "sql": [r"SELECT\s+\w+", r"CREATE\s+TABLE", r"INSERT\s+INTO"]
           }

           # Pattern for identifying code blocks in markdown or text
           self.code_block_pattern = re.compile(r"```(?P<language>\w*)\s*\n(?P<code>.*?)\n```", re.DOTALL)

       async def analyze_document(self, file_path: Path) -> Dict:
           """Analyze a document for code snippets"""
           result = {
               "has_code": False,
               "languages": [],
               "snippets": []
           }

           try:
               # Read the file content
               with open(file_path, 'r', encoding='utf-8') as f:
                   content = f.read()

               # Look for code blocks in markdown
               code_blocks = self.code_block_pattern.findall(content)
               if code_blocks:
                   result["has_code"] = True
                   for language, code in code_blocks:
                       language = language.strip().lower() if language else "unknown"
                       if not language and code:
                           # Try to detect language from code
                           language = self._detect_language(code)

                       if language and language not in result["languages"]:
                           result["languages"].append(language)

                       result["snippets"].append({
                           "language": language,
                           "code": code[:100] + "..." if len(code) > 100 else code,
                           "line_count": code.count('\n') + 1
                       })

               # If no code blocks, analyze the content directly
               if not result["has_code"]:
                   languages = self._detect_language(content, threshold=2)
                   if languages:
                       result["has_code"] = True
                       result["languages"] = languages

           except Exception as e:
               self.logger.error(f"Error analyzing document: {e}")

           return result

       def _detect_language(self, text: str, threshold: int = 1) -> List[str]:
           """Detect programming languages in text based on patterns"""
           languages = []

           for lang, patterns in self.language_patterns.items():
               matches = 0
               for pattern in patterns:
                   if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                       matches += 1

               if matches >= threshold:
                   languages.append(lang)

           return languages

   class CodeSnippetCommand(Command):
       name = "analyze-code"
       help = "Analyzes documents for code snippets and programming languages"

       def add_arguments(self, parser):
           parser.add_argument("files", nargs="+", help="Files to analyze")
           parser.add_argument("--tag", action="store_true",
                           help="Tag files with detected languages")

       async def execute(self, args):
           analyzer = self.plugin.analyzer

           for file_path in args.files:
               path = Path(file_path)
               if not path.exists():
                   print(f"File not found: {file_path}")
                   continue

               print(f"Analyzing {path.name}...")
               result = await analyzer.analyze_document(path)

               if result["has_code"]:
                   print(f"  Contains code: Yes")
                   print(f"  Languages detected: {', '.join(result['languages'])}")
                   print(f"  Code snippets: {len(result['snippets'])}")

                   for i, snippet in enumerate(result['snippets'], 1):
                       print(f"    Snippet {i}: {snippet['language']} ({snippet['line_count']} lines)")
               else:
                   print(f"  Contains code: No")

               # Tag the file if requested
               if args.tag and result["has_code"] and result["languages"]:
                   tag_mgr = self.plugin.codex.get_component("tag_manager")
                   if tag_mgr:
                       # Add language tags
                       for lang in result["languages"]:
                           lang_tag = f"language:{lang}"
                           # Create tag if it doesn't exist
                           if not await tag_mgr.tag_exists(lang_tag):
                               await tag_mgr.create_tag(
                                   name=lang_tag,
                                   description=f"Code in {lang} programming language"
                               )
                           # Apply tag to file
                           await tag_mgr.apply_tag(path, lang_tag)

                       # Add general code tag
                       if not await tag_mgr.tag_exists("contains:code"):
                           await tag_mgr.create_tag(
                               name="contains:code",
                               description="Contains code snippets"
                           )
                       await tag_mgr.apply_tag(path, "contains:code")

                       print(f"  Tagged file with: contains:code, {', '.join(f'language:{lang}' for lang in result['languages'])}")

           return 0

   class CodeAnalyzerPlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="code_analyzer",
               version="0.1.0",
               description="Analyzes documents for code snippets"
           )
           self.analyzer = None
           self.commands = []

       async def initialize(self):
           # Create analyzer
           self.analyzer = CodeSnippetAnalyzer()

           # Register analyzer with the analysis manager
           analysis_mgr = self.codex.get_component("analysis_manager")
           if analysis_mgr:
               analysis_mgr.register_analyzer(self.analyzer)

           # Create and register command
           cmd = CodeSnippetCommand()
           cmd.plugin = self
           self.commands.append(cmd)

           cli = self.codex.get_component("cli")
           if cli:
               for command in self.commands:
                   cli.register_command(command)

           self.logger.info("Code analyzer plugin initialized")
           return True

       async def process_file(self, file: "File"):
           """Hook into file processing pipeline"""
           if not file or not file.path.exists():
               return None

           # Analyze the file
           result = await self.analyzer.analyze_document(file.path)

           if result["has_code"]:
               # Update file metadata with code information
               file_manager = self.codex.get_component("file_manager")
               if file_manager:
                   await file_manager.update_metadata(
                       file.id,
                       custom_metadata={
                           "code_analysis": {
                               "has_code": True,
                               "languages": result["languages"],
                               "snippet_count": len(result["snippets"])
                           }
                       }
                   )

           return result

       async def shutdown(self):
           # Unregister analyzer
           analysis_mgr = self.codex.get_component("analysis_manager")
           if analysis_mgr and self.analyzer:
               analysis_mgr.unregister_analyzer(self.analyzer.name)

           # Unregister commands
           cli = self.codex.get_component("cli")
           if cli:
               for command in self.commands:
                   cli.unregister_command(command.name)

           self.logger.info("Code analyzer plugin shutting down")

   register_plugin(CodeAnalyzerPlugin)

Conclusion
--------

Custom plugins allow you to extend The Aichemist Codex with specialized functionality tailored to your specific needs. Whether you're adding support for custom file formats, implementing specialized analysis algorithms, or integrating with external services, the plugin system provides a flexible framework for extending the core functionality.

By following best practices and the examples in this tutorial, you can create powerful plugins that enhance The Aichemist Codex for your specific use cases, while maintaining compatibility with the core system and other plugins.