#!/usr/bin/env python3
"""
Core clustering functionality for gemsparcl.

This module contains the main algorithms for processing distance data,
creating similarity networks, and identifying genome clusters.
"""

import logging
import time
import csv
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import networkx as nx
from functools import partial
from multiprocessing import Pool
import itertools

logger = logging.getLogger('gemsparcl.clustering')

def process_chunk(chunk: pd.DataFrame, edge_threshold: float, debug_enabled: bool = False) -> Tuple[Set[str], Dict[frozenset, float], Dict]:
    """Process a chunk of distance data and filter by threshold."""

    # Strip file extensions from genome IDs for cleaner output
    chunk['Query'] = chunk['Query'].str.replace(r'\.(fna|fasta|fa)(?:\.gz)?$', '', regex=True)
    chunk['Reference'] = chunk['Reference'].str.replace(r'\.(fna|fasta|fa)(?:\.gz)?$', '', regex=True)

    # Extract unique genomes from all rows (before filtering)
    unique_genomes_per_chunk = set(chunk['Query']).union(set(chunk['Reference']))
    
    # Get statistics before filtering
    total_edges = len(chunk)
    if debug_enabled:
        min_dist = chunk['Core'].min() if not chunk.empty else 0
        max_dist = chunk['Core'].max() if not chunk.empty else 0
    else:
        min_dist = None
        max_dist = None
    
    # Filter edges by threshold using vectorised operations
    # Keep edges where ANI >= threshold (e.g., keep similarities >= 98%)
    mask = chunk['Core'] >= edge_threshold
    filtered_chunk = chunk[mask]
    
    # Get statistics after filtering
    kept_edges = len(filtered_chunk)
    filtered_out = total_edges - kept_edges
    
    # Create distance dictionary with only the filtered edges
    # Use frozenset for genome pairs since edges are undirected
    distance_dict = {
        frozenset([query, ref]): ani
        for query, ref, ani in filtered_chunk[['Query', 'Reference', 'Core']].itertuples(index=False, name=None)
        
    }
    
    stats = {
        'total_edges': total_edges,
        'kept_edges': kept_edges,
        'filtered_out': filtered_out,
        'min_dist': min_dist,
        'max_dist': max_dist
    }
    
    return unique_genomes_per_chunk, distance_dict, stats


def create_graph(genome_ids: Set[str],
                distances: Dict[frozenset, float],
                edge_threshold: float) -> Tuple[nx.Graph, List[Set]]:
    """Create similarity network and identify connected components (clusters)."""
    logger.info("Creating similarity network from filtered distances")
    start_time = time.time()
    
    # Create undirected graph
    G = nx.Graph()
    
    # Add all genome nodes
    G.add_nodes_from(genome_ids)
    logger.info(f"Added {len(genome_ids)} nodes to graph")
    
    # Process edges in batches
    batch_size = 100000
    edge_batch = []

    for pair_set, ani in distances.items():
        pair_list = list(pair_set)
        if len(pair_list) != 2:
            logger.warning(f"Skipping invalid pair: {pair_set}")
            continue

        edge_batch.append((pair_list[0], pair_list[1], {'weight': ani}))

        if len(edge_batch) >= batch_size:
            G.add_edges_from(edge_batch)
            edge_batch = []

    if edge_batch:
        G.add_edges_from(edge_batch)
        
    # Find connected components (these are the genome clusters)
    logger.info("Finding connected components (genome clusters)")
    components = list(nx.connected_components(G))
    
    # Sort components by size (largest first) for output
    components.sort(key=len, reverse=True)
    
    elapsed_time = time.time() - start_time
    
    logger.info(f"Found {len(components)} genome clusters")
    if components:
        logger.info(f"Largest cluster: {len(components[0])} genomes")
    logger.info(f"Network creation took {elapsed_time:.2f} seconds")
    
    return G, components


