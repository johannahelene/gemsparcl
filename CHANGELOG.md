# Changelog

## Unreleased

- `visualise` now accepts `--query-distances` (repeatable) to merge `gemsparcl query` distance files into the reference network, and `--clusters-file` also accepts a `query_full.csv` from `gemsparcl query` — node attributes (`cluster_id`, `is_query`, `note`) are embedded directly in the GraphML output as well as the annotation CSV.
- `visualise` now accepts `--metadata-file` (repeatable) — a CSV/TSV with a `genome_id` column plus any additional columns (e.g. `species`, `completeness`), merged into the embedded node attributes and annotation CSV.
- Removed `_config.json`. `cluster` no longer writes it, and `query` no longer reads it — sketch parameters are read directly from the reference database via `sketchlib info`.
- Genome IDs in the rfile, qfile, and completeness files are now normalized (FASTA extensions stripped) up front, so sketch names, distance IDs, and completeness lookups are consistent across `cluster` and `query`.
- Removed `--no-sketches` and `--remove-intermediates` from `cluster`, and `--no-sketches` from `query`. Sketch (`.skm`/`.skd`) and distance (`.dists`) files are now always kept; delete them yourself if you don't need them.
- Removed stale `--betweenness-percentile`, `--clustering-percentile`, and `--degree-percentile` entries from the `cluster --help` output — these were never implemented options. `--refine` takes no parameters.

## v1.0.0

- Initial release of the `gemsparcl` command-line tool.
- Genome clustering from sketchlib ANI distance output.
- Optional sketch generation and distance calculation through sketchlib.
- Support for existing `.skm` sketches or `.dists` distance files.
- Completeness-aware clustering for incomplete MAGs.
- Optional network refinement to isolate likely contaminated genomes.
- Optional Cytoscape GraphML export.
- Cluster assignment and summary statistics output.
