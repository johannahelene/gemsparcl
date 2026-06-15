#!/usr/bin/env python3
"""Sketching and distance calculation using sketchlib."""

import logging
import re
import subprocess
import shutil
import os
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger('gemsparcl.sketching')

# FASTA extensions (optionally gzipped) stripped from genome IDs so that
# e.g. "GCA_000001405.fna.gz" and "GCA_000001405" are treated as the same genome.
GENOME_ID_EXTENSION_RE = re.compile(r'\.(fna|fasta|fa)(?:\.gz)?$')


def normalize_genome_ids(input_path: str, output_path: str) -> str:
    """Strip known FASTA extensions from the genome_id column (column 1) of a
    tab-separated rfile or completeness file, writing a normalized copy.

    Comment (#) and blank lines are passed through unchanged.
    """
    with open(input_path) as fin, open(output_path, 'w') as fout:
        for line in fin:
            text = line.rstrip('\n')
            if not text or text.startswith('#'):
                fout.write(line)
                continue
            parts = text.split('\t')
            parts[0] = GENOME_ID_EXTENSION_RE.sub('', parts[0])
            fout.write('\t'.join(parts) + '\n')
    return output_path


def validate_input_file(file_path: str) -> None:
    """Validate the input rfile format (tab-separated: genome_id<tab>genome_path)."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Input file is empty: {file_path}")

    valid_lines = 0
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 2:
                raise ValueError(
                    f"Input file must have 2 tab-separated columns, "
                    f"got {len(parts)} in line: {line}"
                )
            valid_lines += 1

    if valid_lines == 0:
        raise ValueError(f"Input file is empty (no non-comment lines): {file_path}")


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


def read_sketch_params(ref_db_prefix: str, sketchlib_path: str) -> dict:
    """Parse k-mer length and sketch size from `sketchlib info {ref_db_prefix}.skm`.

    Raises ValueError if the database has more than one k value, since gemsparcl
    only supports single-k queries.
    """
    result = subprocess.run(
        [sketchlib_path, 'info', f"{ref_db_prefix}.skm"],
        capture_output=True, text=True, check=True
    )
    kmer_length = None
    sketch_size = None
    for line in result.stdout.splitlines():
        if line.startswith('kmers='):
            inner = line.split('=', 1)[1].strip('[]')
            vals = [int(x.strip()) for x in inner.split(',')]
            if len(vals) > 1:
                raise ValueError(
                    f"Reference database has multiple k values {vals}. "
                    "gemsparcl query only supports single-k databases. "
                    "Re-sketch with a single --k-vals value."
                )
            kmer_length = vals[0]
        elif line.startswith('sketch_size='):
            sketch_size = int(line.split('=', 1)[1])
    if kmer_length is None or sketch_size is None:
        raise ValueError(
            f"Could not parse k/s from sketchlib info output:\n{result.stdout}"
        )
    logger.info(f"Read from reference: k={kmer_length}, sketch_size={sketch_size}")
    return {'kmer_length': kmer_length, 'sketch_size': sketch_size}


def validate_sketch_compatibility(ref_db_prefix: str, query_db_prefix: str,
                                  sketchlib_path: str) -> None:
    """Raise ValueError if reference and query sketch databases are incompatible.

    Checks k-mer length and sketch size match exactly. Must be called before
    compute_query_distances to prevent silent wrong results.
    """
    ref_params = read_sketch_params(ref_db_prefix, sketchlib_path)
    query_params = read_sketch_params(query_db_prefix, sketchlib_path)

    errors = []
    if ref_params['kmer_length'] != query_params['kmer_length']:
        errors.append(
            f"k-mer length mismatch: reference k={ref_params['kmer_length']}, "
            f"query k={query_params['kmer_length']}"
        )
    if ref_params['sketch_size'] != query_params['sketch_size']:
        errors.append(
            f"sketch size mismatch: reference s={ref_params['sketch_size']}, "
            f"query s={query_params['sketch_size']}"
        )
    if errors:
        raise ValueError(
            "Reference and query sketch databases are incompatible:\n" +
            "\n".join(f"  - {e}" for e in errors) +
            "\nRe-sketch the query with the same parameters as the reference."
        )
    logger.info("Sketch compatibility check passed")


def run_sketching(input_file: str, output_prefix: str, sketchlib_path: str,
                 sketch_size: int = 1000, kmer_length: int = 31,
                 threads: int = 4) -> Tuple[str, str]:
    """Run sketchlib to create genome sketches."""
    logger.info(f"Sketching with k={kmer_length}, s={sketch_size}")

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


def run_inverted_build(input_file: str, output_prefix: str, sketchlib_path: str,
                      sketch_size: int = 10, kmer_length: int = 31,
                      threads: int = 4) -> Tuple[str, str]:
    """Build inverted index for large-scale search."""
    logger.info(f"Building inverted index with k={kmer_length}, s={sketch_size}")

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
                                   sketchlib_path: str, knn: int = 50, threads: int = 4,
                                   completeness_file: Optional[str] = None,
                                   completeness_cutoff: float = 0.64) -> str:
    """Compute distances using inverted index."""
    logger.info(f"Computing distances with inverted index (knn={knn})")

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


def compute_distances(skm_file: str, output_prefix: str, sketchlib_path: str,
                     kmer_length: int = 31, threads: int = 4, knn: int = 50,
                     completeness_file: Optional[str] = None,
                     completeness_cutoff: float = 0.64) -> str:
    """Compute pairwise ANI distances."""
    logger.info(f"Computing distances (knn={knn})")

    distances_file = f"{output_prefix}.dists"

    dist_cmd = [
        sketchlib_path, 'dist',
        skm_file.removesuffix('.skm'),
        '-o', distances_file,
        '-k', str(kmer_length),
        '--threads', str(threads),
        '--knn', str(knn),
        '--ani'
    ]

    if completeness_file:
        dist_cmd.extend([
            '--ref-completeness-file', completeness_file,
            '--completeness-cutoff', str(completeness_cutoff)
        ])

    logger.info(f"Running: {' '.join(dist_cmd)}")
    subprocess.run(dist_cmd, check=True)

    if not Path(distances_file).exists():
        raise FileNotFoundError("Distance file not created")

    size_mb = Path(distances_file).stat().st_size / (1024 * 1024)
    logger.info(f"Created: {distances_file} ({size_mb:.1f} MB)")

    return distances_file


def sketch_query_genomes(
    query_file: str,
    output_prefix: str,
    sketchlib_path: str,
    sketch_size: int,
    kmer_length: int,
    threads: int = 4,
) -> Tuple[str, str]:
    """Sketch query genomes using the same parameters as the reference database."""
    return run_sketching(
        query_file, output_prefix, sketchlib_path, sketch_size, kmer_length, threads
    )


def compute_query_distances(
    reference_skm: str,
    query_skm: str,
    output_prefix: str,
    sketchlib_path: str,
    kmer_length: int,
    knn: int,
    threads: int = 4,
    ref_completeness_file: Optional[str] = None,
    query_completeness_file: Optional[str] = None,
    completeness_cutoff: float = 0.64,
) -> str:
    """Compute distances between query genomes and the reference database.

    Uses sketchlib dist with query as second argument so only query-vs-reference
    distances are computed, not all-vs-all.
    """
    logger.info(f"Computing query distances (knn={knn})")

    distances_file = f"{output_prefix}.dists"

    ref_prefix = reference_skm.removesuffix('.skm')
    query_prefix = query_skm.removesuffix('.skm')

    dist_cmd = [
        sketchlib_path, 'dist',
        ref_prefix,
        query_prefix,
        '-o', distances_file,
        '-k', str(kmer_length),
        '--threads', str(threads),
        '--ani',
        '--knn', str(knn),
    ]

    if ref_completeness_file:
        dist_cmd.extend([
            '--ref-completeness-file', ref_completeness_file,
            '--completeness-cutoff', str(completeness_cutoff),
        ])
    if query_completeness_file:
        dist_cmd.extend([
            '--query-completeness-file', query_completeness_file,
        ])

    logger.info(f"Running: {' '.join(dist_cmd)}")
    subprocess.run(dist_cmd, check=True)

    if not Path(distances_file).exists():
        raise FileNotFoundError("Query distance file not created")

    size_mb = Path(distances_file).stat().st_size / (1024 * 1024)
    logger.info(f"Created: {distances_file} ({size_mb:.1f} MB)")

    return distances_file


def sketch_and_compute_distances(input_file: str, output_prefix: str,
                                sketch_size: int = 1000, kmer_length: int = 31,
                                threads: int = 4, knn: int = 50,
                                existing_sketch: Optional[str] = None,
                                completeness_file: Optional[str] = None,
                                completeness_cutoff: float = 0.64,
                                use_inverted_index: bool = False) -> str:
    """Main sketching pipeline."""
    logger.info("Starting sketching pipeline")

    sketchlib_path = check_sketchlib()

    ski_file = None
    skq_file = None

    if existing_sketch:
        logger.info(f"Using existing sketch: {existing_sketch}")
        skm_file = existing_sketch
        skd_file = existing_sketch.replace('.skm', '.skd')

        if not Path(skd_file).exists():
            raise FileNotFoundError(f".skd file not found: {skd_file}")

        sketch_prefix = skm_file.replace('.skm', '')
    else:
        logger.info(f"Creating sketches from: {input_file}")

        if use_inverted_index:
            logger.info("Building inverted index with small sketch (s=10) for candidate finding")
            ski_file, skq_file = run_inverted_build(input_file, output_prefix, sketchlib_path, 10, kmer_length, threads)

        skm_file, skd_file = run_sketching(input_file, output_prefix, sketchlib_path, sketch_size, kmer_length, threads)
        sketch_prefix = output_prefix

    logger.info("Computing distances")

    if use_inverted_index:
        if ski_file is None:
            ski_file = f"{sketch_prefix}.ski"
            if not Path(ski_file).exists():
                raise FileNotFoundError(f"Index file not found: {ski_file}")

        distances_file = compute_distances_with_inverted(
            ski_file, sketch_prefix, output_prefix, sketchlib_path, knn, threads,
            completeness_file, completeness_cutoff
        )
    else:
        distances_file = compute_distances(
            skm_file, output_prefix, sketchlib_path, kmer_length, threads, knn,
            completeness_file, completeness_cutoff
        )

    logger.info(f"Pipeline completed: {distances_file}")
    return distances_file
