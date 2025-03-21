Advanced API Usage Tutorial
=========================

This tutorial explores the Python API of The Aichemist Codex, demonstrating how to integrate its powerful features into your own applications, scripts, and workflows.

Setting Up for API Usage
----------------------

Before using the API, ensure you have The Aichemist Codex installed with developer dependencies:

.. code-block:: bash

   pip install the-aichemist-codex[dev]

Import the necessary components:

.. code-block:: python

   import asyncio
   from pathlib import Path

   # Core components
   from the_aichemist_codex.backend.core import CodexCore
   from the_aichemist_codex.backend.config import CodexConfig

   # Specialized components
   from the_aichemist_codex.backend.search import SearchEngine
   from the_aichemist_codex.backend.tagging import TagManager
   from the_aichemist_codex.backend.file_manager import FileManager
   from the_aichemist_codex.backend.indexing import DocumentIndexer
   from the_aichemist_codex.backend.analysis import ContentAnalyzer
   from the_aichemist_codex.backend.organization import FileOrganizer

API Architecture Overview
----------------------

The Aichemist Codex API is structured into several key components:

1. **CodexCore**: The central coordinator that initializes and connects components
2. **FileManager**: Handles file operations, tracking, and metadata
3. **DocumentIndexer**: Creates and maintains search indices
4. **SearchEngine**: Provides various search methods (semantic, keyword, hybrid)
5. **TagManager**: Manages tags and tagging operations
6. **ContentAnalyzer**: Analyzes document content for insights
7. **FileOrganizer**: Handles automated file organization

Basic API Usage Flow
-----------------

Here's a basic workflow to get started:

.. code-block:: python

   import asyncio
   from pathlib import Path
   from the_aichemist_codex.backend.core import CodexCore

   async def basic_codex_workflow():
       # Initialize the core with default configuration
       codex = CodexCore()
       await codex.initialize()

       # Process a file
       file_path = Path("~/Documents/research_paper.pdf").expanduser()
       result = await codex.process_file(file_path)

       print(f"Processed file: {file_path}")
       print(f"Extracted {len(result.extracted_text)} characters of text")
       print(f"Generated {len(result.tags)} tags")

       # Search for content
       search_results = await codex.search("quantum computing", method="semantic", limit=5)
       print(f"\nFound {len(search_results)} results for 'quantum computing':")
       for idx, result in enumerate(search_results, 1):
           print(f"{idx}. {result.file_path.name} (Score: {result.score:.2f})")

       # Clean up resources
       await codex.shutdown()

   # Run the async function
   if __name__ == "__main__":
       asyncio.run(basic_codex_workflow())

Custom Configuration
-----------------

Customize the configuration for your specific needs:

.. code-block:: python

   from the_aichemist_codex.backend.config import CodexConfig

   async def custom_configuration():
       # Create a custom configuration
       config = CodexConfig()

       # Set custom data directory
       config.data_dir = Path("~/custom_codex_data").expanduser()

       # Configure search settings
       config.search.semantic_model = "all-MiniLM-L6-v2"  # Choose embedding model
       config.search.chunk_size = 512  # Text chunking size for embeddings
       config.search.similarity_threshold = 0.75  # Minimum similarity score

       # Configure tagging settings
       config.tagging.auto_tag_threshold = 0.6  # Confidence threshold for auto-tagging
       config.tagging.max_tags_per_file = 10  # Maximum tags per file

       # Initialize with custom config
       codex = CodexCore(config=config)
       await codex.initialize()

       # Use the codex with custom configuration
       # ...

       await codex.shutdown()

   asyncio.run(custom_configuration())

Working with Files
---------------

Here's how to work with files through the API:

.. code-block:: python

   from the_aichemist_codex.backend.file_manager import FileManager
   from the_aichemist_codex.backend.models import FileMetadata

   async def file_management_example():
       # Initialize file manager
       file_manager = FileManager()
       await file_manager.initialize()

       # Add a file to the codex
       file_path = Path("~/Documents/important_doc.pdf").expanduser()
       file_id = await file_manager.add_file(
           file_path,
           copy_to_library=True,  # Make a copy in the codex library
           extract_metadata=True  # Extract metadata
       )

       # Get file metadata
       metadata = await file_manager.get_metadata(file_id)
       print(f"File: {metadata.filename}")
       print(f"Size: {metadata.size} bytes")
       print(f"Created: {metadata.creation_date}")
       print(f"MIME type: {metadata.mime_type}")

       # Update custom metadata
       await file_manager.update_metadata(
           file_id,
           custom_metadata={
               "importance": "high",
               "project": "research-2023",
               "reviewed": True
           }
       )

       # List all files in the codex
       files = await file_manager.list_files()
       print(f"\nTotal files in codex: {len(files)}")

       # Search for files by metadata
       pdf_files = await file_manager.find_files(
           filters={
               "mime_type": "application/pdf",
               "custom_metadata.project": "research-2023"
           }
       )
       print(f"Found {len(pdf_files)} PDF files for research-2023 project")

   asyncio.run(file_management_example())

