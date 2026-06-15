"""
Tests for Cytoscape GraphML export.
"""
import csv

import networkx as nx

from gemsparcl.cytoscape import export_network_for_cytoscape


def _build_graph():
    graph = nx.Graph()
    graph.add_edge('A', 'B', weight=0.99)
    graph.add_node('C')
    components = [{'A', 'B'}, {'C'}]
    return graph, components


class TestExportNetworkForCytoscape:
    """Test GraphML and annotation export with node metadata."""

    def test_cluster_id_only(self, tmp_path):
        graph, components = _build_graph()
        node_metadata = {
            'A': {'cluster_id': 1},
            'B': {'cluster_id': 1},
            'C': {'cluster_id': 2},
        }
        output_prefix = str(tmp_path / "vis")

        result = export_network_for_cytoscape(graph, components, output_prefix, node_metadata)

        assert len(result['graphml_files']) == 1
        g = nx.read_graphml(result['graphml_files'][0])
        assert g.nodes['A']['cluster_id'] == 1
        assert g.nodes['C']['cluster_id'] == 2

        with open(result['annotation_files'][0]) as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ['ID', 'cluster_id']
            rows = {row['ID']: row for row in reader}
        assert rows['A']['cluster_id'] == '1'
        assert rows['C']['cluster_id'] == '2'

    def test_query_and_reference_metadata(self, tmp_path):
        graph, components = _build_graph()
        node_metadata = {
            'A': {'cluster_id': 1, 'is_query': False, 'note': 'existing'},
            'B': {'cluster_id': 1, 'is_query': False, 'note': 'existing'},
            'C': {'cluster_id': 2, 'is_query': True, 'note': 'assigned'},
        }
        output_prefix = str(tmp_path / "vis")

        result = export_network_for_cytoscape(graph, components, output_prefix, node_metadata)

        g = nx.read_graphml(result['graphml_files'][0])
        assert g.nodes['C']['is_query'] is True
        assert g.nodes['C']['note'] == 'assigned'
        assert g.nodes['A']['is_query'] is False

        with open(result['annotation_files'][0]) as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ['ID', 'cluster_id', 'is_query', 'note']
            rows = {row['ID']: row for row in reader}
        assert rows['C']['is_query'] == 'True'
        assert rows['C']['note'] == 'assigned'

    def test_no_metadata_defaults_to_cluster_id(self, tmp_path):
        graph, components = _build_graph()
        output_prefix = str(tmp_path / "vis")

        result = export_network_for_cytoscape(graph, components, output_prefix, None)

        with open(result['annotation_files'][0]) as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ['ID', 'cluster_id']
            rows = list(reader)
        assert all(row['cluster_id'] == 'unknown' for row in rows)
