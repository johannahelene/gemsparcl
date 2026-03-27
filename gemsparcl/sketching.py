#!/usr/bin/env python3
"""Sketching and distance calculation using sketchlib."""

import logging
import subprocess
import shutil
import os
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger('gemsparcl.sketching')


def check_sketchlib() -> str:
    """Find and validate sketchlib binary."""
    env_path = os.environ.get('SKETCHLIB_PATH')
    if env_path:
        if os.path.isfile(env_path) and os.access(env_path, os.X_OK):
            sketchlib_path = env_path
        else:
            raise FileNotFoundError(f"SKETCHLIB_PATH invalid: {env_path}")
    else:
        sketchlib_path = shutil.which('sketchlib')

    if sketchlib_path is None:
        raise FileNotFoundError(
            "sketchlib not found. Set SKETCHLIB_PATH:\n"
            "  export SKETCHLIB_PATH=/path/to/sketchlib"
        )

    result = subprocess.run([sketchlib_path, '--version'],
                          capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"sketchlib test failed: {result.stderr}")

    logger.info(f"Using sketchlib: {sketchlib_path}")
    return sketchlib_path


def run_sketching(input_file: str, output_prefix: str, sketch_size: int = 1000,
                 kmer_length: int = 31, threads: int = 4) -> Tuple[str, str]:
    """Run sketchlib to create genome sketches."""
    logger.info(f"Sketching with k={kmer_length}, s={sketch_size}")

    sketchlib_path = check_sketchlib()

    skm_file = f"{output_prefix}.skm"
    skd_file = f"{output_prefix}.skd"

    sketch_cmd = [
        sketchlib_path, 'sketch',
        '-f', input_file,
        '-o', output_prefix,
        '--k-vals', str(kmer_length),
        '-s', str(sketch_size),
        '--threads', str(threads)
    ]

    logger.info(f"Running: {' '.join(sketch_cmd)}")
    subprocess.run(sketch_cmd, check=True)

    if not Path(skm_file).exists() or not Path(skd_file).exists():
        raise FileNotFoundError("Sketch files not created")

    logger.info(f"Created: {skm_file}, {skd_file}")
    return skm_file, skd_file


