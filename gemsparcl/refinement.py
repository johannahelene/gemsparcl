#!/usr/bin/env python3
"""Network refinement to remove contamination bridges."""

import logging
from typing import List, Set, Tuple, Dict

import networkx as nx
import numpy as np

logger = logging.getLogger('gemsparcl.refinement')


def refine_network(graph: nx.Graph, components: List[Set],
                  sample_size: int = 1000,
                  large_component_threshold: int = 10000) -> Tuple[nx.Graph, List[Set]]:
    """Refine network by removing bridge nodes and edges that connect distinct clusters.

    Contaminated genomes create artefactual bridges between distinct genomic lineages.

    Step 1 — jump detection on betweenness: sort node betweenness values and find the
    largest gap between consecutive values. Everything above that gap is a candidate.
    If there is no meaningful jump (all values are similar), nothing is flagged.

    Step 2 — sanity check on candidates: a true bridge should also have below-median
    degree (few genuine connections to either side). Clustering is not used.

    Edges are handled the same way: jump detection on edge betweenness centrality.

    If a bridge edge connects two bridge nodes, an edge-only cut is tried first.
    Full node isolation is used as a fallback only if the edge cut alone is insufficient.
    """

    logger.info("Refining network")

    edges_to_remove = []
    nodes_to_isolate = set()

    for component in components:
        if len(component) < 3:
            continue

        subgraph = graph.subgraph(component)
        use_approx = len(component) > large_component_threshold

        k = min(sample_size, len(component)) if use_approx else None
        node_betweenness = nx.betweenness_centrality(subgraph, k=k, normalized=True)
        edge_betweenness = nx.edge_betweenness_centrality(subgraph, k=k, normalized=True)

        bridge_nodes = _identify_bridge_nodes(subgraph, node_betweenness)
        bridge_edges = _identify_bridge_edges(edge_betweenness)

        # If a bridge edge connects two bridge nodes, try cutting the edge first.
        # Only fall back to full node isolation if the edge cut alone didn't split
        # the component (i.e. there were multiple inter-cluster connections).
        bridge_node_set = set(bridge_nodes)
        resolved_nodes = set()
        for edge in bridge_edges:
            u, v = edge
            if u in bridge_node_set and v in bridge_node_set:
                test = graph.subgraph(component).copy()
                test.remove_edge(u, v)
                if nx.number_connected_components(test) > 1:
                    resolved_nodes.add(u)
                    resolved_nodes.add(v)
                    logger.debug(f"Bridge edge between bridge nodes resolved by edge cut: {u} -- {v}")
                else:
                    logger.debug(f"Bridge edge between bridge nodes — edge cut insufficient, will isolate nodes: {u} -- {v}")

        nodes_to_isolate.update(n for n in bridge_nodes if n not in resolved_nodes)
        edges_to_remove.extend(bridge_edges)

    # Remove all edges connected to bridge nodes (isolate them as singletons)
    edges_removed_from_nodes = 0
    for node in nodes_to_isolate:
        if node in graph:
            for edge in list(graph.edges(node)):
                if graph.has_edge(*edge):
                    graph.remove_edge(*edge)
                    edges_removed_from_nodes += 1

    # Remove bridge edges
    edges_removed = 0
    for edge in edges_to_remove:
        if graph.has_edge(*edge):
            graph.remove_edge(*edge)
            edges_removed += 1

    new_components = list(nx.connected_components(graph))

    logger.info(f"Isolated {len(nodes_to_isolate)} bridge nodes (removed {edges_removed_from_nodes} edges)")
    logger.info(f"Removed {edges_removed} bridge edges")
    logger.info(f"Components: {len(components)} -> {len(new_components)}")

    return graph, new_components


def _jump_threshold(values: np.ndarray):
    """Return the value at the largest gap in sorted values, or None if no jump exists.

    Finds the largest difference between consecutive sorted values. Everything strictly
    above that gap position is considered an outlier. Returns None if all values are
    identical (no gap possible).
    """
    sorted_vals = np.sort(values)
    gaps = np.diff(sorted_vals)
    if gaps.max() == 0:
        return None
    idx = np.argmax(gaps)
    return sorted_vals[idx]  # threshold: flag values > this


def _identify_bridge_nodes(subgraph: nx.Graph, node_betweenness: Dict) -> List:
    """Identify bridge nodes via betweenness jump detection + median degree check."""
    if len(subgraph) < 3:
        return []

    nodes = list(node_betweenness.keys())
    betweenness_values = np.array([node_betweenness[n] for n in nodes])

    # Step 1: find candidates via jump detection on betweenness
    threshold = _jump_threshold(betweenness_values)
    if threshold is None:
        return []

    candidate_mask = betweenness_values > threshold
    if not candidate_mask.any():
        return []

    # Step 2: sanity check — candidates must also have below-median degree
    degrees = dict(subgraph.degree())
    max_degree = len(subgraph) - 1
    degree_values = np.array([degrees[n] / max_degree if max_degree > 0 else 0 for n in nodes])

    median_degree = np.median(degree_values)

    logger.debug(f"Betweenness jump threshold: {threshold:.6f} — {candidate_mask.sum()} candidates")
    logger.debug(f"Median degree: {median_degree:.6f}")

    bridge_nodes = []
    for i, node in enumerate(nodes):
        if candidate_mask[i] and degree_values[i] <= median_degree:
            bridge_nodes.append(node)

    return bridge_nodes


def _identify_bridge_edges(edge_betweenness: Dict) -> List:
    """Identify bridge edges via jump detection on edge betweenness."""
    if len(edge_betweenness) < 2:
        return []

    edges = list(edge_betweenness.keys())
    values = np.array(list(edge_betweenness.values()))

    threshold = _jump_threshold(values)
    if threshold is None:
        return []

    return [edges[i] for i, v in enumerate(values) if v > threshold]
