"""
Relationship graph functionality.

This module provides classes and utilities for representing and analyzing
file relationships as a graph structure.
"""

import logging
from collections import defaultdict
from pathlib import Path

import networkx as nx

from .models import RelationshipType
from .store import RelationshipStore

logger = logging.getLogger(__name__)


class RelationshipGraph:
    """
    Represents file relationships as a graph structure.

    This class provides graph-based operations on file relationships,
    such as finding paths between files, identifying clusters, and
    calculating centrality metrics.
    """

    def __init__(self, relationship_store: RelationshipStore) -> None:
        """
        Initialize the relationship graph with a relationship store.

        Args:
            relationship_store: The store containing relationships
        """
        self.store = relationship_store
        self._graph = None
        self._last_update = None

    def build_graph(
        self,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
    ) -> nx.DiGraph:
        """
        Build a directed graph from the relationships in the store.

        Args:
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            NetworkX directed graph
        """
        # Create a new directed graph
        graph = nx.DiGraph()

        # Get all relationships from the store
        relationships = self.store.get_all_relationships(
            rel_types=rel_types, min_strength=min_strength
        )

        # Add nodes and edges to the graph
        for rel in relationships:
            source = str(rel.source_path)
            target = str(rel.target_path)

            # Add nodes if they don't exist
            if not graph.has_node(source):
                graph.add_node(source, path=rel.source_path)

            if not graph.has_node(target):
                graph.add_node(target, path=rel.target_path)

            # Add edge with relationship data
            graph.add_edge(
                source,
                target,
                type=rel.rel_type,
                strength=rel.strength,
                metadata=rel.metadata,
                id=rel.id,
            )

        # Cache the graph
        self._graph = graph

        return graph

    def get_graph(
        self,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
        force_rebuild: bool = False,
    ) -> nx.DiGraph:
        """
        Get the relationship graph, building it if necessary.

        Args:
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)
            force_rebuild: Whether to force rebuilding the graph

        Returns:
            NetworkX directed graph
        """
        if self._graph is None or force_rebuild:
            return self.build_graph(rel_types, min_strength)
        return self._graph

    def find_paths(
        self,
        source_path: Path,
        target_path: Path,
        max_length: int = 5,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
    ) -> list[list[tuple[Path, RelationshipType]]]:
        """
        Find all paths between two files up to a maximum length.

        Args:
            source_path: Starting file path
            target_path: Ending file path
            max_length: Maximum path length
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            List of paths, where each path is a list of (file_path, relationship_type) tuples
        """
        graph = self.get_graph(rel_types, min_strength)

        source = str(source_path)
        target = str(target_path)

        # Check if both nodes exist in the graph
        if not graph.has_node(source) or not graph.has_node(target):
            return []

        # Find all simple paths up to max_length
        try:
            paths = list(nx.all_simple_paths(graph, source, target, cutoff=max_length))
        except nx.NetworkXNoPath:
            return []

        # Convert paths to the desired format
        result = []
        for path in paths:
            path_with_types = []
            for i in range(len(path) - 1):
                edge_data = graph.get_edge_data(path[i], path[i + 1])
                path_with_types.append((Path(path[i + 1]), edge_data["type"]))
            result.append(path_with_types)

        return result

    def find_related_clusters(
        self,
        file_path: Path,
        max_distance: int = 2,
        min_strength: float = 0.0,
        rel_types: list[RelationshipType] | None = None,
    ) -> dict[str, list[Path]]:
        """
        Find clusters of related files around the given file.

        Args:
            file_path: The central file to find clusters around
            max_distance: Maximum distance from the central file
            min_strength: Minimum relationship strength (0.0 to 1.0)
            rel_types: Optional filter for relationship types

        Returns:
            Dictionary mapping cluster names to lists of file paths
        """
        graph = self.get_graph(rel_types, min_strength)
        source = str(file_path)

        # Check if the node exists in the graph
        if not graph.has_node(source):
            return {}

        # Get all nodes within max_distance
        nodes_within_distance = set()
        for distance in range(1, max_distance + 1):
            # Get nodes at exactly distance away
            nodes_at_distance = set()

            # Forward direction (outgoing edges)
            for path in nx.single_source_shortest_path_length(
                graph, source, cutoff=distance
            ):
                # Check if node has any outgoing edges
                if len(list(graph.successors(path))) > 0:
                    nodes_at_distance.add(path)

            # Backward direction (incoming edges)
            reverse_graph = graph.reverse(copy=True)
            for path in nx.single_source_shortest_path_length(
                reverse_graph, source, cutoff=distance
            ):
                # Check if node has any incoming edges
                if len(list(graph.predecessors(path))) > 0:
                    nodes_at_distance.add(path)

            nodes_within_distance.update(nodes_at_distance)

        # Group nodes by relationship type
        clusters: dict[str, list[Path]] = defaultdict(list)

        for node in nodes_within_distance:
            if node == source:
                continue

            # Check outgoing edges
            if graph.has_edge(source, node):
                edge_data = graph.get_edge_data(source, node)
                rel_type = edge_data["type"].name
                clusters[rel_type].append(Path(node))

            # Check incoming edges
            elif graph.has_edge(node, source):
                edge_data = graph.get_edge_data(node, source)
                rel_type = f"INCOMING_{edge_data['type'].name}"
                clusters[rel_type].append(Path(node))

            # Indirect relationships
            else:
                clusters["INDIRECT"].append(Path(node))

        return dict(clusters)

    def calculate_centrality(
        self,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
        top_n: int = 10,
    ) -> list[tuple[Path, float]]:
        """
        Calculate centrality metrics to identify the most important files.

        Args:
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)
            top_n: Number of top results to return

        Returns:
            List of (file_path, centrality_score) tuples, sorted by score
        """
        graph = self.get_graph(rel_types, min_strength)

        # Calculate PageRank centrality
        centrality = nx.pagerank(graph)

        # Convert to list of (path, score) tuples and sort
        result = [(Path(node), score) for node, score in centrality.items()]

        # Sort by score in descending order and take top_n
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:top_n]

    def export_graphviz(
        self,
        output_path: Path,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
        max_nodes: int = 100,
    ) -> None:
        """
        Export the relationship graph to a GraphViz DOT file.

        Args:
            output_path: Path to save the DOT file
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)
            max_nodes: Maximum number of nodes to include

        Raises:
            IOError: If there's an error writing the file
        """
        graph = self.get_graph(rel_types, min_strength)

        # Limit the number of nodes if necessary
        if len(graph.nodes) > max_nodes:
            # Use centrality to determine the most important nodes
            centrality = nx.pagerank(graph)
            important_nodes = sorted(
                centrality.items(), key=lambda x: x[1], reverse=True
            )[:max_nodes]

            # Create a subgraph with only the important nodes
            nodes_to_keep = [node for node, _ in important_nodes]
            graph = graph.subgraph(nodes_to_keep)

        # Export to DOT format
        try:
            nx.drawing.nx_pydot.write_dot(graph, str(output_path))
            logger.info(f"Exported relationship graph to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting graph to {output_path}: {str(e)}")
            raise

    def export_json(
        self,
        output_path: Path,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
        max_nodes: int = 100,
    ) -> None:
        """
        Export the relationship graph to a JSON file for visualization.

        Args:
            output_path: Path to save the JSON file
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)
            max_nodes: Maximum number of nodes to include

        Raises:
            IOError: If there's an error writing the file
        """
        import json

        graph = self.get_graph(rel_types, min_strength)

        # Limit the number of nodes if necessary
        if len(graph.nodes) > max_nodes:
            # Use centrality to determine the most important nodes
            centrality = nx.pagerank(graph)
            important_nodes = sorted(
                centrality.items(), key=lambda x: x[1], reverse=True
            )[:max_nodes]

            # Create a subgraph with only the important nodes
            nodes_to_keep = [node for node, _ in important_nodes]
            graph = graph.subgraph(nodes_to_keep)

        # Convert to a format suitable for visualization libraries
        nodes = []
        for node in graph.nodes:
            nodes.append({"id": node, "label": Path(node).name, "path": node})

        edges = []
        for source, target, data in graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "type": data["type"].name,
                    "strength": data["strength"],
                }
            )

        result = {"nodes": nodes, "edges": edges}

        # Export to JSON
        try:
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Exported relationship graph to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting graph to {output_path}: {str(e)}")
            raise