def save_clusters_csv(components: List[Set], output_prefix: str) -> str:
    """Save cluster assignments to CSV file."""
    output_file = f"{output_prefix}_clusters.csv"
    logger.info(f"Saving cluster assignments to {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['genome_id', 'cluster'])
        
        # Assign cluster numbers (1-indexed, largest cluster = 1)
        for cluster_num, component in enumerate(components, 1):
            for genome_id in component:
                writer.writerow([genome_id, cluster_num])
    
    logger.info(f"Saved {len(components)} clusters containing {sum(len(c) for c in components)} genomes")
    return output_file


def save_cluster_stats(components: List[Set], output_prefix: str) -> str:
    """Save cluster statistics to text file."""
    output_file = f"{output_prefix}_cluster_stats.txt"
    
    cluster_sizes = [len(c) for c in components]
    total_genomes = sum(cluster_sizes)
    
    with open(output_file, 'w') as f:
        f.write(f"Total clusters: {len(components)}\n")
        f.write(f"Total genomes: {total_genomes}\n")
        f.write(f"Largest cluster: {max(cluster_sizes)} genomes\n")
        f.write(f"Singleton clusters: {sum(1 for size in cluster_sizes if size == 1)}\n")
    
    logger.info(f"Cluster statistics saved to {output_file}")
    return output_file

def cluster_genomes(distance_file: str, output_prefix: str, num_processes: int, completeness_file: Optional[str] = None,
                   threshold: float = 0.98, chunk_size: int = 100000) -> Tuple[str, str, nx.Graph, List[Set]]:
    """Cluster genomes from distance file using network analysis."""
    logger.info(f"Starting genome clustering with threshold {threshold}")
    start_time = time.time()
    
    # Initialize data structures
    all_unique_genomes = set()
    all_distances = {}
    
    # Debug stats (only calculated if debug logging is enabled)
    debug_enabled = logging.getLogger().isEnabledFor(logging.DEBUG)
    if debug_enabled:
        total_stats = {
            'total_edges_processed': 0,
            'total_edges_kept': 0,
            'total_edges_filtered': 0,
            'min_distance': float('inf'),
            'max_distance': 0
        }
    
    # Process distance file in chunks
    # sketchlib outputs: query_id, reference_id, ANI_distance
    chunk_iterator = pd.read_csv(distance_file, sep='\t', chunksize=chunk_size,
                                 names=['Query', 'Reference', 'Core'], header=None)
    batch_size = num_processes * 2
    
    with Pool(num_processes) as pool:
        process_func = partial(process_chunk, edge_threshold=threshold, debug_enabled=debug_enabled)
        
        while True:
            chunk_batch = list(itertools.islice(chunk_iterator, batch_size))
            if not chunk_batch:
                break
            
            results = pool.map(process_func, chunk_batch)
            
            # Merge results
            for chunk_genomes, chunk_distances, chunk_stats in results:
                all_unique_genomes.update(chunk_genomes)
                all_distances.update(chunk_distances)
                
                # Only update stats if debug is enabled
                if debug_enabled:
                    total_stats['total_edges_processed'] += chunk_stats['total_edges']
                    total_stats['total_edges_kept'] += chunk_stats['kept_edges']
                    total_stats['total_edges_filtered'] += chunk_stats['filtered_out']
                    if chunk_stats['min_dist'] is not None:
                        total_stats['min_distance'] = min(total_stats['min_distance'], chunk_stats['min_dist'])
                    if chunk_stats['max_dist'] is not None:
                        total_stats['max_distance'] = max(total_stats['max_distance'], chunk_stats['max_dist'])
    
    # Debug logging
    if debug_enabled:
        logging.debug(f"Total distances processed: {total_stats['total_edges_processed']:,}")
        logging.debug(f"Distances kept (≥{threshold}): {total_stats['total_edges_kept']:,}")
        logging.debug(f"Unique genomes: {len(all_unique_genomes):,}")
    
    # Create similarity network and find clusters
    graph, components = create_graph(all_unique_genomes, all_distances, threshold)
    
    # Save results
    clusters_file = save_clusters_csv(components, output_prefix)
    stats_file = save_cluster_stats(components, output_prefix)
    
    # Log final results
    total_time = time.time() - start_time
    logger.info(f"Clustering completed in {total_time:.2f} seconds")
    logger.info(f"Results saved: {clusters_file}, {stats_file}")

    # Return graph and components for optional refinement/visualization
    return clusters_file, stats_file, graph, components