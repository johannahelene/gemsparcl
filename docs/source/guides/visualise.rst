The ``visualise`` command
=========================

``gemsparcl visualise`` exports a similarity network to Cytoscape-compatible GraphML files.
It rebuilds the network from an existing distances file and does not require re-running sketching or clustering.

.. code-block:: bash

   gemsparcl visualise \
     --existing-distances my_run.dists \
     --clusters-file my_run_clusters.csv \
     -o vis_out


When to use it
--------------

- You want to visualise the network after clustering without re-running the full pipeline
- You want to try a different ANI threshold for the visualisation without re-clustering
- You want to visualise a subset or a specific clustering result (e.g. the refined clusters)
- You want to see where genomes from a ``gemsparcl query`` run land within the full reference network

Because ``visualise`` is separate from ``cluster``, you can experiment freely with different thresholds and outputs without touching your cluster assignments.


Prerequisites
-------------

You need:

1. A distances file (``*.dists``) — produced by ``gemsparcl cluster`` and always kept
2. A clusters CSV (``*_clusters.csv`` or ``*_refined_clusters.csv``) — used to annotate nodes with their cluster in Cytoscape

Both files are produced by ``gemsparcl cluster``.

To additionally show genomes from a ``gemsparcl query`` run alongside the reference (see `Including query genomes`_ below), you also need the query's ``*.dists`` and ``*_query_full.csv`` files, produced by ``gemsparcl query``.


Options
-------

.. option:: --existing-distances PATH

   **Required.** Path to the ``.dists`` file containing pairwise ANI distances.

.. option:: --query-distances PATH

   Optional, repeatable. One or more additional ``.dists`` files — typically the
   ``<prefix>.dists`` file written by ``gemsparcl query`` — merged with
   ``--existing-distances`` before building the network. Use this to bring query
   genomes into the same network as the reference genomes.

.. option:: --clusters-file PATH

   **Required.** Path to a clusters CSV (e.g. ``my_run_clusters.csv``), used to annotate each node in the GraphML output and the annotation CSV.

   Two formats are accepted:

   - A ``*_clusters.csv``/``*_refined_clusters.csv`` from ``gemsparcl cluster`` (columns ``genome_id,cluster``) — nodes are annotated with ``cluster_id``.
   - A ``*_query_full.csv`` from ``gemsparcl query`` (columns ``genome_id,GCU,is_query,note``) — nodes are annotated with ``cluster_id`` (from ``GCU``), ``is_query``, and ``note``.

.. option:: --metadata-file PATH

   Optional, repeatable. A CSV or TSV file with a ``genome_id`` column plus any
   number of additional metadata columns (e.g. ``species``, ``completeness``).
   Every other column is merged into the node attributes for matching genomes,
   in addition to anything from ``--clusters-file``. Pass it multiple times to
   merge metadata from several files (e.g. one for reference genomes and one
   for query genomes).

.. option:: -t, --threshold FLOAT

   ANI threshold used to draw edges in the network. Genome pairs with ANI ≥ this value are connected. Default: ``0.98``.

   This does not need to match the threshold used during clustering — you can visualise the same distances at a different threshold to explore the network structure.

.. option:: -o, --output STR

   Output prefix for all files. Default: ``gemsparcl_vis``.

.. option:: --threads INT

   Number of threads for reading and processing the distances file. Default: ``4``.


Output files
------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Contents
   * - ``<prefix>_part<N>.graphml``
     - Cytoscape-compatible network file. Each node is a genome; edges connect genomes above the ANI threshold. Node attributes from ``--clusters-file`` (``cluster_id``, and ``is_query``/``note`` if a ``query_full.csv`` was given) and any columns from ``--metadata-file`` (e.g. ``species``) are embedded directly in the file.
   * - ``<prefix>_annotations_part<N>.csv``
     - Node metadata with the same columns as the embedded node attributes. Import into Cytoscape to colour or shape nodes by ``cluster_id``, ``species``, and (for query results) ``is_query``.

Large networks are automatically split into multiple files (up to 30 000 nodes each) to keep Cytoscape responsive.


Examples
--------

Basic export:

.. code-block:: bash

   gemsparcl visualise \
     --existing-distances my_run.dists \
     --clusters-file my_run_clusters.csv \
     -o vis_out

Visualise the refined clustering at a lower threshold:

.. code-block:: bash

   gemsparcl visualise \
     --existing-distances my_run.dists \
     --clusters-file my_run_refined_clusters.csv \
     -t 0.95 \
     -o vis_out_95


Including query genomes
------------------------

After running ``gemsparcl query bactdb new_genomes.rfile --clusters-file bactdb_clusters.csv -o query_out`` (see :doc:`query`), merge the query distances into the reference network and use ``query_out_query_full.csv`` for annotations:

.. code-block:: bash

   gemsparcl visualise \
     --existing-distances bactdb.dists \
     --query-distances query_out.dists \
     --clusters-file query_out_query_full.csv \
     -o vis_with_query

The resulting GraphML contains every reference genome (and cluster) plus the query genomes, with each node annotated as ``is_query`` ``True``/``False`` and its assigned ``cluster_id``. See :ref:`step7-visualise-queries` for a worked example.

To also annotate nodes with species (or other metadata), add one ``--metadata-file`` per genome set — for example a reference metadata table and the query metadata table:

.. code-block:: bash

   gemsparcl visualise \
     --existing-distances bactdb.dists \
     --query-distances query_out.dists \
     --clusters-file query_out_query_full.csv \
     --metadata-file bactdb_metadata.tsv \
     --metadata-file query_metadata.tsv \
     -o vis_with_query


Opening in Cytoscape
--------------------

1. Open `Cytoscape <https://cytoscape.org>`_
2. **File → Import → Network from File** — select a ``_partN.graphml`` file
3. **File → Import → Table from File** — select the matching ``_annotations_partN.csv`` file, mapping the ``ID`` column to node names (this is optional — the same columns are already embedded as node attributes in the GraphML)
4. Use the Style panel to colour nodes by ``cluster_id`` or ``species`` (if ``--metadata-file`` was used), and (for query results) map ``is_query`` to a shape or border colour to highlight the new genomes
