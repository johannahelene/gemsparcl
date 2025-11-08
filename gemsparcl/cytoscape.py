#!/usr/bin/env python3
"""Cytoscape GraphML export for network visualization."""

import logging
import csv
import os
from typing import List, Set, Dict

import networkx as nx

logger = logging.getLogger('gemsparcl.cytoscape')


def export_network_for_cytoscape(graph: nx.Graph, components: List[Set[str]],
                                output_prefix: str,
                                cluster_assignments: Dict[str, int] = None) -> Dict[str, List[str]]:
    """Export network to Cytoscape format, splitting large components."""

    logger.info(f"Exporting network ({graph.number_of_nodes()} nodes) to Cytoscape")

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
            nx.write_graphml(subgraph, graphml_file)
            _save_annotations(subgraph.nodes(), annotation_file, cluster_assignments)

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
                nx.write_graphml(batch_graph, graphml_file)
                _save_annotations(batch_graph.nodes(), annotation_file, cluster_assignments)

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
            nx.write_graphml(batch_graph, graphml_file)
            _save_annotations(batch_graph.nodes(), annotation_file, cluster_assignments)

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


def _save_annotations(nodes, annotation_file: str, cluster_assignments: Dict[str, int] = None) -> None:
    """Save node annotations to CSV."""
    with open(annotation_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'cluster_id'])
        for node in nodes:
            cluster_id = cluster_assignments.get(node, 'unknown') if cluster_assignments else 'unknown'
            writer.writerow([node, cluster_id])
