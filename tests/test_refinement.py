#!/usr/bin/env python3
"""Tests for gemsparcl refinement functionality."""

import pytest
import networkx as nx
from gemsparcl.refinement import refine_network, _identify_bridge_nodes, _identify_bridge_edges


def _make_two_clusters_with_bridge():
    """Create a graph with two dense clusters connected by a bridge node."""
    G = nx.Graph()

    # Cluster 1 (fully connected clique)
    cluster1 = ['c1_n1', 'c1_n2', 'c1_n3', 'c1_n4']
    for i in range(len(cluster1)):
        for j in range(i + 1, len(cluster1)):
            G.add_edge(cluster1[i], cluster1[j])

    # Cluster 2 (fully connected clique)
    cluster2 = ['c2_n1', 'c2_n2', 'c2_n3', 'c2_n4']
    for i in range(len(cluster2)):
        for j in range(i + 1, len(cluster2)):
            G.add_edge(cluster2[i], cluster2[j])

    # Bridge node connecting the two clusters
    G.add_edge('bridge', 'c1_n1')
    G.add_edge('bridge', 'c2_n1')

    return G


class TestIdentifyBridgeNodes:
    """Tests for _identify_bridge_nodes."""

    def test_finds_bridge_in_two_cluster_graph(self):
        G = _make_two_clusters_with_bridge()
        component = set(G.nodes())
        subgraph = G.subgraph(component)
        node_betweenness = nx.betweenness_centrality(subgraph, normalized=True)

        bridge_nodes = _identify_bridge_nodes(
            subgraph, node_betweenness,
            betweenness_percentile=80.0,
            clustering_percentile=20.0,
            degree_percentile=20.0
        )

        assert 'bridge' in bridge_nodes

    def test_skips_small_subgraph(self):
        G = nx.Graph()
        G.add_edge('A', 'B')
        subgraph = G.subgraph({'A', 'B'})
        node_betweenness = nx.betweenness_centrality(subgraph, normalized=True)

        bridge_nodes = _identify_bridge_nodes(
            subgraph, node_betweenness,
            betweenness_percentile=80.0,
            clustering_percentile=20.0,
            degree_percentile=20.0
        )

        assert bridge_nodes == []


class TestIdentifyBridgeEdges:
    """Tests for _identify_bridge_edges."""

    def test_finds_high_betweenness_edges(self):
        G = _make_two_clusters_with_bridge()
        edge_betweenness = nx.edge_betweenness_centrality(G, normalized=True)

        bridge_edges = _identify_bridge_edges(edge_betweenness, percentile=80.0)

        # The edges connecting bridge node to clusters should have high betweenness
        assert len(bridge_edges) >= 1

    def test_skips_single_edge(self):
        edge_betweenness = {('A', 'B'): 1.0}
        bridge_edges = _identify_bridge_edges(edge_betweenness, percentile=80.0)
        assert bridge_edges == []


class TestRefineNetwork:
    """Tests for the main refine_network function."""

    def test_splits_bridged_clusters(self):
        G = _make_two_clusters_with_bridge()
        components = list(nx.connected_components(G))
        assert len(components) == 1  # one big component before refinement

        refined_graph, new_components = refine_network(G, components)

        # Should split into more components after removing bridge
        assert len(new_components) > 1

    def test_mutates_graph_in_place(self):
        G = _make_two_clusters_with_bridge()
        original_edge_count = G.number_of_edges()
        components = list(nx.connected_components(G))

        refined_graph, _ = refine_network(G, components)

        # Graph is modified in place to avoid copying large graphs
        assert refined_graph is G
        assert G.number_of_edges() < original_edge_count

    def test_small_components_skipped(self):
        G = nx.Graph()
        G.add_edge('A', 'B')
        components = [{'A', 'B'}]

        refined_graph, new_components = refine_network(G, components)

        # Should pass through unchanged
        assert len(new_components) == 1
        assert {'A', 'B'} in new_components

    def test_empty_graph(self):
        G = nx.Graph()
        components = []

        refined_graph, new_components = refine_network(G, components)

        assert isinstance(refined_graph, nx.Graph)
        assert len(new_components) == 0

    def test_clean_cluster_not_fragmented(self):
        """A single well-connected clique should not be split."""
        G = nx.Graph()
        nodes = [f'n{i}' for i in range(6)]
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                G.add_edge(nodes[i], nodes[j])

        components = [set(nodes)]

        refined_graph, new_components = refine_network(G, components)

        # A perfect clique has uniform betweenness and max clustering;
        # no node should satisfy all three bridge criteria
        non_singleton = [c for c in new_components if len(c) > 1]
        assert len(non_singleton) == 1
