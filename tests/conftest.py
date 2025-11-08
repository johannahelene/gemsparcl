"""
Pytest configuration and fixtures for gemsparcl tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def small_test_data():
    """
    Path to small test dataset.
    You can create a minimal test dataset with 5-10 genomes.
    """
    # This should point to a small test dataset in the repo
    # For now, we'll use the test_genomes.txt if it exists
    test_file = Path(__file__).parent.parent / "test_genomes.txt"
    if test_file.exists():
        return test_file
    return None


@pytest.fixture
def mock_distances():
    """Mock distance data for testing clustering without running sketchlib."""
    # Simple test network: 6 genomes forming 2 clusters
    return [
        ("genome_A", "genome_B", 0.99),
        ("genome_B", "genome_C", 0.985),
        ("genome_D", "genome_E", 0.995),
        ("genome_E", "genome_F", 0.98),
    ]


@pytest.fixture
def expected_clusters():
    """Expected clustering for mock_distances fixture."""
    return {
        "genome_A": 1,
        "genome_B": 1,
        "genome_C": 1,
        "genome_D": 2,
        "genome_E": 2,
        "genome_F": 2,
    }


@pytest.fixture
def sketchlib_available():
    """Check if sketchlib is available in PATH."""
    return shutil.which('sketchlib') is not None or \
           Path('/hps/nobackup/rdf/metagenomics/research-team/johanna/projects/PhD_main/bin/sketchlib.rust/target/release/sketchlib').exists()