Advanced Search Techniques
-----------------------

Implement advanced search capabilities:

.. code-block:: python

   from the_aichemist_codex.backend.search import SearchEngine
   from the_aichemist_codex.backend.models import SearchQuery, SearchFilter

   async def advanced_search_example():
       # Initialize search engine
       search_engine = SearchEngine()
       await search_engine.initialize()

       # Basic semantic search
       results = await search_engine.search(
           "quantum computing applications",
           method="semantic",
           limit=5
       )

       # Advanced multi-stage search
       query = SearchQuery(
           text="neural network architecture",
           method="hybrid",
           filters=[
               SearchFilter(field="tags", values=["machine-learning", "research"]),
               SearchFilter(field="creation_date", range={"start": "2022-01-01", "end": "2023-12-31"}),
               SearchFilter(field="file_extension", values=["pdf", "ipynb"])
           ],
           boost_factors={
               "recency": 0.3,  # Boost more recent documents
               "length": 0.2,   # Boost longer documents
               "tag_match": 0.5  # Boost documents with more matching tags
           },
           limit=20,
           offset=0,
           similarity_threshold=0.65
       )

       advanced_results = await search_engine.advanced_search(query)

       # Context-enhanced search
       context_results = await search_engine.search(
           "implementation details",
           context="I'm working on a transformer-based language model focusing on attention mechanisms",
           method="semantic"
       )

       # Search within specific files
       file_paths = [Path("doc1.pdf"), Path("doc2.pdf"), Path("doc3.pdf")]
       scoped_results = await search_engine.search_within_files(
           "optimization techniques",
           file_paths=file_paths,
           method="semantic"
       )

       # Generate search insights
       insights = await search_engine.analyze_results(advanced_results)
       print(f"Key concepts: {', '.join(insights.key_concepts)}")
       print(f"Suggested queries: {', '.join(insights.suggested_queries)}")

   asyncio.run(advanced_search_example())

Working with Tags
--------------

Implement sophisticated tagging operations:

.. code-block:: python

   from the_aichemist_codex.backend.tagging import TagManager, TagSuggester
   from the_aichemist_codex.backend.models import Tag, TagCategory

   async def advanced_tagging_example():
       # Initialize tag components
       tag_manager = TagManager()
       await tag_manager.initialize()

       tag_suggester = TagSuggester(tag_manager)

       # Create tag categories
       category_id = await tag_manager.create_category(
           name="research_areas",
           description="Research domains and fields"
       )

       # Create tags
       ml_tag_id = await tag_manager.create_tag(
           name="machine_learning",
           description="Machine Learning research and applications",
           category_id=category_id
       )

       # Create child tags (hierarchical)
       await tag_manager.create_tag(
           name="deep_learning",
           description="Deep neural network approaches",
           parent_id=ml_tag_id,
           category_id=category_id
       )

       # Get tag suggestions for a file
       file_path = Path("~/Documents/research_paper.pdf").expanduser()
       suggestions = await tag_suggester.suggest_tags(
           file_path,
           methods=["content", "metadata", "similar_files"],
           limit=10
       )

       print("Tag suggestions:")
       for tag, score in suggestions:
           print(f"- {tag.name}: {score:.2f}")

       # Get suggestion explanation
       explanation = await tag_suggester.explain_suggestions(file_path, suggestions[:3])
       for tag, reasons in explanation.items():
           print(f"\nWhy '{tag}' was suggested:")
           for reason in reasons:
               print(f"- {reason}")

       # Apply tags to a file
       selected_tags = [tag for tag, score in suggestions if score > 0.7]
       await tag_manager.apply_tags(file_path, selected_tags)

       # Find files with specific tags
       files_with_tags = await tag_manager.find_files_with_tags(
           ["machine_learning", "research"],
           match_all=True
       )

       # Get tag statistics
       stats = await tag_manager.get_tag_statistics()
       print("\nMost used tags:")
       for tag, count in stats.most_used_tags[:5]:
           print(f"- {tag.name}: {count} files")

   asyncio.run(advanced_tagging_example())

