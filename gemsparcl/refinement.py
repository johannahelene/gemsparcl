#!/usr/bin/env python3
"""Network refinement to remove contamination bridges."""

import logging
from typing import List, Set, Tuple, Dict

import networkx as nx
import numpy as np

logger = logging.getLogger('gemsparcl.refinement')


def refine_network(graph: nx.Graph, components: List[Set],
                  sample_size: int = 1000,
                  large_component_threshold: int = 10000,
                  betweenness_percentile: float = 80.0,
                  clustering_percentile: float = 20.0,
                  degree_percentile: float = 80.0,
                  **kwargs) -> Tuple[nx.Graph, List[Set]]:
    """Refine network by removing bridge edges that connect distinct clusters."""

    logger.info("Refining network")

    edges_to_remove = []

    for component in components:
        if len(component) < 3:
            continue

        subgraph = graph.subgraph(component).copy()
        use_approx = len(component) > large_component_threshold

        # Calculate betweenness
        k = min(sample_size, len(component)) if use_approx else None
        node_betweenness = nx.betweenness_centrality(subgraph, k=k, normalized=True)
        edge_betweenness = nx.edge_betweenness_centrality(subgraph, k=k, normalized=True)

        # Identify bridge nodes and edges
        bridge_nodes = _identify_bridge_nodes(
            subgraph, node_betweenness,
            betweenness_percentile, clustering_percentile, degree_percentile
        )
        bridge_edges = _identify_bridge_edges(edge_betweenness, betweenness_percentile)

        edges_to_remove.extend(bridge_edges)

    # Remove bridge edges
    edges_removed = 0
    for edge in edges_to_remove:
        if graph.has_edge(*edge):
            graph.remove_edge(*edge)
            edges_removed += 1

    # Recalculate components
    new_components = list(nx.connected_components(graph))

    logger.info(f"Removed {edges_removed} bridge edges")
    logger.info(f"Components: {len(components)} -> {len(new_components)}")

    return graph, new_components


def _identify_bridge_nodes(subgraph: nx.Graph, node_betweenness: Dict,
                           betweenness_percentile: float,
                           clustering_percentile: float,
                           degree_percentile: float) -> List:
    """Identify bridge nodes using percentile thresholds."""
    if len(subgraph) < 3:
        return []

    nodes = list(node_betweenness.keys())
    betweenness_values = np.array([node_betweenness[n] for n in nodes])

    clustering_dict = nx.clustering(subgraph)
    clustering_values = np.array([clustering_dict[n] for n in nodes])

    degrees = dict(subgraph.degree())
    max_degree = len(subgraph) - 1
    degree_values = np.array([degrees[n] / max_degree if max_degree > 0 else 0 for n in nodes])

    # Calculate thresholds
    b_thresh = np.percentile(betweenness_values, betweenness_percentile)
    c_thresh = np.percentile(clustering_values, clustering_percentile)
    d_thresh = np.percentile(degree_values, degree_percentile)

    # Identify bridges: high betweenness, low clustering, moderate degree
    bridge_nodes = []
    for i, node in enumerate(nodes):
        if (betweenness_values[i] >= b_thresh and
            clustering_values[i] <= c_thresh and
            degree_values[i] <= d_thresh):
            bridge_nodes.append(node)

    return bridge_nodes


def _identify_bridge_edges(edge_betweenness: Dict, percentile: float) -> List:
    """Identify bridge edges using percentile threshold."""
    if len(edge_betweenness) < 2:
        return []

    edges = list(edge_betweenness.keys())
    values = np.array(list(edge_betweenness.values()))

    threshold = np.percentile(values, percentile)
    bridge_edges = [edges[i] for i, v in enumerate(values) if v >= threshold]

    return bridge_edges
