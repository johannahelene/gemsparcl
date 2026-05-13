#!/usr/bin/env python3
"""
Picking component representatives for gemsparcl.

This module contains the algorithms to select from when picking representatives.
default (fast) = best completeness score when given otherwise random
GTDB = applies the GTDB rules if metadata is given (not implemented yet)
dereplicate = removes all genomes that are too similar based on threshold (not implemented yet)
"""

import heapq
import random
import logging
from functools import partial
import pandas as pd

logger = logging.getLogger(__name__)


def select_representatives(components, completeness_file, output_prefix,
                           threads, method='fast', threshold=0.99):
    """
    Select representatives from all components using specified method.
    Sequential processing to avoid memory issues with large datasets.
    """
    # Load completeness if provided
    completeness_dict = {}
    if completeness_file:
        logger.info(f"Loading completeness scores from {completeness_file}")
        with open(completeness_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    try:
                        completeness_dict[parts[0]] = float(parts[1])
                    except ValueError:
                        continue
        logger.info(f"Loaded {len(completeness_dict)} completeness scores")

    # Select method
    if method == 'fast':
        function = select_representatives_fast
    elif method == 'gtdb':
        function = select_representatives_GTDB
    elif method == 'dereplicate':
        function = partial(select_representatives_dereplicate, threshold=threshold)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Process sequentially 
    logger.info(f"Processing {len(components)} components sequentially")
    all_representatives = []
    for i, component in enumerate(components):
        reps = function(component, completeness_dict)
        all_representatives.append(reps)

        # Log progress for large datasets
        if (i + 1) % 5000 == 0:
            logger.info(f"Processed {i + 1}/{len(components)} components")

    logger.info(f"Completed processing all {len(components)} components")

    # Flatten list of lists and save results
    all_reps_flat = [rep for reps in all_representatives for rep in reps]
    logger.info(f"Selected {len(all_reps_flat)} total representatives")

    output_file = f"{output_prefix}_representatives.txt"
    with open(output_file, 'w') as f:
        for rep in all_reps_flat:
            f.write(f"{rep}\n")

    # Update clusters CSV with is_representative column
    logger.info("Updating clusters CSV with representative information")
    clusters_file = f"{output_prefix}_clusters.csv"
    df = pd.read_csv(clusters_file)

    # Create set of representatives for fast lookup
    reps_set = set(all_reps_flat)

    # Add is_representative column
    df['is_representative'] = df['genome_id'].isin(reps_set)

    # Save updated CSV
    df.to_csv(clusters_file, index=False)
    logger.info(f"Representatives saved to {output_file}")

    return output_file


def process_component(args, selector):
    """Process a single component with the given selector function."""
    component, completeness_dict = args
    return selector(component, completeness_dict)


def select_representatives_fast(component, completeness_dict):
    """
    Select n_reps genomes from component based on completeness if available,
    otherwise random selection.
    Memory-optimized version using iterator pattern.
    """
    n_reps = max(1, len(component) // 500)

    # Check if any genome in this component has completeness data
    has_completeness = any(g in completeness_dict for g in component)

    if has_completeness:
        # Use completeness for selection with iterator to avoid materializing dict
        representatives = heapq.nlargest(
            n_reps,
            ((genome, completeness_dict.get(genome, 0)) for genome in component),
            key=lambda x: x[1]
        )
        return [g for g, _ in representatives]
    else:
        # Random selection if no completeness data
        return random.sample(list(component), n_reps)


def select_representatives_GTDB(component, completeness_dict):  # ADD THIS STUB
    """
    Select rep genomes from component based on GTDB rules.
    """
    raise NotImplementedError("GTDB method not yet implemented")


def select_representatives_dereplicate(component, completeness_dict, threshold):  # ADD THIS STUB
    """
    Greedily select non-redundant representative genomes.
    
    For each genome, if distance to another exceeds threshold, keeps the
    first as representative and excludes the second. Ensures representatives
    are sufficiently distinct (distance >= threshold).
    """
    raise NotImplementedError("Dereplicate method not yet implemented")