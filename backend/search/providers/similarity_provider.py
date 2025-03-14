"""Similarity-based search provider for finding related files.

This module provides classes and functions for finding similar files
using vector embeddings based on file content.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from backend.config.settings import get_settings
from backend.models.embeddings import (TextEmbeddingModel, VectorIndex,
                                      create_embedding_model, compute_similarity_matrix)
from backend.utils.async_io import AsyncFileTools
from backend.utils.cache_manager import CacheManager
from backend.utils.concurrency import AsyncThreadPoolExecutor

logger = logging.getLogger(__name__)


class SimilarityProvider:
    """Provider for similarity-based search capabilities.

    This class enables finding files related to a query or another file
    by comparing their vector embeddings.

    Features:
    - Vector-based similarity search
    - File-to-file similarity comparison
    - Text-to-file search
    - File grouping based on similarity
    - Caching of results
    """

    def __init__(self,
                 embedding_model: Optional[TextEmbeddingModel] = None,
                 vector_index: Optional[VectorIndex] = None,
                 path_mapping: Optional[List[str]] = None,
                 cache_manager: Optional[CacheManager] = None):
        """Initialize the similarity provider.

        Args:
            embedding_model: Model for creating text embeddings
            vector_index: Index for storing and searching vectors
            path_mapping: List of file paths corresponding to vectors in the index
            cache_manager: Manager for caching search results
        """
        self.embedding_model = embedding_model
        self.vector_index = vector_index
        self.path_mapping = path_mapping or []
        self.cache_manager = cache_manager
        self.cache_ttl = get_settings().get("SIMILARITY_CACHE_TTL", 300)  # Default 5 minutes
        self.batch_processor = AsyncThreadPoolExecutor.get_instance()

    async def search(self,
                     query: str,
                     file_paths: Optional[List[str]] = None,
                     threshold: float = 0.7,
                     max_results: int = 10) -> List[str]:
        """Search for files similar to the provided text query.

        Args:
            query: Text query to search for
            file_paths: Optional list of file paths to limit search to
            threshold: Minimum similarity score (0.0-1.0) for matches
            max_results: Maximum number of results to return

        Returns:
            List of file paths ordered by similarity
        """
        if not query or not self.embedding_model or not self.vector_index:
            return []

        # Check cache first
        cache_key = f"similarity_search:{query}:{threshold}:{max_results}"
        if file_paths:
            cache_key += f":{','.join(sorted(file_paths[:5]))}"  # Include sample of paths in key

        if self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for similarity search: {query}")
                return cached_result

        try:
            # Generate embedding for the query
            query_vector = self.embedding_model.encode(query)

            # Search the vector index
            distances, indices = self.vector_index.search(query_vector, k=max_results * 2)  # Get more results than needed for filtering

            # Filter by threshold and get paths
            filtered_indices = [idx for i, idx in enumerate(indices) if distances[i] >= threshold]
            results = self.vector_index.get_paths(filtered_indices)

            # If file_paths is provided, filter to only include those paths
            if file_paths:
                file_path_set = set(file_paths)
                results = [path for path in results if path in file_path_set]

            # Limit to max_results
            results = results[:max_results]

            # Cache results
            if self.cache_manager:
                self.cache_manager.set(cache_key, results, ttl=self.cache_ttl)

            logger.debug(f"Found {len(results)} similar files for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []

    async def find_similar_files(self,
                                file_path: Union[str, Path],
                                threshold: float = 0.7,
                                max_results: int = 10) -> List[Tuple[str, float]]:
        """Find files similar to the provided file.

        Args:
            file_path: Path to the reference file
            threshold: Minimum similarity score (0.0-1.0) for matches
            max_results: Maximum number of results to return

        Returns:
            List of tuples containing (file_path, similarity_score)
        """
        if not self.embedding_model or not self.vector_index:
            return []

        file_path_str = str(file_path)

        # Check cache first
        cache_key = f"similar_files:{file_path_str}:{threshold}:{max_results}"
        if self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for similar files: {file_path_str}")
                return cached_result

        try:
            # Read file content
            content = ""
            if os.path.exists(file_path):
                async for chunk in AsyncFileTools.read_chunked(file_path):
                    content += chunk.decode('utf-8', errors='ignore')

                # Generate embedding for the file
                file_vector = self.embedding_model.encode(content)

                # Search the vector index
                distances, indices = self.vector_index.search(file_vector, k=max_results + 1)  # +1 for the file itself

                # Filter by threshold and get paths with scores
                results = []
                for i, idx in enumerate(indices):
                    path = self.vector_index.path_mapping[idx] if idx < len(self.vector_index.path_mapping) else ""
                    score = float(distances[i])

                    # Skip the file itself and ensure score meets threshold
                    if path and path != file_path_str and score >= threshold:
                        results.append((path, score))

                # Limit to max_results
                results = results[:max_results]

                # Cache results
                if self.cache_manager:
                    self.cache_manager.set(cache_key, results, ttl=self.cache_ttl)

                logger.debug(f"Found {len(results)} similar files for: {file_path_str}")
                return results
            else:
                logger.warning(f"File not found: {file_path_str}")
                return []

        except Exception as e:
            logger.error(f"Error finding similar files for {file_path_str}: {e}")
            return []

    async def find_file_groups(self,
                              file_paths: Optional[List[Union[str, Path]]] = None,
                              threshold: float = 0.7,
                              min_group_size: int = 2) -> List[List[str]]:
        """Find groups of similar files using hierarchical clustering.

        Args:
            file_paths: Optional list of file paths to analyze
            threshold: Similarity threshold for group membership
            min_group_size: Minimum number of files to form a group

        Returns:
            List of lists, where each inner list contains paths of similar files
        """
        if not self.embedding_model:
            return []

        # Use provided file_paths or all paths in the index
        paths_to_process = [str(p) for p in file_paths] if file_paths else self.path_mapping

        if not paths_to_process:
            logger.warning("No files to process for finding file groups")
            return []

        # Check cache first
        cache_key = f"file_groups:{threshold}:{min_group_size}"
        if file_paths:
            cache_key += f":{len(file_paths)}"  # Add count to distinguish different file sets

        if self.cache_manager:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for file groups with threshold {threshold}")
                return cached_result

        try:
            # Process files in manageable batches
            batch_size = 100  # Process 100 files at a time
            all_embeddings = []
            valid_paths = []

            # Process files in batches
            for i in range(0, len(paths_to_process), batch_size):
                batch = paths_to_process[i:i+batch_size]

                # Process files to get their embeddings
                results = await self.batch_processor.process_batch(
                    items=batch,
                    process_func=self._process_file,
                    max_workers=10,
                    description="Processing files for grouping"
                )

                # Filter out None results and collect embeddings and paths
                for result in results:
                    if result:
                        path, embedding = result
                        all_embeddings.append(embedding)
                        valid_paths.append(path)

            if not all_embeddings:
                logger.warning("No valid embeddings extracted from files")
                return []

            # Convert list of embeddings to a numpy array
            embeddings_array = np.array(all_embeddings)

            # Compute similarity matrix
            similarity_matrix = compute_similarity_matrix(embeddings_array)

            # Convert similarity to distance (1 - similarity)
            distance_matrix = 1 - similarity_matrix

            # Apply hierarchical clustering
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=1 - threshold,  # Convert similarity threshold to distance
                affinity='precomputed',
                linkage='average'
            )

            cluster_labels = clustering.fit_predict(distance_matrix)

            # Group files by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(valid_paths[i])

            # Filter clusters by minimum size
            file_groups = [group for group in clusters.values() if len(group) >= min_group_size]

            # Cache results
            if self.cache_manager:
                self.cache_manager.set(cache_key, file_groups, ttl=self.cache_ttl)

            logger.info(f"Found {len(file_groups)} groups of similar files")
            return file_groups

        except Exception as e:
            logger.error(f"Error finding file groups: {e}")
            return []

    async def _process_file(self, file_path: Union[str, Path]) -> Optional[Tuple[str, np.ndarray]]:
        """Process a file to extract its embedding.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (file_path, embedding) or None if processing failed
        """
        try:
            file_path_str = str(file_path)
            if not os.path.exists(file_path_str):
                return None

            # Skip large files and non-text files
            if os.path.getsize(file_path_str) > 1_000_000:  # 1MB limit
                logger.debug(f"Skipping large file: {file_path_str}")
                return None

            content = ""
            async for chunk in AsyncFileTools.read_chunked(file_path_str):
                content += chunk.decode('utf-8', errors='ignore')

            # Generate embedding for the file
            file_vector = self.embedding_model.encode(content)
            return (file_path_str, file_vector)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None
