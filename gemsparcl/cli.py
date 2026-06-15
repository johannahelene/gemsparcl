#!/usr/bin/env python3
"""
gemsparcl command-line interface

Ultra-fast genome clustering using advanced sketching and network clustering.
"""

import rich_click as click
import logging
import os
import sys
import traceback

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
            "options": ["--refine"],
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
@click.option('--use-inverted-index', is_flag=True,
              help='Use inverted index for fast search (recommended for >100k genomes)')
@click.option('--representatives', is_flag=True,
              help='Select one representative per cluster (highest completeness, or random)')


def cluster(input_file, output, threshold, sketch_size, kmer_length, threads, knn,
            existing_sketch, existing_distances, completeness_file, completeness_cutoff, refine,
            use_inverted_index, representatives):
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
    from .sketching import sketch_and_compute_distances, normalize_genome_ids
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
        # Normalize genome IDs (strip .fna/.fasta/.fa[.gz]) up front so sketch
        # names, distance IDs, and completeness lookups are consistent everywhere.
        if input_file:
            input_file = normalize_genome_ids(input_file, f"{output}_input.normalized.tsv")
        if completeness_file:
            completeness_file = normalize_genome_ids(completeness_file, f"{output}_completeness.normalized.tsv")

        # Step 1: Run sketching and distance calculation (skip if using existing distances)
        if existing_distances:
            logger.info("Step 1: Using existing distances file, skipping computation")
            distances_file = existing_distances
        else:
            logger.info("Step 1: Running sketchlib sketching and computing distances...")
            distances_file = sketch_and_compute_distances(
                input_file, output, sketch_size, kmer_length, threads, knn,
                existing_sketch, completeness_file, completeness_cutoff,
                use_inverted_index=use_inverted_index
            )
        
        # Step 2: Create network and find clusters
        logger.info("Step 2: Creating similarity network and finding clusters...")
        clusters_file, stats_file, graph, components = cluster_genomes(
            distances_file, output, threads, completeness_file, threshold
        )
        
        # Step 3: Optional refinement
        if refine:
            from .refinement import refine_network
            logger.info("Step 3: Refining clusters (removing contaminated genomes)...")

            # Apply refinement directly to the existing graph
            refined_graph, refined_components = refine_network(graph, components)
            
            # Save refined clusters
            refined_clusters_file = save_clusters_csv(refined_components, f"{output}_refined")
            save_cluster_stats(refined_components, f"{output}_refined")
            
            logger.info(f"Refined clusters saved: {refined_clusters_file}")
            
        # Step 4: Optional representative selection
        if representatives:
            from .representatives import select_representatives
            logger.info("Step 4: Selecting cluster representatives...")
            final_components = refined_components if refine else components
            reps_file = select_representatives(
                final_components, completeness_file, output, threads
            )
            logger.info(f"Representatives saved: {reps_file}")

        logger.info("Clustering completed successfully")
        logger.info(f"Results: {clusters_file}, {stats_file}")
        
    except Exception as e:
        logger.error(f"Error during clustering: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


click.rich_click.OPTION_GROUPS['gemsparcl query'] = [
    {
        "name": "Input / Output",
        "options": ["--output", "--existing-query-sketch"],
    },
    {
        "name": "Completeness correction (MAGs)",
        "options": ["--ref-completeness-file", "--query-completeness-file", "--completeness-cutoff"],
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
@click.option('--existing-query-sketch', type=click.Path(exists=True),
              help='Path to an existing query .skm file to skip re-sketching '
                   '(expects .skd in the same location). Compatibility with '
                   'the reference database is always validated.')
@click.option('--ref-completeness-file', type=click.Path(exists=True),
              help='Tab-separated completeness file for the reference database genomes (genome_id<tab>completeness)')
@click.option('--query-completeness-file', type=click.Path(exists=True),
              help='Tab-separated completeness file for the query genomes (genome_id<tab>completeness)')
@click.option('--completeness-cutoff', default=0.64, type=click.FloatRange(0.0, 1.0),
              show_default=True)
@click.option('--threads', default=4, type=click.IntRange(1), show_default=True,
              help='Number of threads')
def query(refdb, input_file, output, clusters_file, threshold, knn,
          existing_query_sketch, ref_completeness_file, query_completeness_file,
          completeness_cutoff, threads):
    """
    Query new genomes against an existing reference database.

    REFDB is the sketchlib database prefix (e.g. bactdb → bactdb.skm + bactdb.skd).
    INPUT_FILE is a tab-separated rfile (genome_id<tab>genome_path).

    Example:
        gemsparcl query bactdb new_genomes.rfile --clusters-file bactdb_clusters.csv -o query_out
    """
    from .sketching import (
        check_sketchlib, validate_input_file, normalize_genome_ids,
        read_sketch_params, sketch_query_genomes, compute_query_distances,
        validate_sketch_compatibility,
    )
    from .query import (
        load_cluster_assignments, assign_query_genomes,
        log_contamination_warnings, save_query_results,
    )

    logger.info(f"gemsparcl v{__version__} - Starting query")

    try:
        # Validate refdb
        skm_path = f"{refdb}.skm"
        if not os.path.exists(skm_path):
            raise FileNotFoundError(f"Reference sketch not found: {skm_path}")

        validate_input_file(input_file)

        # Normalize genome IDs (strip .fna/.fasta/.fa[.gz]) up front so they
        # match the reference database's (also normalized) genome IDs.
        input_file = normalize_genome_ids(input_file, f"{output}_input.normalized.tsv")
        if ref_completeness_file:
            ref_completeness_file = normalize_genome_ids(ref_completeness_file, f"{output}_ref_completeness.normalized.tsv")
        if query_completeness_file:
            query_completeness_file = normalize_genome_ids(query_completeness_file, f"{output}_query_completeness.normalized.tsv")

        # Step 1: Auto-detect sketch params from reference database
        logger.info("Step 1: Reading sketch parameters from reference database...")
        sketchlib_path = check_sketchlib()
        params = read_sketch_params(refdb, sketchlib_path)
        logger.info(f"  k={params['kmer_length']}, s={params['sketch_size']}")

        # Step 2: Sketch query genomes (or use existing sketch)
        if existing_query_sketch:
            query_prefix = existing_query_sketch.removesuffix('.skm').removesuffix('.skd')
            logger.info(f"Step 2: Using existing query sketch: {query_prefix}")
            skd_path = f"{query_prefix}.skd"
            if not os.path.exists(skd_path):
                raise FileNotFoundError(
                    f"Expected .skd file not found alongside existing sketch: {skd_path}"
                )
        else:
            logger.info("Step 2: Sketching query genomes...")
            query_prefix = f"{output}_query_sketches"
            sketch_query_genomes(
                input_file, query_prefix, sketchlib_path,
                params['sketch_size'], params['kmer_length'], threads,
            )

        # Always validate that ref and query sketches are compatible
        logger.info("Step 2b: Validating sketch compatibility...")
        validate_sketch_compatibility(refdb, query_prefix, sketchlib_path)

        # Step 3: Compute query-vs-reference distances
        logger.info("Step 3: Computing query distances...")
        distances_file = compute_query_distances(
            reference_skm=f"{refdb}.skm",
            query_skm=f"{query_prefix}.skm",
            output_prefix=output,
            sketchlib_path=sketchlib_path,
            kmer_length=params['kmer_length'],
            knn=knn,
            threads=threads,
            ref_completeness_file=ref_completeness_file,
            query_completeness_file=query_completeness_file,
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

        logger.info("Query completed successfully")

    except Exception as e:
        logger.error(f"Error during query: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


click.rich_click.OPTION_GROUPS['gemsparcl visualise'] = [
    {
        "name": "Input / Output",
        "options": ["--existing-distances", "--query-distances", "--clusters-file", "--metadata-file", "--output"],
    },
]


@main.command()
@click.option('--existing-distances', required=True, type=click.Path(exists=True),
              help='Path to existing .dists file')
@click.option('--query-distances', multiple=True, type=click.Path(exists=True),
              help='Optional: one or more query-vs-reference .dists files from '
                   '`gemsparcl query`, merged with --existing-distances so query '
                   'genomes appear in the network')
@click.option('--clusters-file', required=True, type=click.Path(exists=True),
              help='Clusters CSV from a gemsparcl cluster run (genome_id, cluster), '
                   'or a query_full.csv from `gemsparcl query` (genome_id, GCU, '
                   'is_query, note) — used for node annotations')
@click.option('--metadata-file', multiple=True, type=click.Path(exists=True),
              help='Optional, repeatable. CSV/TSV file(s) with a genome_id column '
                   'plus additional metadata columns (e.g. species, completeness) '
                   'to embed as node attributes')
@click.option('-t', '--threshold', default=0.98, type=click.FloatRange(0.0, 1.0),
              show_default=True, help='ANI threshold used to rebuild the network')
@click.option('-o', '--output', default='gemsparcl_vis', show_default=True,
              help='Output prefix for GraphML and annotation files')
@click.option('--threads', default=4, type=click.IntRange(1), show_default=True,
              help='Number of threads for distance processing')
def visualise(existing_distances, query_distances, clusters_file, metadata_file, threshold, output, threads):
    """Export the similarity network to Cytoscape-compatible GraphML files.

    Rebuilds the network from an existing distances file and exports it as GraphML,
    ready to open in Cytoscape. Large networks are split into multiple files.

    Example:
        gemsparcl visualise --existing-distances my_run.dists --clusters-file my_run_clusters.csv -o vis_out
    """
    from .clustering import build_graph_from_distances
    from .cytoscape import export_network_for_cytoscape
    import pandas as pd

    logger.info(f"gemsparcl v{__version__} - Starting visualisation")

    try:
        distance_files = [existing_distances, *query_distances]
        if query_distances:
            logger.info(f"Merging {len(query_distances)} query distance file(s) with reference distances")

        logger.info(f"Building network from {len(distance_files)} distance file(s) (threshold={threshold})...")
        graph, components = build_graph_from_distances(distance_files, threshold, threads)
        logger.info(f"Network: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges, "
                    f"{len(components)} components")

        cluster_df = pd.read_csv(clusters_file)
        column_map = {'cluster': 'cluster_id', 'GCU': 'cluster_id', 'is_query': 'is_query', 'note': 'note'}
        node_metadata: dict = {}
        for column, key in column_map.items():
            if column in cluster_df.columns:
                for genome_id, value in zip(cluster_df['genome_id'], cluster_df[column]):
                    node_metadata.setdefault(genome_id, {})[key] = value

        for metadata_path in metadata_file:
            logger.info(f"Merging metadata from {metadata_path}")
            meta_df = pd.read_csv(metadata_path, sep=None, engine='python')
            for column in meta_df.columns:
                if column == 'genome_id':
                    continue
                for genome_id, value in zip(meta_df['genome_id'], meta_df[column]):
                    node_metadata.setdefault(genome_id, {})[column] = value

        logger.info("Exporting to Cytoscape GraphML...")
        result = export_network_for_cytoscape(graph, components, output, node_metadata)
        logger.info(f"Created {len(result['graphml_files'])} GraphML file(s): "
                    + ', '.join(result['graphml_files']))

    except Exception as e:
        logger.error(f"Error during visualisation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main()
