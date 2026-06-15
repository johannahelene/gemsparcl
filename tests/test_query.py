"""Tests for gemsparcl/query.py"""

import pytest
import pandas as pd

from gemsparcl.query import (
    load_cluster_assignments,
    assign_query_genomes,
    log_contamination_warnings,
    save_query_results,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _write_clusters(tmp_path, rows):
    """Write a clusters CSV and return its path."""
    path = tmp_path / "clusters.csv"
    df = pd.DataFrame(rows, columns=["genome_id", "cluster"])
    df.to_csv(path, index=False)
    return str(path)


def _write_distances(tmp_path, rows):
    """Write a distances file (no header, tab-sep: query_id, reference_id, ani)."""
    path = tmp_path / "distances.dists"
    with open(path, "w") as f:
        for q, r, ani in rows:
            f.write(f"{q}\t{r}\t{ani}\n")
    return str(path)


# ── TestLoadClusterAssignments ────────────────────────────────────────────────

class TestLoadClusterAssignments:
    def test_loads_assignments(self, tmp_path):
        clusters_file = _write_clusters(tmp_path, [
            ("genome_A", 1), ("genome_B", 1), ("genome_C", 2),
        ])
        assignments, _ = load_cluster_assignments(clusters_file)
        assert assignments["genome_A"] == "1"
        assert assignments["genome_B"] == "1"
        assert assignments["genome_C"] == "2"

    def test_identifies_singletons(self, tmp_path):
        clusters_file = _write_clusters(tmp_path, [
            ("genome_A", 1), ("genome_B", 1),  # cluster 1 — not singleton
            ("genome_C", 2),                    # cluster 2 — singleton
            ("genome_D", 3),                    # cluster 3 — singleton
        ])
        _, singletons = load_cluster_assignments(clusters_file)
        assert "2" in singletons
        assert "3" in singletons
        assert "1" not in singletons

    def test_empty_file_raises(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("genome_id,cluster\n")
        with pytest.raises(ValueError, match="empty"):
            load_cluster_assignments(str(path))


# ── TestAssignQueryGenomes ────────────────────────────────────────────────────

class TestAssignQueryGenomes:

    def _base_setup(self, tmp_path):
        cluster_assignments = {
            "ref_A": "1", "ref_B": "1",  # cluster 1
            "ref_C": "2",                 # cluster 2 (singleton)
            "ref_D": "3", "ref_E": "3",  # cluster 3
        }
        singleton_clusters = {"2"}
        return cluster_assignments, singleton_clusters

    def test_assigned_single_cluster(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_A", 0.99),
            ("query1", "ref_B", 0.985),
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "assigned"
        assert r["GCU"] == "1"

    def test_connecting_clusters_flagged(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_A", 0.99),   # cluster 1
            ("query1", "ref_D", 0.985),  # cluster 3
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "connecting_clusters — potential contamination"
        assert "1" in r["GCU"] and "3" in r["GCU"]

    def test_connecting_one_singleton(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_C", 0.99),  # cluster 2 (singleton)
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "connecting_one_singleton"

    def test_connecting_multiple_singletons(self, tmp_path):
        ca = {"ref_C": "2", "ref_X": "5"}
        sc = {"2", "5"}
        dists = _write_distances(tmp_path, [
            ("query1", "ref_C", 0.99),
            ("query1", "ref_X", 0.985),
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "connecting_multiple_singletons"

    def test_connecting_cluster_and_singleton(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_A", 0.99),  # cluster 1 (non-singleton)
            ("query1", "ref_C", 0.99),  # cluster 2 (singleton)
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "connecting_cluster_and_singleton"
        assert r["GCU"] == "1"

    def test_no_hit(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_A", 0.97),  # below threshold
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "no_hit"
        assert r["GCU"] == "unassigned"
        assert r["top_hit_genome"] is None

    def test_top_hit_is_highest_ani(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_A", 0.99),
            ("query1", "ref_B", 0.995),  # highest
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["top_hit_genome"] == "ref_B"
        assert r["top_hit_ani"] == pytest.approx(0.995)

    def test_threshold_respected(self, tmp_path):
        ca, sc = self._base_setup(tmp_path)
        dists = _write_distances(tmp_path, [
            ("query1", "ref_A", 0.979),  # just below threshold
        ])
        results = assign_query_genomes(dists, ca, sc, threshold=0.98)
        r = next(x for x in results if x["query_id"] == "query1")
        assert r["note"] == "no_hit"


# ── TestLogContaminationWarnings ──────────────────────────────────────────────

class TestLogContaminationWarnings:
    def test_logs_warning_for_contamination(self, caplog):
        import logging
        assignments = [
            {"query_id": "genome_X", "GCU": "1,3",
             "note": "connecting_clusters — potential contamination",
             "top_hit_genome": "ref_A", "top_hit_ani": 0.99},
        ]
        with caplog.at_level(logging.WARNING, logger="gemsparcl.query"):
            log_contamination_warnings(assignments)
        assert "genome_X" in caplog.text
        assert "potential contamination" in caplog.text.lower()

    def test_no_warning_for_assigned(self, caplog):
        import logging
        assignments = [
            {"query_id": "genome_Y", "GCU": "1", "note": "assigned",
             "top_hit_genome": "ref_A", "top_hit_ani": 0.99},
        ]
        with caplog.at_level(logging.WARNING, logger="gemsparcl.query"):
            log_contamination_warnings(assignments)
        assert "genome_Y" not in caplog.text


# ── TestSaveQueryResults ──────────────────────────────────────────────────────

class TestSaveQueryResults:

    def _assignments(self):
        return [
            {"query_id": "new_A", "GCU": "1", "note": "assigned",
             "top_hit_genome": "ref_A", "top_hit_ani": 0.99},
            {"query_id": "new_B", "GCU": "unassigned", "note": "no_hit",
             "top_hit_genome": None, "top_hit_ani": None},
        ]

    def test_query_results_file_created(self, tmp_path):
        clusters = _write_clusters(tmp_path, [("ref_A", 1), ("ref_B", 1)])
        save_query_results(self._assignments(), clusters, str(tmp_path / "out"))
        assert (tmp_path / "out_query_results.csv").exists()

    def test_query_full_file_created(self, tmp_path):
        clusters = _write_clusters(tmp_path, [("ref_A", 1), ("ref_B", 1)])
        save_query_results(self._assignments(), clusters, str(tmp_path / "out"))
        assert (tmp_path / "out_query_full.csv").exists()

    def test_query_results_columns(self, tmp_path):
        clusters = _write_clusters(tmp_path, [("ref_A", 1)])
        save_query_results(self._assignments(), clusters, str(tmp_path / "out"))
        df = pd.read_csv(tmp_path / "out_query_results.csv")
        assert set(df.columns) >= {"query_id", "GCU", "note", "top_hit_genome", "top_hit_ani"}

    def test_query_full_contains_all_genomes(self, tmp_path):
        clusters = _write_clusters(tmp_path, [("ref_A", 1), ("ref_B", 1)])
        save_query_results(self._assignments(), clusters, str(tmp_path / "out"))
        df = pd.read_csv(tmp_path / "out_query_full.csv")
        assert set(df["genome_id"]) == {"ref_A", "ref_B", "new_A", "new_B"}

    def test_is_query_column_correct(self, tmp_path):
        clusters = _write_clusters(tmp_path, [("ref_A", 1)])
        save_query_results(self._assignments(), clusters, str(tmp_path / "out"))
        df = pd.read_csv(tmp_path / "out_query_full.csv")
        assert not df.loc[df["genome_id"] == "ref_A", "is_query"].values[0]
        assert df.loc[df["genome_id"] == "new_A", "is_query"].values[0]
