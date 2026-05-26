<table border="0">
  <tr>
    <td valign="middle">
      <h1>gemsparcl</h1>
      <p>Fast, scalable genome clustering using sketch-based ANI and network analysis.</p>
    </td>
    <td valign="middle" align="right">
      <img src="docs/logo.png" alt="gemsparcl logo" width="200"/>
    </td>
  </tr>
</table>

**Documentation:** https://johannahelene.github.io/gemsparcl/

## Installation

```bash
conda install -c bioconda sketchlib
pip install git+https://github.com/johannahelene/gemsparcl.git
```

See the [installation guide](https://johannahelene.github.io/gemsparcl/installation.html) for other sketchlib install methods (pre-built binary, build from source).

## Usage

```bash
# Cluster genomes
gemsparcl cluster -i genomes.txt -o my_run

# Query new genomes against an existing clustering
gemsparcl query my_run new_genomes.txt --clusters-file my_run_clusters.csv -o query_out
```

Full documentation at https://johannahelene.github.io/gemsparcl/

## Citation

If you use gemsparcl, please cite:

- Zhao, X. BinDash, software for fast genome distance estimation. *Bioinformatics* **35**:671–673 (2019)
- sketchlib: https://github.com/bacpop/sketchlib.rust

## License

Apache 2.0
