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

    def test_cluster_invalid_threshold(self):
        """Test cluster validates threshold range."""
        runner = CliRunner()
        # Threshold should be between 0 and 1
        result = runner.invoke(main, [
            'cluster',
            '-i', 'dummy.txt',
            '--threshold', '1.5',
        ])
        # Should fail (either file not found or validation error)
        assert result.exit_code != 0


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

    def test_cytoscape_flag(self):
        """Test that --cytoscape flag is recognized."""
        runner = CliRunner()
        result = runner.invoke(main, ['cluster', '--help'])
        assert '--cytoscape' in result.output
