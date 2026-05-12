# gemsparcl

**Fast genome clustering using sketching and network clustering**

gemsparcl clusters bacterial genomes at scale using the sketchlib algorithm for ANI estimation and network-based clustering. It handles incomplete MAGs through completeness correction and can detect contaminated genomes through network refinement.

## Installation

### 1. Install sketchlib

gemsparcl requires the [sketchlib](https://github.com/bacpop/sketchlib.rust) binary. Choose the method that suits your setup:

**conda (recommended):**
```bash
conda install -c bioconda sketchlib
```
No further configuration needed — sketchlib will be found automatically on your PATH.

**Pre-built binary (Linux):**

Download the latest binary from the [sketchlib releases page](https://github.com/bacpop/sketchlib.rust/releases), then:
```bash
chmod +x sketchlib
export SKETCHLIB_PATH=/path/to/sketchlib
```

**Build from source (Mac M1/M2/M3/M4 or custom optimisation):**

Requires the [Rust toolchain](https://rustup.rs):
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Standard install:
cargo install sketchlib

# Or optimised for your machine:
git clone https://github.com/bacpop/sketchlib.rust.git
cd sketchlib.rust
RUSTFLAGS="-C target-cpu=native" cargo install --path .

export SKETCHLIB_PATH=$(which sketchlib)
```

> **Mac users:** If you see a message saying the binary isn't signed by Apple, run:
> ```bash
> xattr -d "com.apple.quarantine" ./sketchlib
> ```

Add the `export SKETCHLIB_PATH=...` line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### 2. Install gemsparcl

Requires Python ≥3.8.

```bash
git clone https://github.com/johannahelene/gemsparcl.git
cd gemsparcl
pip install .
```

### 3. Verify

```bash
gemsparcl --version
```

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