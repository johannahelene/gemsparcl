Changelog
=========

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
