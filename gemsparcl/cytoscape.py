#!/usr/bin/env python3
"""Cytoscape GraphML export for network visualization."""

import logging
import csv
from typing import Any, Dict, List, Set

import networkx as nx

logger = logging.getLogger('gemsparcl.cytoscape')


def export_network_for_cytoscape(graph: nx.Graph, components: List[Set[str]],
                                output_prefix: str,
                                node_metadata: Dict[str, Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """Export network to Cytoscape format, splitting large components.

    `node_metadata` maps genome_id to a dict of arbitrary node attributes (e.g.
    `cluster_id`, `is_query`, `note`). These are embedded directly as node
    attributes in the GraphML output and also written to a side-car annotation CSV.
    """

    logger.info(f"Exporting network ({graph.number_of_nodes()} nodes) to Cytoscape")

    node_metadata = node_metadata or {}
    annotation_columns = sorted({key for meta in node_metadata.values() for key in meta}) or ['cluster_id']

    # Sort components by size
    sorted_components = sorted(components, key=len, reverse=True)

    graphml_files = []
    annotation_files = []
    file_num = 0
    max_nodes_per_file = 30000

    # Handle large components (>30k nodes) - save individually
    large_components = [c for c in sorted_components if len(c) > max_nodes_per_file]
    small_components = [c for c in sorted_components if len(c) <= max_nodes_per_file]

    if large_components:
        logger.info(f"Saving {len(large_components)} large components individually")
        for component in large_components:
            file_num += 1
            graphml_file = f"{output_prefix}_part{file_num}.graphml"
            annotation_file = f"{output_prefix}_annotations_part{file_num}.csv"

            subgraph = graph.subgraph(component).copy()
            _annotate_nodes(subgraph, node_metadata)
            nx.write_graphml(subgraph, graphml_file)
            _save_annotations(subgraph.nodes(), annotation_file, node_metadata, annotation_columns)

            graphml_files.append(graphml_file)
            annotation_files.append(annotation_file)

    # Batch small components together
    if small_components:
        logger.info(f"Batching {len(small_components)} small components")
        current_batch = []
        current_size = 0

        for component in small_components:
            if current_size + len(component) > max_nodes_per_file and current_batch:
                # Save current batch
                file_num += 1
                graphml_file = f"{output_prefix}_part{file_num}.graphml"
                annotation_file = f"{output_prefix}_annotations_part{file_num}.csv"

                batch_graph = _create_batch_graph(current_batch, graph)
                _annotate_nodes(batch_graph, node_metadata)
                nx.write_graphml(batch_graph, graphml_file)
                _save_annotations(batch_graph.nodes(), annotation_file, node_metadata, annotation_columns)

                graphml_files.append(graphml_file)
                annotation_files.append(annotation_file)

                current_batch = []
                current_size = 0

            current_batch.append(component)
            current_size += len(component)

        # Save remaining batch
        if current_batch:
            file_num += 1
            graphml_file = f"{output_prefix}_part{file_num}.graphml"
            annotation_file = f"{output_prefix}_annotations_part{file_num}.csv"

            batch_graph = _create_batch_graph(current_batch, graph)
            _annotate_nodes(batch_graph, node_metadata)
            nx.write_graphml(batch_graph, graphml_file)
            _save_annotations(batch_graph.nodes(), annotation_file, node_metadata, annotation_columns)

            graphml_files.append(graphml_file)
            annotation_files.append(annotation_file)

    logger.info(f"Created {len(graphml_files)} GraphML files")

    return {
        'graphml_files': graphml_files,
        'annotation_files': annotation_files,
        'info_file': None
    }


def _create_batch_graph(components: List[Set[str]], graph: nx.Graph) -> nx.Graph:
    """Combine multiple components into a single graph."""
    batch_graph = nx.Graph()
    for component in components:
        subgraph = graph.subgraph(component)
        batch_graph.add_nodes_from(subgraph.nodes(data=True))
        batch_graph.add_edges_from(subgraph.edges(data=True))
    return batch_graph


def _annotate_nodes(graph: nx.Graph, node_metadata: Dict[str, Dict[str, Any]]) -> None:
    """Copy per-node metadata onto graph nodes so it is embedded in the GraphML output."""
    for node in graph.nodes():
        for key, value in node_metadata.get(node, {}).items():
            graph.nodes[node][key] = value


def _save_annotations(nodes, annotation_file: str,
                      node_metadata: Dict[str, Dict[str, Any]],
                      columns: List[str]) -> None:
    """Save node annotations to CSV."""
    with open(annotation_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID'] + columns)
        for node in nodes:
            meta = node_metadata.get(node, {})
            writer.writerow([node] + [meta.get(column, 'unknown') for column in columns])
