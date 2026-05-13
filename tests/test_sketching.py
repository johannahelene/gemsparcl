"""
Tests for sketching functionality.
"""
import pytest
from pathlib import Path
import shutil

from gemsparcl.sketching import (
    check_sketchlib,
    validate_input_file,
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