Content Analysis
-------------

Extract insights from document content:

.. code-block:: python

   from the_aichemist_codex.backend.analysis import ContentAnalyzer

   async def content_analysis_example():
       # Initialize analyzer
       analyzer = ContentAnalyzer()
       await analyzer.initialize()

       # Analyze a document
       file_path = Path("~/Documents/research_paper.pdf").expanduser()
       analysis = await analyzer.analyze_document(file_path)

       # Extract key information
       print("Document Analysis:")
       print(f"Title: {analysis.title}")
       print(f"Authors: {', '.join(analysis.authors)}")
       print(f"Abstract: {analysis.abstract[:200]}...")

       # Get key topics
       print("\nKey Topics:")
       for topic, relevance in analysis.topics:
           print(f"- {topic}: {relevance:.2f}")

       # Extract entities
       print("\nKey Entities:")
       for entity_type, entities in analysis.entities.items():
           print(f"\n{entity_type}:")
           for entity, occurrences in entities[:5]:
               print(f"- {entity}: {occurrences} occurrences")

       # Generate summary
       summary = await analyzer.generate_summary(file_path, max_length=500)
       print(f"\nSummary:\n{summary}")

       # Extract citations
       citations = await analyzer.extract_citations(file_path)
       print(f"\nFound {len(citations)} citations")

       # Compare documents
       comparison = await analyzer.compare_documents(
           [file_path, Path("~/Documents/related_paper.pdf").expanduser()]
       )
       print("\nDocument Comparison:")
       print(f"Similarity: {comparison.similarity:.2f}")
       print(f"Shared topics: {', '.join(comparison.shared_topics)}")
       print(f"Unique to first: {', '.join(comparison.unique_to_first)}")
       print(f"Unique to second: {', '.join(comparison.unique_to_second)}")

   asyncio.run(content_analysis_example())

Automated File Organization
------------------------

Implement custom file organization logic:

.. code-block:: python

   from the_aichemist_codex.backend.organization import FileOrganizer
   from the_aichemist_codex.backend.rules import OrganizationRuleSet, Rule, Condition, TargetPattern

   async def organization_example():
       # Initialize organizer
       organizer = FileOrganizer()
       await organizer.initialize()

       # Create custom rules programmatically
       rules = OrganizationRuleSet()

       # Add a rule for research papers
       research_rule = Rule(
           name="Research Papers",
           conditions=[
               Condition(type="extension", values=["pdf", "docx"]),
               Condition(type="tag", value="research")
           ],
           target=TargetPattern("Research/{extracted.year}/{extracted.topic}")
       )
       rules.add_rule(research_rule)

       # Add a rule for code files
       code_rule = Rule(
           name="Code Files",
           conditions=[
               Condition(type="extension", values=["py", "js", "java"])
           ],
           target=TargetPattern("Code/{file.extension}/{extracted.project}")
       )
       rules.add_rule(code_rule)

       # Save rules to file
       rules.save("my_organization_rules.yaml")

       # Plan organization (preview without executing)
       source_dir = Path("~/Documents").expanduser()
       plan = await organizer.plan_organization(
           source_dir=source_dir,
           rules=rules,
           recursive=True
       )

       # Analyze the plan
       print(f"Organization plan would affect {len(plan.moves)} files")

       # Statistics by rule
       rule_stats = {}
       for move in plan.moves:
           rule_name = move.matched_rule
           rule_stats[rule_name] = rule_stats.get(rule_name, 0) + 1

       print("\nMatches by rule:")
       for rule, count in rule_stats.items():
           print(f"- {rule}: {count} files")

       # Execute the plan
       result = await organizer.execute_plan(
           plan,
           mode="copy",  # Options: move, copy, link
           conflict_resolution="rename"  # Options: rename, skip, overwrite, prompt
       )

       print(f"\nOrganized {result.success_count} files")
       if result.errors:
           print(f"Encountered {len(result.errors)} errors")

   asyncio.run(organization_example())

Event Handling and Monitoring
--------------------------

Monitor and respond to Codex events:

