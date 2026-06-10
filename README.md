<img src="docs/logo.png" alt="gemsparcl logo" width="200"/>

# gemsparcl

Fast, scalable genome clustering using sketch-based ANI and network analysis.

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

- von Wachsmann, J., Lorenz, L., Russell, M., Gurbich, T., Rodriguez-Bouza, V., Horsfield, S., Lees, J. A., & Finn, R. D. Rapid and Consistent Genome Clustering at the Scale of Millions of MAGs and Isolates. *bioRxiv* (2025). https://doi.org/10.64898/2025.12.30.695181

## License

Apache 2.0
