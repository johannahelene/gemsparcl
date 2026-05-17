
<table border="0">
       <tr>
       <td valign="middle"><h1>gemsparcl 💎✨</h1><p><strong>Rapid and consistent clustering of millions of genomes highlights the diversity of prokaryotic life
</strong></p></td>
       <td valign="middle" align="right"><img src="docs/logo.png" alt="gemsparcl logo" width="250"/></td>
       </tr>
       </table>

<!-- **Fast genome clustering using sketching and network clustering** -->

gemsparcl clusters bacterial genomes at scale using the sketchlib algorithm for ANI estimation and network-based clustering. It handles incomplete MAGs through completeness correction and can detect contaminated genomes through network refinement.

## Installation

<details>
<summary><b>Click to expand installation instructions</b></summary>

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

</details>

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

1. Generate sketches and compute ANI distances using sketchlib, with optional completeness correction for incomplete MAGs
2. Build similarity network from pairwise distances above threshold
3. Find connected components as genome clusters
4. Optionally refine by removing contaminated genomes based on network topology

### Options

**Input/Output:**
- `-i, --input PATH`: Genome list file (tab-separated: genome_id\tgenome_path)
- `-o, --output STR`: Output prefix (default: gemsparcl_out)
- `--existing-sketch PATH`: Skip sketching, use existing `.skm` file (expects `.skd` in same location)
- `--existing-distances PATH`: Skip sketching and distance computation, use existing `.dists` file
- `--keep-intermediates`: Keep sketch and distance files after clustering

**Sketching:**
- `-s, --sketch-size INT`: Sketch size (default: 1000)
- `-k, --kmer-length INT`: K-mer length (default: 31)
- `--knn INT`: Number of nearest neighbors per genome (default: 50)
- `--threads INT`: Number of threads (default: 4)
- `--use-inverted-index`: Use inverted index for fast search (recommended for >100k genomes)

**Clustering:**
- `-t, --threshold FLOAT`: ANI threshold for clustering (default: 0.98)

**Completeness correction (for MAGs):**
- `--completeness-file PATH`: Genome completeness scores (tab-separated: genome_id\tcompleteness[0-1])
- `--completeness-cutoff FLOAT`: Minimum completeness for correction (default: 0.64)

**Refinement:**
- `--refine`: Enable network refinement to detect contaminated genomes
- `--betweenness-percentile FLOAT`: Betweenness centrality threshold (default: 80.0)
- `--clustering-percentile FLOAT`: Clustering coefficient threshold (default: 20.0)
- `--degree-percentile FLOAT`: Degree threshold (default: 20.0)

**Visualisation:**
- `--cytoscape`: Generate GraphML files for Cytoscape visualization

## Query

Assign new genomes to an existing clustering without re-running the full pipeline. Sketch files and the `_config.json` from the original `cluster` run must be available.

```bash
gemsparcl query -i new_genomes.rfile -c my_clusters_config.json -o query_out
```

Sketch parameters (k-mer length, sketch size) and clustering parameters (threshold, knn) are read automatically from the config. For MAG datasets, provide a combined completeness file covering both existing and new genomes:

```bash
gemsparcl query -i new_genomes.rfile -c my_clusters_config.json \
    --completeness-file combined_completeness.tsv -o query_out
```

**Output files:**

| File | Contents |
|---|---|
| `query_out_query_results.csv` | New genomes only: `query_id, GCU, note, top_hit_genome, top_hit_ani` |
| `query_out_query_full.csv` | All genomes (existing + new): `genome_id, GCU, is_query, note` |

**The `note` column:**

| Note | Meaning |
|---|---|
| `assigned` | All hits fall within one existing cluster |
| `connecting_clusters — potential contamination` | Hits span two or more distinct non-singleton clusters |
| `connecting_one_singleton` | Hit to exactly one singleton cluster |
| `connecting_multiple_singletons` | Hits to two or more singleton clusters |
| `connecting_cluster_and_singleton` | Hits to a real cluster and at least one singleton |
| `no_hit` | No hits above the ANI threshold |

**Options:**
- `-i / --input PATH`: rfile of new genomes (required)
- `-c / --config PATH`: `_config.json` from previous `gemsparcl cluster` run (required)
- `-o / --output STR`: output prefix (default: `gemsparcl_query`)
- `--completeness-file PATH`: combined completeness file for existing + new genomes
- `--no-sketches`: delete query sketch files after the run
- `--threads INT`: number of threads (default: 4)

> **Note:** If `gemsparcl cluster` was run with `--no-sketches`, querying is not possible. Re-run clustering without that flag to enable query.

## Citation

If you use gemsparcl in your research, please cite the sketchlib algorithm it depends on:

- BinDash: Zhao, X. BinDash, software for fast genome distance estimation. *Bioinformatics* **35**:671–673 (2019)
- sketchlib: https://github.com/bacpop/sketchlib.rust

## License

Apache 2.0 License