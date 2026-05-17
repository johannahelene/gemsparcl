#!/usr/bin/env python3
"""
gemsparcl command-line interface

Ultra-fast genome clustering using advanced sketching and network clustering.
"""

import rich_click as click
import json
import logging
import os
import sys
import traceback
from typing import Optional

from . import __version__

click.rich_click.STYLE_OPTION = "bold medium_purple1"
click.rich_click.STYLE_SWITCH = "bold medium_purple1"
click.rich_click.STYLE_METAVAR = "plum3"
click.rich_click.STYLE_HELPTEXT = "white"
click.rich_click.STYLE_OPTION_GROUP_BORDER = "medium_purple3"
click.rich_click.STYLE_OPTION_HELP = "white"
click.rich_click.STYLE_HEADER_TEXT = "bold medium_purple1"
click.rich_click.STYLE_USAGE = "bold medium_purple1"
click.rich_click.STYLE_USAGE_COMMAND = "bold white"

click.rich_click.OPTION_GROUPS = {
    "gemsparcl cluster": [
        {
            "name": "Input / Output",
            "options": [
                "--input", "--output",
                "--existing-sketch", "--existing-distances",
                "--no-sketches", "--remove-intermediates",
            ],
        },
        {
            "name": "Representatives",
            "options": ["--representatives"],
        },
        {
            "name": "Sketching",
            "options": [
                "--sketch-size", "--kmer-length", "--knn",
                "--threads", "--use-inverted-index",
            ],
        },
        {
            "name": "Clustering",
            "options": ["--threshold"],
        },
        {
            "name": "Completeness correction (MAGs)",
            "options": ["--completeness-file", "--completeness-cutoff"],
        },
        {
            "name": "Refinement",
            "options": [
                "--refine",
                "--betweenness-percentile",
                "--clustering-percentile",
                "--degree-percentile",
            ],
        },
        {
            "name": "Visualisation",
            "options": ["--cytoscape"],
        },
    ]
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('gemsparcl')


def save_config(output: str, threshold: float, knn: int, sketch_size: int,
                kmer_length: int, sketch_prefix: Optional[str],
                clusters_file: str, completeness_file: Optional[str]) -> str:
    """Write _config.json after a successful cluster run."""
    config = {
        "threshold": threshold,
        "knn": knn,
        "sketch_size": sketch_size,
        "kmer_length": kmer_length,
        "sketch_prefix": os.path.abspath(sketch_prefix) if sketch_prefix else None,
        "clusters_file": os.path.abspath(clusters_file),
        "completeness_file": os.path.abspath(completeness_file) if completeness_file else None,
    }
    config_file = f"{output}_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    return config_file


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose):
    """
    gemsparcl: Ultra-fast genome dereplication
    
    Cluster bacterial genomes using sketching algorithms and network clustering.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@main.command()
@click.option('-i', '--input', 'input_file', type=click.Path(exists=True),
              help='Input file (tab-separated: genome_id<tab>genome_path). Required for sketching, optional with --existing-sketch or --existing-distances')
@click.option('-o', '--output', default='gemsparcl_out',
              help='Output prefix [default: gemsparcl_out]')
@click.option('-t', '--threshold', default=0.98, type=click.FloatRange(0.0, 1.0),
              help='ANI threshold for clustering [default: 0.98]')
@click.option('-s', '--sketch-size', default=1000, type=click.IntRange(1),
              help='Sketch size [default: 1000]')
@click.option('-k', '--kmer-length', default=31, type=click.IntRange(1),
              help='K-mer length [default: 31]')
@click.option('--threads', default=4, type=click.IntRange(1),
              help='Number of threads [default: 4]')
@click.option('--knn', default=50, type=click.IntRange(1),
              help='Number of nearest neighbors per genome [default: 50]')
@click.option('--existing-sketch', type=click.Path(exists=True),
              help='Optional: Path to existing .skm file to skip sketching (expects .skd in same location)')
@click.option('--existing-distances', type=click.Path(exists=True),
              help='Optional: Path to existing .dists file to skip sketching and distance computation')
@click.option('--completeness-file', type=click.Path(exists=True),
              help='Optional: File with genome completeness (tab-separated: genome_id<tab>completeness[0-1])')
@click.option('--completeness-cutoff', default=0.64, type=click.FloatRange(0.0, 1.0),
              help='Minimum completeness for correction [default: 0.64]')
@click.option('--refine', is_flag=True,
              help='Enable network refinement (detect contaminated genomes)')
@click.option('--betweenness-percentile', default=80.0, type=click.FloatRange(0.0, 100.0),
              help='Betweenness percentile threshold [default: 80.0]')
@click.option('--clustering-percentile', default=20.0, type=click.FloatRange(0.0, 100.0),
              help='Clustering coefficient percentile threshold [default: 20.0]')
@click.option('--degree-percentile', default=20.0, type=click.FloatRange(0.0, 100.0),
              help='Degree percentile threshold [default: 20.0]')
@click.option('--cytoscape', is_flag=True,
              help='Generate GraphML files for Cytoscape visualization')
@click.option('--no-sketches', is_flag=True,
              help='Delete sketch files after clustering (disables gemsparcl query on this dataset)')
@click.option('--remove-intermediates', is_flag=True,
              help='Remove intermediate distance files after clustering')
@click.option('--use-inverted-index', is_flag=True,
              help='Use inverted index for fast search (recommended for >100k genomes)')
@click.option('--representatives', is_flag=True,
              help='Select one representative per cluster (highest completeness, or random)')


def cluster(input_file, output, threshold, sketch_size, kmer_length, threads, knn,
            existing_sketch, existing_distances, completeness_file, completeness_cutoff, refine,
            betweenness_percentile, clustering_percentile, degree_percentile,
            cytoscape, no_sketches, remove_intermediates, use_inverted_index, representatives):
    """
    Cluster genomes based on ANI similarity.

    This is the main gemsparcl functionality that:
    1. Creates sketches using sketchlib algorithm
    2. Computes pairwise ANI distances
    3. Builds similarity network and finds clusters
    4. Optionally refines clusters and generates visualisations

    Example:
        gemsparcl cluster -i genomes.rfile -o my_clusters
    """
    # Lazy import heavy dependencies
    from .sketching import sketch_and_compute_distances
    from .clustering import cluster_genomes, save_clusters_csv, save_cluster_stats

    logger.info(f"gemsparcl v{__version__} - Starting clustering")

    # Validate input: need either input_file for sketching, existing_sketch, or existing_distances
    if not input_file and not existing_sketch and not existing_distances:
        logger.error("Error: Either --input (for sketching), --existing-sketch, or --existing-distances must be provided")
        sys.exit(1)

    if input_file and not existing_sketch and not existing_distances:
        logger.info(f"Input: {input_file}")

    logger.info(f"Output prefix: {output}")
    logger.info(f"ANI threshold: {threshold}")

    if existing_distances:
        logger.info(f"Using existing distances file: {existing_distances}")
        logger.info("Skipping sketching and distance computation - going straight to clustering")
    elif existing_sketch:
        logger.info(f"Using existing sketch: {existing_sketch}")
        if not input_file:
            logger.info("Skipping sketching step - using existing sketches only")
    else:
        logger.info(f"Sketch size: {sketch_size}, K-mer length: {kmer_length}")

    if not existing_distances:
        logger.info(f"knn: {knn}")

    if completeness_file:
        logger.info(f"Completeness correction enabled: {completeness_file}")
        logger.info(f"Completeness cutoff: {completeness_cutoff}")

    try:
        # Determine sketch_prefix for config (where the .skm/.skd files will live)
        if no_sketches:
            logger.warning(
                "Warning: sketch files will not be kept. "
                "You will not be able to run gemsparcl query against this dataset."
            )
            sketch_prefix = None
        elif existing_sketch:
            sketch_prefix = os.path.abspath(existing_sketch.replace('.skm', ''))
        elif existing_distances:
            sketch_prefix = None  # no sketch involved in this run
        else:
            sketch_prefix = os.path.abspath(output)

        # Step 1: Run sketching and distance calculation (skip if using existing distances)
        if existing_distances:
            logger.info("Step 1: Using existing distances file, skipping computation")
            distances_file = existing_distances
        else:
            logger.info("Step 1: Running sketchlib sketching and computing distances...")
            distances_file = sketch_and_compute_distances(
                input_file, output, sketch_size, kmer_length, threads, knn,
                existing_sketch, completeness_file, completeness_cutoff,
                keep_sketches=not no_sketches,
                use_inverted_index=use_inverted_index
            )
        
        # Step 2: Create network and find clusters
        logger.info("Step 2: Creating similarity network and finding clusters...")
        clusters_file, stats_file, graph, components = cluster_genomes(
            distances_file, output, threads, completeness_file, threshold
        )
        
        # Load cluster assignments for optional steps
        cluster_assignments = {}
        if refine or cytoscape:
            import pandas as pd
            cluster_df = pd.read_csv(clusters_file)
            cluster_assignments = dict(zip(cluster_df['genome_id'], cluster_df['cluster']))
        
        # Step 3: Optional refinement
        if refine:
            from .refinement import refine_network
            logger.info("Step 3: Refining clusters (removing contaminated genomes)...")

            # Apply refinement directly to the existing graph
            refined_graph, refined_components = refine_network(
                graph, components,
                betweenness_percentile=betweenness_percentile,
                clustering_percentile=clustering_percentile,
                degree_percentile=degree_percentile
            )
            
            # Save refined clusters
            refined_clusters_file = save_clusters_csv(refined_components, f"{output}_refined")
            save_cluster_stats(refined_components, f"{output}_refined")
            
            logger.info(f"Refined clusters saved: {refined_clusters_file}")
            
            # Update for cytoscape if needed
            if cytoscape:
                graph = refined_graph
                components = refined_components
                # Update cluster assignments
                cluster_df = pd.read_csv(refined_clusters_file)
                cluster_assignments = dict(zip(cluster_df['genome_id'], cluster_df['cluster']))
        
        # Step 4: Optional Cytoscape output
        if cytoscape:
            from .cytoscape import export_network_for_cytoscape
            logger.info("Step 4: Generating Cytoscape files...")

            # Export to Cytoscape using the graph we already have
            # (either the original from clustering or the refined version)
            cytoscape_files = export_network_for_cytoscape(
                graph, components, output, cluster_assignments
            )
            logger.info(f"Cytoscape files created: {len(cytoscape_files['graphml_files'])} networks")
        
        # Step 5: Optional representative selection
        if representatives:
            from .representatives import select_representatives
            logger.info("Step 5: Selecting cluster representatives...")
            final_components = refined_components if refine else components
            reps_file = select_representatives(
                final_components, completeness_file, output
            )
            logger.info(f"Representatives saved: {reps_file}")

        # Write config for future gemsparcl query runs
        config_file = save_config(
            output, threshold, knn, sketch_size, kmer_length,
            sketch_prefix, clusters_file, completeness_file
        )
        logger.info(f"Config saved: {config_file}")

        # Clean up distance file if requested
        if remove_intermediates:
            logger.info("Removing intermediate distance files...")
            try:
                os.remove(distances_file)
                logger.info(f"Removed: {distances_file}")
            except OSError as e:
                logger.warning(f"Could not remove {distances_file}: {e}")
        
        logger.info("Clustering completed successfully")
        logger.info(f"Results: {clusters_file}, {stats_file}")
        
    except Exception as e:
        logger.error(f"Error during clustering: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


click.rich_click.OPTION_GROUPS['gemsparcl query'] = [
    {
        "name": "Input / Output",
        "options": ["--input", "--config", "--output", "--no-sketches"],
    },
    {
        "name": "Completeness correction (MAGs)",
        "options": ["--completeness-file"],
    },
    {
        "name": "Performance",
        "options": ["--threads"],
    },
]


@main.command()
@click.argument('refdb')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', default='gemsparcl_query', show_default=True,
              help='Output prefix')
@click.option('--clusters-file', required=True, type=click.Path(exists=True),
              help='Clusters CSV from the reference gemsparcl cluster run '
                   '(e.g. bactdb_clusters.csv)')
@click.option('-t', '--threshold', default=0.98, type=click.FloatRange(0.0, 1.0),
              show_default=True, help='ANI threshold for cluster assignment')
@click.option('--knn', default=50, type=click.IntRange(1), show_default=True,
              help='Nearest neighbours per query genome')
@click.option('--completeness-file', type=click.Path(exists=True),
              help='Tab-separated completeness file (genome_id<tab>completeness)')
@click.option('--completeness-cutoff', default=0.64, type=click.FloatRange(0.0, 1.0),
              show_default=True)
@click.option('--no-sketches', is_flag=True,
              help='Delete query sketch files after the run')
@click.option('--threads', default=4, type=click.IntRange(1), show_default=True,
              help='Number of threads')
def query(refdb, input_file, output, clusters_file, threshold, knn,
          completeness_file, completeness_cutoff, no_sketches, threads):
    """
    Query new genomes against an existing reference database.

    REFDB is the sketchlib database prefix (e.g. bactdb → bactdb.skm + bactdb.skd).
    INPUT_FILE is a tab-separated rfile (genome_id<tab>genome_path).

    Example:
        gemsparcl query bactdb new_genomes.rfile --clusters-file bactdb_clusters.csv -o query_out
    """
    from .sketching import (
        check_sketchlib, validate_input_file,
        read_sketch_params, sketch_query_genomes, compute_query_distances,
    )
    from .query import (
        load_cluster_assignments, assign_query_genomes,
        log_contamination_warnings, save_query_results,
    )
    import glob

    logger.info(f"gemsparcl v{__version__} - Starting query")

    try:
        # Validate refdb
        skm_path = f"{refdb}.skm"
        if not os.path.exists(skm_path):
            raise FileNotFoundError(f"Reference sketch not found: {skm_path}")

        validate_input_file(input_file)

        # Step 1: Auto-detect sketch params from reference database
        logger.info("Step 1: Reading sketch parameters from reference database...")
        sketchlib_path = check_sketchlib()
        params = read_sketch_params(refdb, sketchlib_path)
        logger.info(f"  k={params['kmer_length']}, s={params['sketch_size']}")

        # Step 2: Sketch query genomes
        logger.info("Step 2: Sketching query genomes...")
        query_prefix = f"{output}_query_sketches"
        sketch_query_genomes(
            input_file, query_prefix, sketchlib_path,
            params['sketch_size'], params['kmer_length'], threads,
        )

        # Step 3: Compute query-vs-reference distances
        logger.info("Step 3: Computing query distances...")
        distances_file = compute_query_distances(
            query_skm=f"{query_prefix}.skm",
            reference_skm=f"{refdb}.skm",
            output_prefix=output,
            sketchlib_path=sketchlib_path,
            kmer_length=params['kmer_length'],
            knn=knn,
            threads=threads,
            completeness_file=completeness_file,
            completeness_cutoff=completeness_cutoff,
        )
        logger.info(f"  Distances written to {distances_file}")

        # Step 4: Assign query genomes to clusters
        logger.info("Step 4: Assigning query genomes to clusters...")
        cluster_assignments, singleton_clusters = load_cluster_assignments(clusters_file)
        logger.info(
            f"  Loaded {len(cluster_assignments):,} reference genomes, "
            f"{len(singleton_clusters):,} singleton clusters"
        )
        assignments = assign_query_genomes(
            distances_file, cluster_assignments, singleton_clusters, threshold
        )
        assigned = sum(1 for a in assignments if a['note'] == 'assigned')
        contaminated = sum(
            1 for a in assignments
            if a['note'] == 'connecting_clusters — potential contamination'
        )
        no_hit = sum(1 for a in assignments if a['note'] == 'no_hit')
        logger.info(
            f"  Assigned: {assigned}, potential contamination: {contaminated}, no hit: {no_hit}"
        )
        log_contamination_warnings(assignments)

        # Step 5: Save results
        logger.info("Step 5: Saving results...")
        results_file, full_file = save_query_results(assignments, clusters_file, output)
        logger.info(f"  Results: {results_file}, {full_file}")

        # Step 6: Clean up query sketch files if requested
        if no_sketches:
            for f in glob.glob(f"{query_prefix}.*"):
                try:
                    os.remove(f)
                except OSError as e:
                    logger.warning(f"Could not remove {f}: {e}")
            logger.info("Query sketch files removed")

        logger.info("Query completed successfully")

    except Exception as e:
        logger.error(f"Error during query: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main()
