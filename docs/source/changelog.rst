Changelog
=========

Unreleased
----------

- ``visualise`` now accepts ``--query-distances`` (repeatable) to merge ``gemsparcl query`` distance files into the reference network, and ``--clusters-file`` also accepts a ``query_full.csv`` from ``gemsparcl query`` — node attributes (``cluster_id``, ``is_query``, ``note``) are embedded directly in the GraphML output as well as the annotation CSV.
- ``visualise`` now accepts ``--metadata-file`` (repeatable) — a CSV/TSV with a ``genome_id`` column plus any additional columns (e.g. ``species``, ``completeness``), merged into the embedded node attributes and annotation CSV.
- Removed ``_config.json``. ``cluster`` no longer writes it, and ``query`` no longer reads it — sketch parameters are read directly from the reference database via ``sketchlib info``.
- Genome IDs in the rfile, qfile, and completeness files are now normalized (FASTA extensions stripped) up front, so sketch names, distance IDs, and completeness lookups are consistent across ``cluster`` and ``query``.

v1.0.0
------

Initial release.

- ``gemsparcl cluster`` command for end-to-end genome clustering
- Genome sketching and ANI distance computation via sketchlib integration
- Support for resuming from existing sketch files (``--existing-sketch``) or distance files (``--existing-distances``)
- Completeness-aware clustering for incomplete MAGs (``--completeness-file``)
- Network refinement to isolate contaminated genomes (``--refine``)
- Cytoscape GraphML export for network visualisation (``--cytoscape``)
- Representative genome selection per cluster (``--representatives``)
- Inverted index support for large datasets > 100 k genomes (``--use-inverted-index``)
- ``gemsparcl query`` command for incremental assignment of new genomes to an existing clustering
- Config file (``_config.json``) for reproducible query runs
