#!/usr/bin/env python3
"""Query new genomes against an existing gemsparcl clustering."""

import json
import logging
import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import pandas as pd

logger = logging.getLogger('gemsparcl.query')

REQUIRED_CONFIG_KEYS = {'threshold', 'knn', 'sketch_size', 'kmer_length', 'clusters_file'}


def load_config(config_file: str) -> dict:
    """Load and validate _config.json from a previous cluster run."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file) as f:
        config = json.load(f)

    missing = REQUIRED_CONFIG_KEYS - set(config.keys())
    if missing:
        raise ValueError(f"Config missing required keys: {', '.join(sorted(missing))}")

    if not os.path.exists(config['clusters_file']):
        raise FileNotFoundError(
            f"Clusters file from config not found: {config['clusters_file']}"
        )

    if not config.get('sketch_prefix'):
        raise ValueError(
            "Config has no sketch_prefix — sketch files were not kept during clustering.\n"
            "Run gemsparcl cluster again without --no-sketches to enable querying."
        )

    skm = config['sketch_prefix'] + '.skm'
    if not os.path.exists(skm):
        raise FileNotFoundError(
            f"Sketch file not found: {skm}\n"
            "Was --no-sketches used during clustering? gemsparcl query requires sketch files."
        )

    return config


def load_cluster_assignments(clusters_file: str) -> Tuple[Dict[str, str], Set[str]]:
    """Load cluster assignments and identify singleton clusters.

    Returns (cluster_assignments, singleton_cluster_ids).
    """
    df = pd.read_csv(clusters_file)

    if df.empty:
        raise ValueError(f"Clusters file is empty: {clusters_file}")

    cluster_assignments = dict(
        zip(df['genome_id'].astype(str), df['cluster'].astype(str))
    )

    cluster_sizes = df.groupby('cluster').size()
    singleton_clusters = set(cluster_sizes[cluster_sizes == 1].index.astype(str))

    return cluster_assignments, singleton_clusters


def assign_query_genomes(
    distances_file: str,
    cluster_assignments: Dict[str, str],
    singleton_clusters: Set[str],
    threshold: float,
) -> List[dict]:
    """Assign query genomes to existing clusters based on ANI distances.

    Reads the distances file in chunks and classifies each query genome
    according to which existing clusters it connects to.
    """
    # Single pass: collect all query IDs and hits above threshold
    hits: Dict[str, List[Tuple[float, str, str]]] = defaultdict(list)
    all_query_ids: Set[str] = set()

    for chunk in pd.read_csv(
        distances_file, sep='\t', header=None,
        names=['reference_id', 'query_id', 'ani'],
        chunksize=100_000,
        dtype={'reference_id': str, 'query_id': str, 'ani': float},
    ):
        all_query_ids.update(chunk['query_id'].unique())

        above = chunk[chunk['ani'] >= threshold]
        above = above[above['reference_id'].isin(cluster_assignments)]

        for row in above.itertuples(index=False):
            cluster_id = cluster_assignments[row.reference_id]
            hits[row.query_id].append((row.ani, row.reference_id, cluster_id))

    assignments = []
    for qid in sorted(all_query_ids):
        query_hits = hits.get(qid, [])

        if not query_hits:
            assignments.append({
                'query_id': qid,
                'GCU': 'unassigned',
                'note': 'no_hit',
                'top_hit_genome': None,
                'top_hit_ani': None,
            })
            continue

        top_ani, top_genome, _ = max(query_hits, key=lambda x: x[0])
        hit_clusters = {cluster_id for _, _, cluster_id in query_hits}
        non_singletons = hit_clusters - singleton_clusters
        singletons_hit = hit_clusters & singleton_clusters

        if len(non_singletons) > 1:
            note = 'connecting_clusters — potential contamination'
            gcu = ','.join(sorted(non_singletons))
        elif len(non_singletons) == 1 and singletons_hit:
            note = 'connecting_cluster_and_singleton'
            gcu = next(iter(non_singletons))
        elif len(non_singletons) == 1:
            note = 'assigned'
            gcu = next(iter(non_singletons))
        elif len(singletons_hit) > 1:
            note = 'connecting_multiple_singletons'
            gcu = ','.join(sorted(singletons_hit))
        else:
            note = 'connecting_one_singleton'
            gcu = next(iter(singletons_hit))

        assignments.append({
            'query_id': qid,
            'GCU': gcu,
            'note': note,
            'top_hit_genome': top_genome,
            'top_hit_ani': top_ani,
        })

    return assignments


def log_contamination_warnings(assignments: List[dict]) -> None:
    """Log a warning for every query genome flagged as potential contamination."""
    for a in assignments:
        if a['note'] == 'connecting_clusters — potential contamination':
            logger.warning(
                f"Potential contamination: {a['query_id']} connects clusters {a['GCU']}"
            )


def save_query_results(
    assignments: List[dict],
    existing_clusters_file: str,
    output_prefix: str,
) -> Tuple[str, str]:
    """Write query results to two output files.

    Returns (results_file, full_file).
    """
    query_df = pd.DataFrame(assignments)

    results_file = f"{output_prefix}_query_results.csv"
    query_df.to_csv(results_file, index=False)
    logger.info(f"Query results saved: {results_file}")

    existing_df = pd.read_csv(existing_clusters_file)
    existing_df = existing_df.rename(columns={'cluster': 'GCU'})
    existing_df['GCU'] = existing_df['GCU'].astype(str)
    existing_df['is_query'] = False
    existing_df['note'] = 'existing'

    query_full = query_df[['query_id', 'GCU', 'note']].rename(
        columns={'query_id': 'genome_id'}
    ).copy()
    query_full['is_query'] = True

    full_df = pd.concat(
        [existing_df[['genome_id', 'GCU', 'is_query', 'note']],
         query_full[['genome_id', 'GCU', 'is_query', 'note']]],
        ignore_index=True,
    )

    full_file = f"{output_prefix}_query_full.csv"
    full_df.to_csv(full_file, index=False)
    logger.info(f"Full results saved: {full_file}")

    return results_file, full_file