.. code-block:: python

   from the_aichemist_codex.backend.core import CodexCore
   from the_aichemist_codex.backend.events import EventListener, EventType

   async def event_handling_example():
       # Initialize the core
       codex = CodexCore()

       # Create an event listener
       class MyListener(EventListener):
           async def on_event(self, event_type, data):
               print(f"Event: {event_type}")
               if event_type == EventType.FILE_ADDED:
                   print(f"File added: {data['file_path']}")
               elif event_type == EventType.SEARCH_PERFORMED:
                   print(f"Search performed: {data['query']} (found {len(data['results'])} results)")
               elif event_type == EventType.TAG_APPLIED:
                   print(f"Tag '{data['tag']}' applied to {data['file_path']}")
               elif event_type == EventType.ERROR:
                   print(f"Error: {data['message']}")

       # Register the listener
       listener = MyListener()
       codex.register_listener(listener)

       # Initialize with the listener attached
       await codex.initialize()

       # Perform some operations that will trigger events
       await codex.process_file(Path("~/Documents/example.pdf").expanduser())
       await codex.search("quantum computing")

       # Later, unregister if needed
       codex.unregister_listener(listener)

       # Always clean up
       await codex.shutdown()

   asyncio.run(event_handling_example())

Integration with External Services
-------------------------------

Integrate with external tools and services:

.. code-block:: python

   from the_aichemist_codex.backend.core import CodexCore
   from the_aichemist_codex.backend.integrations import (
       SlackIntegration,
       DropboxIntegration,
       NotionIntegration
   )

   async def integration_example():
       # Initialize the core
       codex = CodexCore()
       await codex.initialize()

       # Set up Slack integration
       slack = SlackIntegration(
           token="your_slack_token",
           default_channel="#documents"
       )
       await slack.initialize()

       # Connect the integration to Codex
       codex.register_integration(slack)

       # Now Codex can send notifications to Slack
       await codex.notify(
           message="New research papers have been processed",
           level="info",
           data={"file_count": 5, "categories": ["AI", "ML"]}
       )

       # Use the integration directly
       await slack.send_message(
           channel="#research",
           message="Document analysis complete",
           attachments=[
               {"title": "Research Summary", "text": "Key findings..."}
           ]
       )

       # Clean up
       await slack.shutdown()
       await codex.shutdown()

   asyncio.run(integration_example())

Creating Custom Plugins
-------------------

Extend The Aichemist Codex with your own plugins:

.. code-block:: python

   from the_aichemist_codex.backend.plugins import CodexPlugin, register_plugin
   from the_aichemist_codex.backend.models import File

   # Define a custom plugin
   class ResearchAnalyzerPlugin(CodexPlugin):
       def __init__(self):
           super().__init__(
               name="research_analyzer",
               version="1.0.0",
               description="Analyzes research papers for methodology and findings"
           )

       async def initialize(self):
           # Plugin initialization code
           self.logger.info("Research Analyzer Plugin initialized")
           return True

       async def process_file(self, file: File):
           """Custom file processing for research papers"""
           if not file.mime_type.startswith("application/pdf"):
               return None

           self.logger.info(f"Analyzing research paper: {file.path}")

           # Example analysis (in a real plugin, you'd do actual processing)
           analysis_result = {
               "methodology": "Experimental",
               "sample_size": 250,
               "statistical_methods": ["ANOVA", "Regression"],
               "key_findings": ["Finding 1", "Finding 2"]
           }

           # Store the analysis with the file
           await self.codex.file_manager.update_metadata(
               file.id,
               custom_metadata={
                   "research_analysis": analysis_result
               }
           )

           return analysis_result

       async def shutdown(self):
           # Clean up resources
           self.logger.info("Research Analyzer Plugin shutting down")

   # Register the plugin
   register_plugin(ResearchAnalyzerPlugin)

   # Using the plugin in your code
   async def use_custom_plugin():
       codex = CodexCore()
       await codex.initialize()

       # The plugin will be automatically loaded if it's registered

       # Process a file, which will also run through the plugin
       file_path = Path("~/Documents/research_paper.pdf").expanduser()
       await codex.process_file(file_path)

       # Get the results added by the plugin
       metadata = await codex.file_manager.get_metadata(file_path)
       if "research_analysis" in metadata.custom_metadata:
           analysis = metadata.custom_metadata["research_analysis"]
           print(f"Methodology: {analysis['methodology']}")
           print(f"Sample size: {analysis['sample_size']}")

       await codex.shutdown()

   asyncio.run(use_custom_plugin())

Working with Batch Processing
--------------------------

Efficiently process large collections of files:

