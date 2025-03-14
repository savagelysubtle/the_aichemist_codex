"""Integration tests for the similarity search feature.

This file contains tests that verify the functionality of the
similarity search feature in a real-world context.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

from backend.config.settings import get_settings
from backend.models.embeddings import TextEmbeddingModel, VectorIndex
from backend.search.providers.similarity_provider import SimilarityProvider
from backend.search.search_engine import SearchEngine
from backend.utils.cache_manager import CacheManager


@pytest.fixture
def test_files():
    """Create temporary test files with controlled content.

    Creates groups of files with related content to test similarity detection.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Python group (4 files)
        python_dir = Path(temp_dir) / "python"
        python_dir.mkdir()

        (python_dir / "basic.py").write_text(
            "def hello_world():\n    print('Hello, world!')\n\n"
            "if __name__ == '__main__':\n    hello_world()\n"
        )

        (python_dir / "classes.py").write_text(
            "class Person:\n    def __init__(self, name, age):\n"
            "        self.name = name\n        self.age = age\n\n"
            "    def greet(self):\n        print(f'Hello, my name is {self.name}')\n\n"
            "person = Person('Alice', 30)\nperson.greet()\n"
        )

        (python_dir / "functions.py").write_text(
            "def add(a, b):\n    return a + b\n\n"
            "def subtract(a, b):\n    return a - b\n\n"
            "def multiply(a, b):\n    return a * b\n\n"
            "def divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n"
            "    return a / b\n"
        )

        (python_dir / "list_comp.py").write_text(
            "# List comprehensions in Python\n"
            "numbers = [1, 2, 3, 4, 5]\n"
            "squares = [n**2 for n in numbers]\n"
            "even_squares = [n**2 for n in numbers if n % 2 == 0]\n"
            "print(squares)\nprint(even_squares)\n"
        )

        # JavaScript group (3 files)
        js_dir = Path(temp_dir) / "javascript"
        js_dir.mkdir()

        (js_dir / "basic.js").write_text(
            "function helloWorld() {\n    console.log('Hello, world!');\n}\n\n"
            "helloWorld();\n"
        )

        (js_dir / "classes.js").write_text(
            "class Person {\n    constructor(name, age) {\n"
            "        this.name = name;\n        this.age = age;\n    }\n\n"
            "    greet() {\n        console.log(`Hello, my name is ${this.name}`);\n    }\n}\n\n"
            "const person = new Person('Bob', 25);\nperson.greet();\n"
        )

        (js_dir / "arrays.js").write_text(
            "// Array methods in JavaScript\n"
            "const numbers = [1, 2, 3, 4, 5];\n"
            "const squares = numbers.map(n => n * n);\n"
            "const evenSquares = numbers.filter(n => n % 2 === 0).map(n => n * n);\n"
            "console.log(squares);\nconsole.log(evenSquares);\n"
        )

        # HTML group (2 files)
        html_dir = Path(temp_dir) / "html"
        html_dir.mkdir()

        (html_dir / "index.html").write_text(
            "<!DOCTYPE html>\n<html>\n<head>\n    <title>Test Page</title>\n"
            "    <link rel='stylesheet' href='styles.css'>\n</head>\n"
            "<body>\n    <h1>Welcome to the Test Page</h1>\n"
            "    <p>This is a simple HTML page for testing.</p>\n"
            "    <script src='script.js'></script>\n</body>\n</html>\n"
        )

        (html_dir / "about.html").write_text(
            "<!DOCTYPE html>\n<html>\n<head>\n    <title>About Us</title>\n"
            "    <link rel='stylesheet' href='styles.css'>\n</head>\n"
            "<body>\n    <h1>About Us</h1>\n"
            "    <p>This is the about page of our website.</p>\n"
            "    <a href='index.html'>Back to Home</a>\n"
            "    <script src='script.js'></script>\n</body>\n</html>\n"
        )

        # Unrelated file
        (temp_dir / "random.txt").write_text(
            "This is a random text file with unrelated content.\n"
            "It should not be grouped with any of the other files.\n"
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        )

        yield temp_dir


