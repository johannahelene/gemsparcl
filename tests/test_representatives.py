"""
Tests for representative selection functionality.
"""
import pytest
import csv
from pathlib import Path

from gemsparcl.representatives import (
    select_representatives,
    select_representatives_fast,
    select_representatives_GTDB,
    select_representatives_dereplicate,
)


def _make_clusters_csv(path, components):
    """Helper: write a clusters CSV from a list of components."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['genome_id', 'cluster'])
        for cluster_num, component in enumerate(components, 1):
            for genome in component:
                writer.writerow([genome, cluster_num])


def _make_completeness_file(path, completeness_dict):
    """Helper: write a tab-separated completeness file."""
    with open(path, 'w') as f:
        for genome, score in completeness_dict.items():
            f.write(f"{genome}\t{score}\n")


# ---------------------------------------------------------------------------
# select_representatives_fast
# ---------------------------------------------------------------------------

class TestSelectRepresentativesFast:

    def test_returns_highest_completeness(self):
        """Genome with highest completeness score should be selected."""
        component = {'genome_A', 'genome_B', 'genome_C'}
        completeness_dict = {'genome_A': 0.70, 'genome_B': 0.95, 'genome_C': 0.80}

        reps = select_representatives_fast(component, completeness_dict)

        assert 'genome_B' in reps

    def test_returns_correct_count_small_component(self):
        """Component of <500 genomes should return exactly 1 rep."""
        component = {f'genome_{i}' for i in range(499)}
        completeness_dict = {}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 1

    def test_returns_correct_count_large_component(self):
        """Component of 1000 genomes should return exactly 2 reps."""
        component = {f'genome_{i}' for i in range(1000)}
        completeness_dict = {}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 2

    def test_boundary_500(self):
        """Component of exactly 500 genomes: 500 // 500 = 1 rep."""
        component = {f'genome_{i}' for i in range(500)}
        completeness_dict = {}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 1

    def test_boundary_1000(self):
        """Component of exactly 1000 genomes: 1000 // 500 = 2 reps."""
        component = {f'genome_{i}' for i in range(1000)}
        completeness_dict = {}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 2

    def test_partial_completeness(self):
        """Genome with a score beats genomes with no score (defaults to 0)."""
        component = {'genome_A', 'genome_B', 'genome_C'}
        # Only genome_C has a score; A and B default to 0
        completeness_dict = {'genome_C': 0.85}

        reps = select_representatives_fast(component, completeness_dict)

        assert 'genome_C' in reps

    def test_no_completeness_data(self):
        """With no completeness data, random selection should still return valid genomes."""
        component = {'genome_A', 'genome_B', 'genome_C'}
        completeness_dict = {}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 1
        assert reps[0] in component

    def test_single_genome_component(self):
        """Single genome component should always return that genome."""
        component = {'genome_A'}
        completeness_dict = {'genome_A': 0.95}

        reps = select_representatives_fast(component, completeness_dict)

        assert reps == ['genome_A']

    def test_single_genome_no_completeness(self):
        """Single genome with no completeness data should still return that genome."""
        component = {'genome_A'}
        completeness_dict = {}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 1
        assert reps[0] == 'genome_A'

    def test_completeness_tie(self):
        """Two genomes with identical scores: exactly 1 rep should be returned."""
        component = {'genome_A', 'genome_B'}
        completeness_dict = {'genome_A': 0.90, 'genome_B': 0.90}

        reps = select_representatives_fast(component, completeness_dict)

        assert len(reps) == 1
        assert reps[0] in component

    def test_reps_are_subset_of_component(self):
        """All returned representatives must belong to the input component."""
        component = {'genome_A', 'genome_B', 'genome_C', 'genome_D', 'genome_E'}
        completeness_dict = {'genome_A': 0.9, 'genome_C': 0.7}

        reps = select_representatives_fast(component, completeness_dict)

        for rep in reps:
            assert rep in component


# ---------------------------------------------------------------------------
# select_representatives (orchestrator)
# ---------------------------------------------------------------------------

class TestSelectRepresentatives:

    def test_creates_output_file(self, tmp_dir):
        """Output representatives file should be created."""
        components = [{'genome_A', 'genome_B'}, {'genome_C'}]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        result = select_representatives(components, None, output_prefix)

        assert Path(result).exists()

    def test_output_file_contains_valid_genomes(self, tmp_dir):
        """Every genome in the output file should belong to one of the components."""
        components = [{'genome_A', 'genome_B', 'genome_C'}, {'genome_D', 'genome_E'}]
        all_genomes = {g for c in components for g in c}
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        result = select_representatives(components, None, output_prefix)

        with open(result) as f:
            reps = [line.strip() for line in f if line.strip()]
        for rep in reps:
            assert rep in all_genomes

    def test_updates_clusters_csv_with_column(self, tmp_dir):
        """Clusters CSV should gain an is_representative column after running."""
        import pandas as pd
        components = [{'genome_A', 'genome_B'}, {'genome_C'}]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        select_representatives(components, None, output_prefix)

        df = pd.read_csv(tmp_dir / "test_clusters.csv")
        assert 'is_representative' in df.columns

    def test_representative_column_correct(self, tmp_dir):
        """Genomes in the output file should be True in is_representative, others False."""
        import pandas as pd
        components = [{'genome_A', 'genome_B', 'genome_C'}]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        result = select_representatives(components, None, output_prefix)

        with open(result) as f:
            reps = {line.strip() for line in f if line.strip()}

        df = pd.read_csv(tmp_dir / "test_clusters.csv")
        for _, row in df.iterrows():
            expected = row['genome_id'] in reps
            assert row['is_representative'] == expected

    def test_without_completeness_file(self, tmp_dir):
        """Should run without error when no completeness file is provided."""
        components = [{'genome_A', 'genome_B'}, {'genome_C'}]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        result = select_representatives(components, None, output_prefix)

        assert Path(result).exists()

    def test_with_completeness_file(self, tmp_dir):
        """Highest-completeness genome should be selected as representative."""
        components = [{'genome_A', 'genome_B', 'genome_C'}]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)
        completeness_file = str(tmp_dir / "completeness.txt")
        _make_completeness_file(
            completeness_file,
            {'genome_A': 0.70, 'genome_B': 0.99, 'genome_C': 0.80}
        )

        result = select_representatives(
            components, completeness_file, output_prefix
        )

        with open(result) as f:
            reps = [line.strip() for line in f if line.strip()]
        assert 'genome_B' in reps

    def test_multiple_components_one_rep_each(self, tmp_dir):
        """Each component should contribute at least one representative."""
        components = [
            {'genome_A', 'genome_B'},
            {'genome_C', 'genome_D'},
            {'genome_E'},
        ]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        result = select_representatives(components, None, output_prefix)

        with open(result) as f:
            reps = [line.strip() for line in f if line.strip()]
        assert len(reps) >= 3  # at least one per component

    def test_unknown_method_raises(self, tmp_dir):
        """Unknown method name should raise ValueError."""
        components = [{'genome_A', 'genome_B'}]
        output_prefix = str(tmp_dir / "test")
        _make_clusters_csv(tmp_dir / "test_clusters.csv", components)

        with pytest.raises(ValueError):
            select_representatives(components, None, output_prefix, method='invalid')


# ---------------------------------------------------------------------------
# Unimplemented stubs
# ---------------------------------------------------------------------------

class TestUnimplementedMethods:

    def test_gtdb_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            select_representatives_GTDB({'genome_A'}, {})

    def test_dereplicate_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            select_representatives_dereplicate({'genome_A'}, {}, threshold=0.99)
