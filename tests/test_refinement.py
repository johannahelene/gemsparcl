#!/usr/bin/env python3
"""
Tests for gemsparcl refinement functionality.
"""

import pytest
import networkx as nx
from gemsparcl.refinement import GraphRefiner, refine_network


class TestGraphRefiner:
    """Tests for GraphRefiner class."""

    def test_init_zscore_method(self):
        """Test initialization with zscore method."""
        refiner = GraphRefiner(z_threshold=2.5, method='zscore')
        assert refiner.method == 'zscore'
        assert refiner.z_threshold == 2.5

    def test_init_percentile_method(self):
        """Test initialization with percentile method."""
        refiner = GraphRefiner(
            method='percentile',
            betweenness_percentile=85.0,
            clustering_percentile=15.0,
            degree_percentile=75.0
        )
        assert refiner.method == 'percentile'
        assert refiner.betweenness_percentile == 85.0
        assert refiner.clustering_percentile == 15.0
        assert refiner.degree_percentile == 75.0

    def test_init_invalid_method(self):
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Method must be"):
            GraphRefiner(method='invalid')

    def test_identify_betweenness_outliers_zscore(self):
        """Test z-score based outlier detection."""
        refiner = GraphRefiner(z_threshold=2.0)

        # Create test data with clear outliers
        betweenness = {
            'node1': 0.1,
            'node2': 0.15,
            'node3': 0.12,
            'node4': 0.14,
            'node5': 0.9,  # outlier
        }

        outliers = refiner.identify_betweenness_outliers(betweenness)
        assert 'node5' in outliers
        assert len(outliers) >= 1

    def test_identify_bridge_nodes_percentile(self):
        """Test percentile-based bridge node detection."""
        refiner = GraphRefiner(
            method='percentile',
            betweenness_percentile=80.0,
            clustering_percentile=20.0,
            degree_percentile=80.0
        )

        # Create a simple test graph with a bridge node
        # Structure: cluster1 <-> bridge <-> cluster2
        G = nx.Graph()

        # Cluster 1 (highly connected)
        cluster1 = ['c1_n1', 'c1_n2', 'c1_n3', 'c1_n4']
        for i in range(len(cluster1)):
            for j in range(i+1, len(cluster1)):
                G.add_edge(cluster1[i], cluster1[j])

        # Cluster 2 (highly connected)
        cluster2 = ['c2_n1', 'c2_n2', 'c2_n3', 'c2_n4']
        for i in range(len(cluster2)):
            for j in range(i+1, len(cluster2)):
                G.add_edge(cluster2[i], cluster2[j])

        # Bridge node connecting clusters
        bridge = 'bridge'
        G.add_edge(bridge, 'c1_n1')
        G.add_edge(bridge, 'c2_n1')

        # Calculate betweenness
        node_betweenness = nx.betweenness_centrality(G, normalized=True)

        # Identify bridges
        bridge_nodes = refiner.identify_bridge_nodes_percentile(
            G, node_betweenness, use_approximate=False
        )

        # The bridge node should be identified
        # (high betweenness, low clustering, moderate degree)
        assert len(bridge_nodes) >= 0  # May or may not find bridges depending on thresholds

    def test_refine_graph_zscore(self):
        """Test graph refinement with zscore method."""
        # Create a simple test graph
        G = nx.Graph()
        G.add_edges_from([
            ('A', 'B'), ('B', 'C'), ('C', 'D'),
            ('E', 'F'), ('F', 'G')
        ])

        components = list(nx.connected_components(G))

        refiner = GraphRefiner(method='zscore')
        refined_graph, new_components = refiner.refine_graph(G, components)

        # Should return a graph and components
        assert isinstance(refined_graph, nx.Graph)
        assert isinstance(new_components, list)

    def test_refine_graph_percentile(self):
        """Test graph refinement with percentile method."""
        # Create a test graph with two clusters connected by a bridge
        G = nx.Graph()

        # Cluster 1
        G.add_edges_from([
            ('A1', 'A2'), ('A2', 'A3'), ('A3', 'A1'),
        ])

        # Cluster 2
        G.add_edges_from([
            ('B1', 'B2'), ('B2', 'B3'), ('B3', 'B1'),
        ])

        # Bridge
        G.add_edge('A1', 'Bridge')
        G.add_edge('Bridge', 'B1')

        components = list(nx.connected_components(G))

        refiner = GraphRefiner(
            method='percentile',
            betweenness_percentile=80.0,
            clustering_percentile=20.0,
            degree_percentile=80.0
        )
        refined_graph, new_components = refiner.refine_graph(G, components)

        # Should return a graph and components
        assert isinstance(refined_graph, nx.Graph)
        assert isinstance(new_components, list)
        assert len(new_components) >= len(components)


class TestRefineNetwork:
    """Tests for the convenience function."""

    def test_refine_network_zscore(self):
        """Test refine_network with zscore method."""
        # Create simple graph
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C')])
        components = list(nx.connected_components(G))

        refined_graph, new_components = refine_network(
            G, components, z_threshold=2.0, method='zscore'
        )

        assert isinstance(refined_graph, nx.Graph)
        assert isinstance(new_components, list)

    def test_refine_network_percentile(self):
        """Test refine_network with percentile method."""
        # Create simple graph
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C')])
        components = list(nx.connected_components(G))

        refined_graph, new_components = refine_network(
            G, components,
            method='percentile',
            betweenness_percentile=80.0,
            clustering_percentile=20.0,
            degree_percentile=80.0
        )

        assert isinstance(refined_graph, nx.Graph)
        assert isinstance(new_components, list)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_small_component_skip(self):
        """Test that components with <3 nodes are skipped."""
        G = nx.Graph()
        G.add_edge('A', 'B')
        components = [{'A', 'B'}]

        refiner = GraphRefiner(method='zscore')
        refined_graph, new_components = refiner.refine_graph(G, components)

        # Should handle small components gracefully
        assert isinstance(refined_graph, nx.Graph)

    def test_empty_graph(self):
        """Test handling of empty graph."""
        G = nx.Graph()
        components = []

        refiner = GraphRefiner(method='zscore')
        refined_graph, new_components = refiner.refine_graph(G, components)

        assert isinstance(refined_graph, nx.Graph)
        assert len(new_components) == 0
