# gemsparcl

**Fast genome clustering using sketching and network clustering**

gemsparcl clusters bacterial genomes at scale using the sketchlib algorithm for ANI estimation and network-based clustering. It handles incomplete MAGs through completeness correction and can detect contaminated genomes through network refinement.

## Installation

```bash
# Clone and install
git clone https://github.com/yourusername/gemsparcl.git
cd gemsparcl
pip install -e .

# Set path to sketchlib binary
export SKETCHLIB_PATH=/path/to/sketchlib
```

Requires Python ≥3.8 and [sketchlib](https://github.com/bacpop/sketchlib.rust) binary.

## Usage

```bash
# Basic clustering
gemsparcl cluster -i genomes.txt -o output_prefix

# With completeness correction and refinement
gemsparcl cluster -i genomes.txt -o output_prefix \
    --completeness-file completeness.txt \
    --refine \
    --cytoscape
```

### Input Format

Tab-separated genome list:
```
genome1	/path/to/genome1.fna
genome2	/path/to/genome2.fna
```

Optional completeness file (for MAG correction):
```
genome1	0.95
genome2	0.87
```

### Output Files

- `{output}_clusters.csv`: Cluster assignments
- `{output}_cluster_stats.txt`: Cluster statistics
- `{output}_refined_clusters.csv`: Refined clusters (with `--refine`)
- `{output}_part*.graphml`: Network files for Cytoscape (with `--cytoscape`)

### Method

1. Generate sketches and compute ANI distances using sketchlib
2. Build similarity network from pairwise distances above threshold
3. Apply completeness correction for incomplete MAGs (if provided)
4. Find connected components as genome clusters
5. Optionally refine by removing contaminated genomes based on network topology

### Options

- `--threshold FLOAT`: ANI threshold for clustering (default: 0.98)
- `--sketch-size INT`: Sketch size (default: 1000)
- `--kmer-length INT`: K-mer length (default: 31)
- `--knn INT`: Number of nearest neighbors per genome (default: 50)
- `--completeness-file PATH`: Genome completeness file for MAG correction
- `--completeness-cutoff FLOAT`: Minimum completeness for correction (default: 0.64)
- `--refine`: Enable network refinement to detect contaminated genomes
- `--cytoscape`: Generate GraphML files for Cytoscape visualization
- `--use-inverted-index`: Use inverted index for >100k genomes
- `--keep-intermediates`: Keep sketch and distance files
- `--threads INT`: Number of threads (default: 4)

## Citation

If you use gemsparcl in your research, please cite the sketchlib algorithm it depends on:

- BinDash: Zhao, X. BinDash, software for fast genome distance estimation. *Bioinformatics* **35**:671–673 (2019)
- sketchlib: https://github.com/bacpop/sketchlib.rust

## License

Apache 2.0 License