.. code-block:: python

   from the_aichemist_codex.backend.core import CodexCore
   from the_aichemist_codex.backend.batch import BatchProcessor

   async def batch_processing_example():
       # Initialize components
       codex = CodexCore()
       await codex.initialize()

       batch_processor = BatchProcessor(codex)

       # Define a source directory with many files
       source_dir = Path("~/large_document_collection").expanduser()

       # Create a batch job
       job = await batch_processor.create_job(
           name="Process Research Papers",
           source_paths=[source_dir],
           file_patterns=["*.pdf", "*.docx"],
           recursive=True,
           max_files=1000,
           operations=["index", "tag", "analyze"],
           options={
               "tag": {"auto_threshold": 0.6},
               "analyze": {"extract_citations": True}
           }
       )

       # Start processing with progress updates
       async for progress in batch_processor.run_job(job.id):
           print(f"Progress: {progress.percentage:.1f}% ({progress.completed}/{progress.total})")
           if progress.current_file:
               print(f"Processing: {progress.current_file.name}")

           # Handle any errors from the batch
           for error in progress.recent_errors:
               print(f"Error on {error.file_path}: {error.message}")

       # Get job results
       results = await batch_processor.get_job_results(job.id)
       print(f"\nJob complete. Processed {results.success_count} files successfully.")
       print(f"Failed: {results.error_count} files")

       # Get a summary of the batch
       summary = await batch_processor.summarize_job(job.id)
       print(f"\nBatch Summary:")
       print(f"Most common topics: {', '.join(summary.top_topics)}")
       print(f"Document types: {', '.join(f'{k}: {v}' for k, v in summary.document_types.items())}")

       await codex.shutdown()

   asyncio.run(batch_processing_example())

Advanced Configuration and Customization
-------------------------------------

Fine-tune The Aichemist Codex for specific use cases:

.. code-block:: python

   from the_aichemist_codex.backend.config import CodexConfig
   from the_aichemist_codex.backend.core import CodexCore

   async def advanced_configuration():
       # Create a highly customized configuration
       config = CodexConfig()

       # General settings
       config.data_dir = Path("~/specialized_codex").expanduser()
       config.temp_dir = Path("/tmp/codex_processing")
       config.max_concurrent_tasks = 8
       config.log_level = "DEBUG"

       # File management settings
       config.file_manager.default_copy_mode = "link"  # Options: copy, move, link
       config.file_manager.duplicate_handling = "hash"  # Options: hash, name, ask
       config.file_manager.allowed_extensions = [".pdf", ".docx", ".md", ".py", ".ipynb"]

       # Search settings
       config.search.engine = "milvus"  # Options: faiss, milvus, opensearch
       config.search.semantic_model = "all-mpnet-base-v2"
       config.search.enable_hybrid_search = True
       config.search.index_update_strategy = "realtime"  # Options: realtime, batch, manual

       # Tagging settings
       config.tagging.enable_auto_tagging = True
       config.tagging.tag_suggestion_methods = ["content", "metadata", "similar"]
       config.tagging.max_tags_per_file = 15

       # Analysis settings
       config.analysis.enable_citation_extraction = True
       config.analysis.enable_entity_recognition = True
       config.analysis.summarization_model = "t5-base"
       config.analysis.topic_model = "lda"  # Options: lda, bertopic, nmf

       # Storage settings
       config.storage.enable_versioning = True
       config.storage.compression = "zstd"  # Options: none, zstd, gzip
       config.storage.encryption_key = "your-encryption-key"  # For sensitive data

       # Performance settings
       config.performance.chunk_size = 1024
       config.performance.batch_size = 64
       config.performance.cache_size_mb = 512
       config.performance.use_gpu = True

       # Initialize with the custom configuration
       codex = CodexCore(config=config)
       await codex.initialize()

       # Use the highly customized codex instance
       # ...

       await codex.shutdown()

   asyncio.run(advanced_configuration())

Conclusion
--------

The Aichemist Codex Python API provides a powerful, flexible way to integrate advanced document management capabilities into your applications and workflows. By leveraging the API, you can build custom solutions for:

- Research paper analysis and management
- Knowledge base construction and maintenance
- Document processing pipelines
- Content organization systems
- Intelligent document search applications
- Metadata extraction and enrichment services

The API's modular design allows you to use only the components you need while maintaining a cohesive system through the CodexCore orchestrator. Through custom configurations, plugins, and integrations, you can tailor The Aichemist Codex to your specific use cases and requirements.