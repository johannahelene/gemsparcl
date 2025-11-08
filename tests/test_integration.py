"""
Integration tests for full gemsparcl workflows.
"""
import pytest
import shutil
from pathlib import Path
from click.testing import CliRunner

from gemsparcl.cli import main


# Path to E. coli test dataset (adjust if needed)
ECOLI_RFILE = Path("/hps/nobackup/rdf/metagenomics/research-team/johanna/projects/PhD_main/analysis/2025-06-17-ecoli/ecoli.rfile")


@pytest.mark.skipif(
    not ECOLI_RFILE.exists(),
    reason="E. coli test dataset not available"
)
@pytest.mark.skipif(
    not shutil.which('sketchlib') and
    not Path('/hps/nobackup/rdf/metagenomics/research-team/johanna/projects/PhD_main/bin/sketchlib.rust/target/release/sketchlib').exists(),
    reason="sketchlib not available"
)
class TestEcoliIntegration:
    """Integration tests using E. coli dataset."""

    def test_ecoli_standard_mode(self, tmp_dir):
        """Test full pipeline with E. coli data (standard mode)."""
        runner = CliRunner()
        output_prefix = str(tmp_dir / "ecoli_test")

        result = runner.invoke(main, [
            'cluster',
            '-i', str(ECOLI_RFILE),
            '-o', output_prefix,
            '-k', '21',
            '--threads', '4',
            '--knn', '10',  # Use small knn for faster testing
        ])

        # Check command succeeded
        assert result.exit_code == 0

        # Check output files were created
        assert (tmp_dir / "ecoli_test_clusters.csv").exists()
        assert (tmp_dir / "ecoli_test_cluster_stats.txt").exists()

    def test_ecoli_inverted_index_mode(self, tmp_dir):
        """Test full pipeline with E. coli data (inverted index mode)."""
        runner = CliRunner()
        output_prefix = str(tmp_dir / "ecoli_inverted")

        result = runner.invoke(main, [
            'cluster',
            '-i', str(ECOLI_RFILE),
            '-o', output_prefix,
            '-k', '21',
            '--threads', '4',
            '--knn', '10',
            '--use-inverted-index',
            '--keep-intermediates',  # Keep files to verify they were created
        ])

        # Check command succeeded
        assert result.exit_code == 0

        # Check output files were created
        assert (tmp_dir / "ecoli_inverted_clusters.csv").exists()
        assert (tmp_dir / "ecoli_inverted_cluster_stats.txt").exists()

        # Check inverted index files were created
        assert (tmp_dir / "ecoli_inverted.ski").exists()
        assert (tmp_dir / "ecoli_inverted.skq").exists()

    def test_ecoli_with_refinement(self, tmp_dir):
        """Test full pipeline with refinement."""
        runner = CliRunner()
        output_prefix = str(tmp_dir / "ecoli_refined")

        result = runner.invoke(main, [
            'cluster',
            '-i', str(ECOLI_RFILE),
            '-o', output_prefix,
            '-k', '21',
            '--threads', '4',
            '--knn', '10',
            '--refine',
        ])

        # Check command succeeded
        assert result.exit_code == 0

        # Check both regular and refined outputs exist
        assert (tmp_dir / "ecoli_refined_clusters.csv").exists()
        assert (tmp_dir / "ecoli_refined_refined_clusters.csv").exists()

    @pytest.mark.slow
    def test_ecoli_full_features(self, tmp_dir):
        """Test all features together (marked as slow)."""
        runner = CliRunner()
        output_prefix = str(tmp_dir / "ecoli_full")

        result = runner.invoke(main, [
            'cluster',
            '-i', str(ECOLI_RFILE),
            '-o', output_prefix,
            '-k', '21',
            '--threads', '4',
            '--knn', '10',
            '--use-inverted-index',
            '--refine',
            '--cytoscape',
            '--keep-intermediates',
        ])

        # Check command succeeded
        assert result.exit_code == 0

        # Check various output files exist
        assert (tmp_dir / "ecoli_full_clusters.csv").exists()
        assert (tmp_dir / "ecoli_full_refined_clusters.csv").exists()

        # Check for cytoscape files (may be multiple depending on network size)
        graphml_files = list(tmp_dir.glob("ecoli_full*.graphml"))
        assert len(graphml_files) > 0


class TestClusteringCorrectness:
    """Test clustering produces expected results."""

    def test_mock_clustering(self, tmp_dir):
        """Test clustering with mock distance data produces correct clusters."""
        # Create a mock distance file
        dist_file = tmp_dir / "mock.dists"
        with open(dist_file, 'w') as f:
            # Two clear clusters: A-B-C and D-E-F
            f.write("genome_A\tgenome_B\t0.99\n")
            f.write("genome_B\tgenome_C\t0.985\n")
            f.write("genome_A\tgenome_C\t0.987\n")
            f.write("genome_D\tgenome_E\t0.995\n")
            f.write("genome_E\tgenome_F\t0.98\n")
            f.write("genome_D\tgenome_F\t0.982\n")

        # Import and run clustering directly
        from gemsparcl.clustering import cluster_genomes

        clusters_file, stats_file, graph, components = cluster_genomes(
            str(dist_file),
            str(tmp_dir / "mock"),
            num_processes=1,
            threshold=0.98,
        )

        # Should have 2 clusters
        assert len(components) == 2

        # Each cluster should have 3 genomes
        sizes = sorted([len(c) for c in components])
        assert sizes == [3, 3]

        # Verify output files exist
        assert Path(clusters_file).exists()
        assert Path(stats_file).exists()