@pytest.fixture
async def similarity_search_setup(test_files):
    """Set up the components needed for similarity search testing."""
    # Create cache manager
    cache_manager = CacheManager()

    # Create embedding model and fit it to the test files
    embedding_model = TextEmbeddingModel()

    # Get all file paths in the test directory
    file_paths = []
    for root, _, files in os.walk(test_files):
        for file in files:
            file_paths.append(os.path.join(root, file))

    # Load file contents for fitting the model
    texts = []
    for path in file_paths:
        try:
            with open(path, "r", errors="ignore") as f:
                text = f.read()
                texts.append(text)
        except Exception as e:
            print(f"Error reading {path}: {e}")

    # Fit the model
    embedding_model.fit(texts)

    # Create vector index
    vector_index = VectorIndex()

    # Generate and add embeddings to the index
    embeddings = []
    for i, path in enumerate(file_paths):
        with open(path, "r", errors="ignore") as f:
            text = f.read()
            embedding = embedding_model.encode(text)
            embeddings.append(embedding)

    vector_index.add_vectors(np.array(embeddings), file_paths)

    # Create similarity provider
    similarity_provider = SimilarityProvider(
        embedding_model=embedding_model,
        vector_index=vector_index,
        path_mapping=file_paths,
        cache_manager=cache_manager,
    )

    # Create search engine with mock settings
    settings = get_settings()
    settings["enable_similarity_search"] = True

    with tempfile.TemporaryDirectory() as base_dir:
        # Create search engine
        search_engine = SearchEngine(base_dir=Path(base_dir))
        # Replace the similarity provider
        search_engine.similarity_provider = similarity_provider

        yield {
            "search_engine": search_engine,
            "similarity_provider": similarity_provider,
            "file_paths": file_paths,
            "test_dir": test_files,
        }


class TestSimilaritySearch:
    """Integration tests for similarity search functionality."""

    @pytest.mark.asyncio
    async def test_find_similar_files(self, similarity_search_setup):
        """Test finding files similar to a given file."""
        setup = similarity_search_setup
        search_engine = setup["search_engine"]
        file_paths = setup["file_paths"]

        # Find a Python file to use as reference
        python_file = next(path for path in file_paths if path.endswith(".py"))

        # Find similar files
        results = await search_engine.find_similar_files_async(
            file_path=python_file, threshold=0.5, max_results=5
        )

        # Should find at least one similar file
        assert len(results) > 0

        # Results should include other Python files
        python_files_found = [r for r in results if r["path"].endswith(".py")]
        assert len(python_files_found) > 0

        # Each result should have a path and similarity score
        for result in results:
            assert "path" in result
            assert "similarity_score" in result
            assert isinstance(result["similarity_score"], float)
            assert 0.0 <= result["similarity_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_find_file_groups(self, similarity_search_setup):
        """Test finding groups of similar files."""
        setup = similarity_search_setup
        search_engine = setup["search_engine"]
        file_paths = setup["file_paths"]

        # Find file groups
        groups = await search_engine.find_file_groups_async(
            file_paths=file_paths, threshold=0.6, min_group_size=2
        )

        # Should find at least two groups (Python and JavaScript)
        assert len(groups) >= 2

        # Verify we have a Python group
        python_group = next(
            (group for group in groups if all(path.endswith(".py") for path in group)),
            None,
        )
        assert python_group is not None
        assert len(python_group) >= 2

        # Verify we have a JavaScript group
        js_group = next(
            (group for group in groups if all(path.endswith(".js") for path in group)),
            None,
        )
        assert js_group is not None
        assert len(js_group) >= 2

    @pytest.mark.asyncio
    async def test_text_query_similarity_search(self, similarity_search_setup):
        """Test finding files similar to a text query."""
        setup = similarity_search_setup
        provider = setup["similarity_provider"]

        # Search for Python-related files
        python_results = await provider.search(
            query="Python functions and classes programming",
            threshold=0.5,
            max_results=5,
        )

        # Should find Python files
        assert len(python_results) > 0
        python_files = [path for path in python_results if path.endswith(".py")]
        assert len(python_files) > 0

        # Search for JavaScript-related files
        js_results = await provider.search(
            query="JavaScript arrays and functions", threshold=0.5, max_results=5
        )

        # Should find JavaScript files
        assert len(js_results) > 0
        js_files = [path for path in js_results if path.endswith(".js")]
        assert len(js_files) > 0

        # Verify different queries return different results
        assert set(python_results) != set(js_results)

    @pytest.mark.asyncio
    async def test_caching_behavior(self, similarity_search_setup):
        """Test that results are properly cached and retrieved from cache."""
        setup = similarity_search_setup
        provider = setup["similarity_provider"]

        # Mock the vector_index.search method to verify it's only called once
        original_search = provider.vector_index.search
        search_called = 0

        def mock_search(*args, **kwargs):
            nonlocal search_called
            search_called += 1
            return original_search(*args, **kwargs)

        provider.vector_index.search = mock_search

        # First search should call the search method
        query = "Test query for caching"
        results1 = await provider.search(query, threshold=0.5, max_results=3)
        assert search_called == 1

        # Second search with same parameters should use the cache
        results2 = await provider.search(query, threshold=0.5, max_results=3)
        assert search_called == 1  # Should not increment

        # Results should be the same
        assert results1 == results2

        # Different parameters should trigger a new search
        results3 = await provider.search(query, threshold=0.7, max_results=3)
        assert search_called == 2

        # Different query should trigger a new search
        results4 = await provider.search(
            "Different query", threshold=0.5, max_results=3
        )
        assert search_called == 3

        # Restore original method
        provider.vector_index.search = original_search
