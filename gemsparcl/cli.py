#!/usr/bin/env python3
"""
gemsparcl command-line interface

Ultra-fast genome clustering using advanced sketching and network clustering.
"""

import click
import logging
import os
import sys
import traceback

from . import __version__

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
@click.option('--betweenness-percentile', default=80.0, type=click.FloatRange(0.0, 100.0),
              help='Betweenness percentile threshold [default: 80.0]')
@click.option('--clustering-percentile', default=20.0, type=click.FloatRange(0.0, 100.0),
              help='Clustering coefficient percentile threshold [default: 20.0]')
@click.option('--degree-percentile', default=20.0, type=click.FloatRange(0.0, 100.0),
              help='Degree percentile threshold [default: 20.0]')
@click.option('--cytoscape', is_flag=True,
              help='Generate GraphML files for Cytoscape visualization')
@click.option('--keep-intermediates', is_flag=True,
              help='Keep sketch and distance files')
@click.option('--use-inverted-index', is_flag=True,
              help='Use inverted index for fast search (recommended for >100k genomes)')
# @click.option('--rep-method', type=click.Choice(['fast', 'gtdb', 'dereplicate'], case_sensitive=False), default='fast',
#               help='Representative selection method [default: fast]')
# @click.option('--rep-threshold', default=0.99, type=float,
#               help='Similarity threshold for dereplicate method [default: 0.99]')


def cluster(input_file, output, threshold, sketch_size, kmer_length, threads, knn,
            existing_sketch, existing_distances, completeness_file, completeness_cutoff, refine,
            betweenness_percentile, clustering_percentile, degree_percentile,
            cytoscape, keep_intermediates, use_inverted_index):
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
        # Step 1: Run sketching and distance calculation (skip if using existing distances)
        if existing_distances:
            logger.info("Step 1: Using existing distances file, skipping computation")
            distances_file = existing_distances
        else:
            logger.info("Step 1: Running sketchlib sketching and computing distances...")
            distances_file = sketch_and_compute_distances(
                input_file, output, sketch_size, kmer_length, threads, knn,
                existing_sketch, completeness_file, completeness_cutoff, keep_intermediates,
                use_inverted_index
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
        
        # # Step 5: Representative selection (always runs, uses final components)
        # from .representatives import select_all_representatives
        # logger.info(f"Selecting cluster representatives using method: {rep_method}")
        
        # reps_file = select_representatives(
        #     components=components,
        #     completeness_file=completeness_file,
        #     output_prefix=output,
        #     threads=threads,
        #     method=rep_method,
        #     threshold=rep_threshold  # only used if method='dereplicate'
        # )
        
        # logger.info(f"Representatives saved: {reps_file}")


        # Clean up distance file if not keeping intermediates
        if not keep_intermediates:
            logger.info("Cleaning up intermediate distance files...")
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


# @main.command()
# @click.option('-c', '--clusters', required=True, type=click.Path(exists=True),
#               help='Cluster file from cluster command')
# @click.option('-i', '--input', 'input_file', required=True, type=click.Path(exists=True),
#               help='Original genome file list')
# @click.option('-o', '--output', default='representatives.txt',
#               help='Output representatives list [default: representatives.txt]')
# @click.option('--method', default='largest', type=click.Choice(['largest', 'random']),
#               help='Selection method [default: largest]')
# def representatives(clusters, input_file, output, method):
#     """
#     Select representative genomes from clusters.
    
#     This command selects one representative genome per cluster based on
#     the specified method (e.g., largest genome, random selection).
    
#     Example:
#         gemsparcl representatives -c clusters.csv -i genomes.txt -o reps.txt
#     """
#     logger.info(f"gemsparcl v{__version__} - Selecting representatives")
#     logger.info(f"Clusters: {clusters}")
#     logger.info(f"Method: {method}")
    
#     try:
#         # TODO: Implement representative selection
#         logger.info("This feature is not yet implemented")
        
#     except Exception as e:
#         logger.error(f"Error selecting representatives: {e}")
#         sys.exit(1)


if __name__ == '__main__':
    main()
