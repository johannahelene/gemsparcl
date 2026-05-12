"""
Tests for clustering functionality.
"""
import pytest
import pandas as pd
import networkx as nx
from pathlib import Path
import tempfile

from gemsparcl.clustering import (
    process_chunk,
    create_graph,
    save_clusters_csv,
    save_cluster_stats,
)


class TestProcessChunk:
    """Test chunk processing and filtering."""

    def test_process_chunk_basic(self):
        """Test basic chunk processing with threshold filtering."""
        # Create test chunk
        data = {
            'Query': ['genome_A', 'genome_A', 'genome_B'],
            'Reference': ['genome_B', 'genome_C', 'genome_C'],
            'Core': [0.99, 0.97, 0.985]
        }
        chunk = pd.DataFrame(data)
        threshold = 0.98

        genomes, distances, stats = process_chunk(chunk, threshold)

        # Check genomes found
        assert 'genome_A' in genomes
        assert 'genome_B' in genomes
        assert 'genome_C' in genomes
        assert len(genomes) == 3

        # Check filtering (only 2 pairs above 0.98)
        assert stats['kept_edges'] == 2
        assert stats['filtered_out'] == 1

    def test_process_chunk_empty(self):
        """Test processing empty chunk."""
        chunk = pd.DataFrame(columns=['Query', 'Reference', 'Core'])
        threshold = 0.98

        genomes, distances, stats = process_chunk(chunk, threshold)

        assert len(genomes) == 0
        assert len(distances) == 0
        assert stats['total_edges'] == 0


class TestCreateGraph:
    """Test graph creation and component finding."""

    def test_create_graph_simple(self):
        """Test creating a graph with two separate clusters."""
        genome_ids = {'A', 'B', 'C', 'D', 'E', 'F'}
        distances = {
            ('A', 'B'): 0.99,
            ('B', 'C'): 0.985,
            ('D', 'E'): 0.995,
            ('E', 'F'): 0.98,
        }

        graph, components = create_graph(genome_ids, distances)

        # Check graph properties
        assert graph.number_of_nodes() == 6
        assert graph.number_of_edges() == 4

        # Should have 2 components
        assert len(components) == 2

        # Check component sizes
        sizes = [len(c) for c in components]
        assert sorted(sizes) == [3, 3]

    def test_create_graph_with_singleton(self):
        """Test graph with a singleton genome (no connections)."""
        genome_ids = {'A', 'B', 'C', 'D'}
        distances = {
            ('A', 'B'): 0.99,
            ('B', 'C'): 0.985,
            # D has no connections
        }

        graph, components = create_graph(genome_ids, distances)

        # Check that all genomes are in graph
        assert graph.number_of_nodes() == 4
        assert graph.number_of_edges() == 2

        # Should have 2 components: one with A-B-C, one with D alone
        assert len(components) == 2
        sizes = [len(c) for c in components]
        assert sorted(sizes) == [1, 3]

    def test_create_graph_fully_connected(self):
        """Test graph where all genomes form one cluster."""
        genome_ids = {'A', 'B', 'C'}
        distances = {
            ('A', 'B'): 0.99,
            ('B', 'C'): 0.985,
            ('A', 'C'): 0.987,
        }

        graph, components = create_graph(genome_ids, distances)

        # Should be 1 component with all 3 genomes
        assert len(components) == 1
        assert len(components[0]) == 3


class TestSaveFunctions:
    """Test saving cluster results."""

    def test_save_clusters_csv(self, tmp_dir):
        """Test saving cluster assignments to CSV."""
        components = [
            {'genome_A', 'genome_B', 'genome_C'},
            {'genome_D', 'genome_E'},
            {'genome_F'},
        ]
        output_prefix = str(tmp_dir / "test_clusters")

        clusters_file = save_clusters_csv(components, output_prefix)

        # Check file was created
        assert Path(clusters_file).exists()

        # Read and verify content
        df = pd.read_csv(clusters_file)
        assert len(df) == 6
        assert set(df.columns) == {'genome_id', 'cluster'}

        # Check cluster assignments
        cluster_map = dict(zip(df['genome_id'], df['cluster']))
        assert cluster_map['genome_A'] == cluster_map['genome_B']
        assert cluster_map['genome_D'] == cluster_map['genome_E']
        assert cluster_map['genome_F'] != cluster_map['genome_A']

    def test_save_cluster_stats(self, tmp_dir):
        """Test saving cluster statistics."""
        components = [
            {'genome_A', 'genome_B', 'genome_C'},
            {'genome_D', 'genome_E'},
            {'genome_F'},
        ]
        output_prefix = str(tmp_dir / "test_stats")

        stats_file = save_cluster_stats(components, output_prefix)

        # Check file was created
        assert Path(stats_file).exists()

        # Read and check content
        with open(stats_file) as f:
            content = f.read()
            assert "Total clusters: 3" in content
            assert "Total genomes: 6" in content
            assert "Largest cluster: 3" in content