def run_inverted_build(input_file: str, output_prefix: str, sketch_size: int = 10,
                      kmer_length: int = 31, threads: int = 4) -> Tuple[str, str]:
    """Build inverted index for large-scale search."""
    logger.info(f"Building inverted index with k={kmer_length}, s={sketch_size}")

    sketchlib_path = check_sketchlib()

    ski_file = f"{output_prefix}.ski"
    skq_file = f"{output_prefix}.skq"

    build_cmd = [
        sketchlib_path, 'inverted', 'build',
        '-f', input_file,
        '-o', output_prefix,
        '-k', str(kmer_length),
        '-s', str(sketch_size),
        '--write-skq',
        '--threads', str(threads)
    ]

    logger.info(f"Running: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True)

    if not Path(ski_file).exists() or not Path(skq_file).exists():
        raise FileNotFoundError("Index files not created")

    logger.info(f"Created: {ski_file}, {skq_file}")
    return ski_file, skq_file


def compute_distances_with_inverted(ski_file: str, skd_prefix: str, output_prefix: str,
                                   knn: int = 50, threads: int = 4,
                                   completeness_file: Optional[str] = None,
                                   completeness_cutoff: float = 0.64) -> str:
    """Compute distances using inverted index."""
    logger.info(f"Computing distances with inverted index (knn={knn})")

    sketchlib_path = check_sketchlib()

    distances_file = f"{output_prefix}.dists"

    precluster_cmd = [
        sketchlib_path, 'inverted', 'precluster',
        '--skd', skd_prefix,
        '--knn', str(knn),
        '--ani',
        '--retain-unmatched', 'singleton',
        '--threads', str(threads),
        '-o', distances_file,
        ski_file
    ]

    if completeness_file:
        precluster_cmd.extend([
            '--completeness-file', completeness_file,
            '--completeness-cutoff', str(completeness_cutoff)
        ])

    logger.info(f"Running: {' '.join(precluster_cmd)}")
    subprocess.run(precluster_cmd, check=True)

    if not Path(distances_file).exists():
        raise FileNotFoundError("Distance file not created")

    size_mb = Path(distances_file).stat().st_size / (1024 * 1024)
    logger.info(f"Created: {distances_file} ({size_mb:.1f} MB)")

    return distances_file


def compute_distances(skm_file: str, output_prefix: str, kmer_length: int = 31,
                     threads: int = 4, knn: int = 50,
                     completeness_file: Optional[str] = None,
                     completeness_cutoff: float = 0.64) -> str:
    """Compute pairwise ANI distances."""
    logger.info(f"Computing distances (knn={knn})")

    sketchlib_path = check_sketchlib()

    distances_file = f"{output_prefix}.dists"

    dist_cmd = [
        sketchlib_path, 'dist',
        skm_file,
        '-o', distances_file,
        '-k', str(kmer_length),
        '--threads', str(threads),
        '--knn', str(knn),
        '--ani'
    ]

    if completeness_file:
        dist_cmd.extend([
            '--completeness-file', completeness_file,
            '--completeness-cutoff', str(completeness_cutoff)
        ])

    logger.info(f"Running: {' '.join(dist_cmd)}")
    subprocess.run(dist_cmd, check=True)

    if not Path(distances_file).exists():
        raise FileNotFoundError("Distance file not created")

    size_mb = Path(distances_file).stat().st_size / (1024 * 1024)
    logger.info(f"Created: {distances_file} ({size_mb:.1f} MB)")

    return distances_file


def sketch_and_compute_distances(input_file: str, output_prefix: str,
                                sketch_size: int = 1000, kmer_length: int = 31,
                                threads: int = 4, knn: int = 50,
                                existing_sketch: Optional[str] = None,
                                completeness_file: Optional[str] = None,
                                completeness_cutoff: float = 0.64,
                                keep_intermediates: bool = False,
                                use_inverted_index: bool = False) -> str:
    """Main sketching pipeline."""
    logger.info("Starting sketching pipeline")

    ski_file = None
    skq_file = None

    if existing_sketch:
        logger.info(f"Using existing sketch: {existing_sketch}")
        skm_file = existing_sketch
        skd_file = existing_sketch.replace('.skm', '.skd')

        if not Path(skd_file).exists():
            raise FileNotFoundError(f".skd file not found: {skd_file}")

        keep_intermediates = True
        sketch_prefix = skm_file.replace('.skm', '')
    else:
        logger.info(f"Creating sketches from: {input_file}")

        if use_inverted_index:
            logger.info("Building inverted index with small sketch (s=10) for candidate finding")
            ski_file, skq_file = run_inverted_build(input_file, output_prefix, 10, kmer_length, threads)

        skm_file, skd_file = run_sketching(input_file, output_prefix, sketch_size, kmer_length, threads)
        sketch_prefix = output_prefix

    logger.info("Computing distances")

    if use_inverted_index:
        if ski_file is None:
            ski_file = f"{sketch_prefix}.ski"
            if not Path(ski_file).exists():
                raise FileNotFoundError(f"Index file not found: {ski_file}")

        distances_file = compute_distances_with_inverted(
            ski_file, sketch_prefix, output_prefix, knn, threads,
            completeness_file, completeness_cutoff
        )
    else:
        distances_file = compute_distances(
            skm_file, output_prefix, kmer_length, threads, knn,
            completeness_file, completeness_cutoff
        )

    if not keep_intermediates:
        logger.info("Cleaning up intermediate files")
        files_to_remove = [skm_file, skd_file]
        if ski_file:
            files_to_remove.extend([ski_file, skq_file])

        for file in files_to_remove:
            if file and Path(file).exists():
                try:
                    os.remove(file)
                except OSError as e:
                    logger.warning(f"Could not remove {file}: {e}")

    logger.info(f"Pipeline completed: {distances_file}")
    return distances_file
