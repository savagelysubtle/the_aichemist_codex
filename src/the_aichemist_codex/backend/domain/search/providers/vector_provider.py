"""
Vector/semantic search provider implementation.

This module provides semantic search capabilities using vector embeddings
for more advanced content similarity search.
"""

import logging
import os
from pathlib import Path
from typing import Any

import numpy as np

from the_aichemist_codex.backend.core.exceptions import SearchError
from the_aichemist_codex.backend.core.models import FileMetadata, SearchResult
from the_aichemist_codex.backend.domain.search.providers.base_provider import (
    BaseSearchProvider,
)

logger = logging.getLogger(__name__)


class VectorSearchProvider(BaseSearchProvider):
    """Implements a vector-based semantic search provider."""

    def __init__(self, embedding_dimension: int = 384, cache_dir: str | None = None):
        """
        Initialize the vector search provider.

        Args:
            embedding_dimension: Dimension of the embedding vectors
            cache_dir: Directory to cache embeddings and models
        """
        self._embedding_dimension = embedding_dimension
        self._cache_dir = cache_dir

        # Simple in-memory storage for vector index
        self._document_embeddings = {}  # id -> embedding vector
        self._document_metadata = {}  # id -> metadata
        self._document_content = {}  # id -> content

        # Embedding model - will be loaded lazily
        self._embedding_model = None

        super().__init__()

    async def _initialize_provider(self) -> None:
        """Initialize the vector search provider."""
        try:
            # Create cache directory if it doesn't exist
            if self._cache_dir:
                os.makedirs(self._cache_dir, exist_ok=True)

            # Load embedding model
            await self._load_embedding_model()

            # Load existing index if available
            await self._load_index()

            logger.info(
                f"Vector search provider initialized with {len(self._document_embeddings)} documents"
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector search provider: {e}")
            raise SearchError(
                f"Vector search provider initialization failed: {e}"
            ) from e

    async def _close_provider(self) -> None:
        """Close the vector search provider."""
        try:
            # Save index to disk if cache directory is specified
            if self._cache_dir:
                await self._save_index()

            # Clear in-memory data
            self._document_embeddings.clear()
            self._document_metadata.clear()
            self._document_content.clear()

            # Free embedding model
            self._embedding_model = None

            logger.info("Vector search provider closed")
        except Exception as e:
            logger.error(f"Error closing vector search provider: {e}")
            raise SearchError(f"Failed to close vector search provider: {e}") from e

    async def _perform_search(
        self, query: str, options: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Perform vector-based semantic search.

        Args:
            query: The text to search for
            options: Search options including:
                - threshold: Minimum similarity score (0-1, default: 0.6)
                - max_results: Maximum number of results to return
                - include_content: Whether to include the content in results
                - content_preview_length: Length of content preview to include

        Returns:
            List of search results as dictionaries
        """
        try:
            # Get search options
            threshold = options.get("threshold", 0.6)
            max_results = options.get("max_results", 10)
            include_content = options.get("include_content", False)
            preview_length = options.get("content_preview_length", 100)

            # If no documents indexed, return empty results
            if not self._document_embeddings:
                logger.warning("No documents in vector index")
                return []

            # Get query embedding
            query_embedding = await self._get_embedding(query)

            # Calculate similarities to all document embeddings
            results = []

            for doc_id, doc_embedding in self._document_embeddings.items():
                # Calculate cosine similarity
                similarity = self._calculate_similarity(query_embedding, doc_embedding)

                # Filter by threshold
                if similarity >= threshold:
                    # Get document metadata
                    metadata = self._document_metadata.get(doc_id, {})
                    content = self._document_content.get(doc_id, "")

                    # Create search result
                    result = self._create_search_result(
                        doc_id,
                        metadata,
                        content,
                        similarity,
                        include_content,
                        preview_length,
                    )

                    results.append(result)

            # Sort by similarity (descending)
            results.sort(key=lambda x: x["score"], reverse=True)

            # Limit results
            return results[:max_results]

        except Exception as e:
            error_msg = f"Error in vector search: {e}"
            logger.error(error_msg)
            raise SearchError(error_msg) from e

    def _get_provider_options(self) -> dict[str, Any]:
        """
        Get the options supported by the vector search provider.

        Returns:
            Dictionary of supported options
        """
        return {
            "threshold": {
                "type": "number",
                "description": "Minimum similarity score (0-1)",
                "default": 0.6,
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
            },
            "include_content": {
                "type": "boolean",
                "description": "Whether to include the full content in results",
                "default": False,
            },
            "content_preview_length": {
                "type": "integer",
                "description": "Length of content preview to include",
                "default": 100,
            },
        }

    def _get_provider_type(self) -> str:
        """
        Get the provider type identifier.

        Returns:
            String identifier for this provider type
        """
        return "vector"

    async def _load_embedding_model(self) -> None:
        """
        Load the embedding model.

        In a real implementation, this would load a machine learning model.
        For this implementation, we'll use a simple mock embedding function.
        """
        # This is a placeholder for loading a real embedding model (e.g., using sentence-transformers)
        # In a real implementation, you might use something like:
        # from sentence_transformers import SentenceTransformer
        # self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        logger.info("Using mock embedding model")
        self._embedding_model = "mock_model"

    async def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get the embedding vector for a text.

        Args:
            text: The text to embed

        Returns:
            Embedding vector as numpy array
        """
        # This is a placeholder for generating real embeddings
        # In a real implementation, you would use the model:
        # return self._embedding_model.encode(text)

        # For demonstration, we use a mock embedding function
        # that creates a reproducible vector based on the text
        import hashlib

        # Generate a deterministic seed from the text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash, 16) % (2**32)

        # Set the seed for reproducibility
        np.random.seed(seed)

        # Generate a random vector with the specified dimension
        vector = np.random.rand(self._embedding_dimension)

        # Normalize to unit length (for cosine similarity)
        vector = vector / np.linalg.norm(vector)

        return vector

    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate the cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (value between 0 and 1)
        """
        # Cosine similarity
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    async def _load_index(self) -> None:
        """
        Load the vector index from disk.

        In a real implementation, this would load the index from a file.
        """
        if not self._cache_dir:
            return

        index_file = Path(self._cache_dir) / "vector_index.npz"
        metadata_file = Path(self._cache_dir) / "vector_metadata.npz"

        if not index_file.exists() or not metadata_file.exists():
            logger.info("No existing vector index found")
            return

        try:
            # Load embeddings
            data = np.load(index_file, allow_pickle=True)
            self._document_embeddings = data["embeddings"].item()

            # Load metadata and content
            data = np.load(metadata_file, allow_pickle=True)
            self._document_metadata = data["metadata"].item()
            self._document_content = data["content"].item()

            logger.info(
                f"Loaded vector index with {len(self._document_embeddings)} documents"
            )
        except Exception as e:
            logger.error(f"Failed to load vector index: {e}")
            # Start with an empty index
            self._document_embeddings = {}
            self._document_metadata = {}
            self._document_content = {}

    async def _save_index(self) -> None:
        """
        Save the vector index to disk.

        In a real implementation, this would save the index to a file.
        """
        if not self._cache_dir:
            return

        try:
            # Save embeddings
            index_file = Path(self._cache_dir) / "vector_index.npz"
            np.savez(index_file, embeddings=self._document_embeddings)

            # Save metadata and content
            metadata_file = Path(self._cache_dir) / "vector_metadata.npz"
            np.savez(
                metadata_file,
                metadata=self._document_metadata,
                content=self._document_content,
            )

            logger.info(
                f"Saved vector index with {len(self._document_embeddings)} documents"
            )
        except Exception as e:
            logger.error(f"Failed to save vector index: {e}")

    def _create_search_result(
        self,
        doc_id: str,
        metadata: dict[str, Any],
        content: str,
        similarity: float,
        include_content: bool,
        preview_length: int,
    ) -> dict[str, Any]:
        """
        Create a search result dictionary.

        Args:
            doc_id: Document ID
            metadata: Document metadata
            content: Document content
            similarity: Similarity score
            include_content: Whether to include content
            preview_length: Length of content preview

        Returns:
            Search result dictionary
        """
        # Create a file metadata object
        file_meta = FileMetadata(
            id=metadata.get("id", doc_id),
            name=metadata.get("title", ""),
            path=metadata.get("path", ""),
            size=metadata.get("size", 0),
            created_time=metadata.get("created", ""),
            modified_time=metadata.get("modified", ""),
            content_type=metadata.get("type", ""),
            metadata=metadata,
        )

        # Create a summary/preview of the content
        if content and len(content) > preview_length:
            preview = content[:preview_length] + "..."
        else:
            preview = content

        # Create the search result
        result = SearchResult(
            id=doc_id,
            score=similarity,
            file=file_meta,
            match_position=0,  # Not applicable for vector search
            match_context=preview,
            matched_terms=[],  # Not applicable for vector search
        )

        # Convert to dictionary
        result_dict = result.to_dict()

        # Add vector-specific fields
        result_dict["similarity"] = similarity

        # Optionally include full content
        if include_content:
            result_dict["content"] = content

        return result_dict

    async def add_content(
        self, content_id: str, content: str, metadata: dict[str, Any]
    ) -> None:
        """
        Add content to the search index.

        Args:
            content_id: Unique identifier for the content
            content: The content text
            metadata: Content metadata
        """
        self._ensure_initialized()

        try:
            # Generate embedding
            embedding = await self._get_embedding(content)

            # Add to index
            self._document_embeddings[content_id] = embedding
            self._document_metadata[content_id] = metadata
            self._document_content[content_id] = content

            logger.debug(f"Added document {content_id} to vector index")
        except Exception as e:
            logger.error(f"Failed to add document {content_id} to vector index: {e}")
            raise SearchError(f"Failed to add document to vector index: {e}") from e

    async def remove_content(self, content_id: str) -> bool:
        """
        Remove content from the search index.

        Args:
            content_id: Unique identifier for the content to remove

        Returns:
            True if content was removed, False if not found
        """
        self._ensure_initialized()

        # Check if document exists
        if content_id not in self._document_embeddings:
            logger.debug(f"Document {content_id} not found in vector index")
            return False

        # Remove from index
        self._document_embeddings.pop(content_id, None)
        self._document_metadata.pop(content_id, None)
        self._document_content.pop(content_id, None)

        logger.debug(f"Removed document {content_id} from vector index")
        return True

    async def clear_index(self) -> None:
        """Clear all content from the search index."""
        self._ensure_initialized()

        # Clear all data
        self._document_embeddings.clear()
        self._document_metadata.clear()
        self._document_content.clear()

        logger.debug("Cleared vector search index")

    async def get_index_stats(self) -> dict[str, Any]:
        """
        Get statistics about the index.

        Returns:
            Dictionary of index statistics
        """
        self._ensure_initialized()

        return {
            "document_count": len(self._document_embeddings),
            "embedding_dimension": self._embedding_dimension,
            "index_size_bytes": sum(
                array.nbytes for array in self._document_embeddings.values()
            )
            if self._document_embeddings
            else 0,
            "has_cache_dir": bool(self._cache_dir),
        }
