"""
Tests for CLI functionality.
"""
import pytest
from click.testing import CliRunner
from gemsparcl.cli import main


class TestCLI:
    """Test command-line interface."""

    def test_version(self):
        """Test --version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output

    def test_help(self):
        """Test --help flag."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'gemsparcl' in result.output.lower()

    def test_cluster_help(self):
        """Test cluster subcommand help."""
        runner = CliRunner()
        result = runner.invoke(main, ['cluster', '--help'])
        assert result.exit_code == 0
        assert 'threshold' in result.output.lower()
        assert 'knn' in result.output.lower()

    def test_cluster_missing_input(self):
        """Test cluster fails without input file."""
        runner = CliRunner()
        result = runner.invoke(main, ['cluster', '-o', 'test_out'])
        assert result.exit_code != 0

    def test_cluster_invalid_threshold(self, tmp_dir):
        """Test cluster validates threshold range before clustering."""
        distances_file = tmp_dir / "distances.tsv"
        distances_file.write_text("genome_A\tgenome_B\t0.99\n")

        runner = CliRunner()
        result = runner.invoke(main, [
            'cluster',
            '--existing-distances', str(distances_file),
            '--threshold', '1.5',
        ])
        assert result.exit_code != 0
        assert "threshold" in result.output.lower()

    @pytest.mark.parametrize(
        "option,value",
        [
            ("--completeness-cutoff", "1.5"),
            ("--knn", "0"),
            ("--sketch-size", "0"),
            ("--kmer-length", "0"),
        ],
    )
    def test_cluster_invalid_numeric_options(self, tmp_dir, option, value):
        """Test numeric CLI options reject invalid ranges."""
        distances_file = tmp_dir / "distances.tsv"
        distances_file.write_text("genome_A\tgenome_B\t0.99\n")

        runner = CliRunner()
        result = runner.invoke(main, [
            'cluster',
            '--existing-distances', str(distances_file),
            option, value,
        ])

        assert result.exit_code != 0
        assert option in result.output


class TestCLIOptions:
    """Test various CLI option combinations."""

    def test_use_inverted_index_flag(self):
        """Test that --use-inverted-index flag is recognized."""
        runner = CliRunner()
        result = runner.invoke(main, ['cluster', '--help'])
        assert '--use-inverted-index' in result.output

    def test_refine_flag(self):
        """Test that --refine flag is recognized."""
        runner = CliRunner()
        result = runner.invoke(main, ['cluster', '--help'])
        assert '--refine' in result.output

    def test_visualise_command(self):
        """Test that visualise is a recognised command with expected options."""
        runner = CliRunner()
        result = runner.invoke(main, ['visualise', '--help'])
        assert result.exit_code == 0
        assert '--existing-distances' in result.output
        assert '--clusters-file' in result.output
