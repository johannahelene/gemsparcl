"""
Tests for sketching functionality.
"""
import pytest
from pathlib import Path
import shutil

from gemsparcl.sketching import (
    check_sketchlib,
    validate_input_file,
    normalize_genome_ids,
)


class TestCheckSketchlib:
    """Test sketchlib availability checking."""

    def test_check_sketchlib_finds_binary(self, sketchlib_available):
        """Test that check_sketchlib finds the binary."""
        if not sketchlib_available:
            pytest.skip("sketchlib not available")

        sketchlib_path = check_sketchlib()
        assert sketchlib_path is not None
        assert Path(sketchlib_path).exists()


class TestValidateInputFile:
    """Test input file validation."""

    def test_validate_nonexistent_file(self):
        """Test validation fails for non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_input_file("/nonexistent/file.txt")

    def test_validate_empty_file(self, tmp_dir):
        """Test validation fails for empty file."""
        empty_file = tmp_dir / "empty.txt"
        empty_file.touch()

        with pytest.raises(ValueError, match="empty"):
            validate_input_file(str(empty_file))

    def test_validate_invalid_format(self, tmp_dir):
        """Test validation fails for invalid rfile format."""
        invalid_file = tmp_dir / "invalid.txt"
        with open(invalid_file, 'w') as f:
            f.write("genome_only_one_column\n")
            f.write("genome2 path2 extra_column\n")

        with pytest.raises(ValueError, match="2 tab-separated columns"):
            validate_input_file(str(invalid_file))

    def test_validate_valid_file(self, tmp_dir):
        """Test validation passes for valid rfile."""
        # Create dummy genome files
        genome1 = tmp_dir / "genome1.fna"
        genome2 = tmp_dir / "genome2.fna"
        genome1.write_text(">seq1\nATCG\n")
        genome2.write_text(">seq2\nGCTA\n")

        # Create valid rfile
        rfile = tmp_dir / "genomes.rfile"
        with open(rfile, 'w') as f:
            f.write(f"genome1\t{genome1}\n")
            f.write(f"genome2\t{genome2}\n")

        # Should not raise
        validate_input_file(str(rfile))

    def test_validate_with_comments(self, tmp_dir):
        """Test validation handles comment lines."""
        genome1 = tmp_dir / "genome1.fna"
        genome1.write_text(">seq1\nATCG\n")

        rfile = tmp_dir / "genomes.rfile"
        with open(rfile, 'w') as f:
            f.write("# This is a comment\n")
            f.write(f"genome1\t{genome1}\n")
            f.write("\n")  # Empty line

        # Should not raise
        validate_input_file(str(rfile))


class TestNormalizeGenomeIds:
    """Test stripping FASTA extensions from genome IDs."""

    def test_strips_known_extensions(self, tmp_dir):
        """fna/fasta/fa, with or without .gz, are stripped from column 1 only."""
        input_file = tmp_dir / "rfile.tsv"
        with open(input_file, 'w') as f:
            f.write("genome1.fna\t/data/genome1.fna\n")
            f.write("genome2.fasta.gz\t/data/genome2.fasta.gz\n")
            f.write("genome3.fa.gz\t/data/genome3.fa.gz\n")
            f.write("genome4\t/data/genome4.fna\n")

        output_file = tmp_dir / "rfile.normalized.tsv"
        result_path = normalize_genome_ids(str(input_file), str(output_file))

        assert result_path == str(output_file)
        lines = output_file.read_text().splitlines()
        assert lines[0] == "genome1\t/data/genome1.fna"
        assert lines[1] == "genome2\t/data/genome2.fasta.gz"
        assert lines[2] == "genome3\t/data/genome3.fa.gz"
        assert lines[3] == "genome4\t/data/genome4.fna"

    def test_leaves_other_extensions_and_comments_untouched(self, tmp_dir):
        """Unrecognised extensions, comments, and blank lines pass through unchanged."""
        input_file = tmp_dir / "rfile.tsv"
        with open(input_file, 'w') as f:
            f.write("# comment line\n")
            f.write("\n")
            f.write("genome1.fastq.gz\t/data/genome1.fastq.gz\n")
            f.write("genome2.FNA\t/data/genome2.FNA\n")

        output_file = tmp_dir / "rfile.normalized.tsv"
        normalize_genome_ids(str(input_file), str(output_file))

        lines = output_file.read_text().splitlines()
        assert lines[0] == "# comment line"
        assert lines[1] == ""
        assert lines[2] == "genome1.fastq.gz\t/data/genome1.fastq.gz"
        assert lines[3] == "genome2.FNA\t/data/genome2.FNA"

    def test_strips_completeness_file(self, tmp_dir):
        """Works on two-column completeness files too."""
        input_file = tmp_dir / "completeness.tsv"
        with open(input_file, 'w') as f:
            f.write("genome1.fna.gz\t0.95\n")
            f.write("genome2\t1.0\n")

        output_file = tmp_dir / "completeness.normalized.tsv"
        normalize_genome_ids(str(input_file), str(output_file))

        lines = output_file.read_text().splitlines()
        assert lines[0] == "genome1\t0.95"
        assert lines[1] == "genome2\t1.0"


@pytest.mark.skipif(
    not shutil.which('sketchlib') and
    not Path('/hps/nobackup/rdf/metagenomics/research-team/johanna/projects/PhD_main/bin/sketchlib.rust/target/release/sketchlib').exists(),
    reason="sketchlib not available"
)
class TestSketchingIntegration:
    """Integration tests requiring sketchlib (skipped if not available)."""

    def test_sketching_pipeline_basic(self, tmp_dir, small_test_data):
        """Test basic sketching pipeline if test data available."""
        if small_test_data is None:
            pytest.skip("No test data available")

        # This test would run full sketching - expensive, so we skip for now
        # In real tests, you'd have a tiny test dataset (3-5 genomes)
        pytest.skip("Full integration test - implement with tiny dataset")
