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

Because ``visualise`` is separate from ``cluster``, you can experiment freely with different thresholds and outputs without touching your cluster assignments.


Prerequisites
-------------

You need:

1. A distances file (``*.dists``) — produced by ``gemsparcl cluster`` (keep it with ``--remove-intermediates`` absent, which is the default)
2. A clusters CSV (``*_clusters.csv`` or ``*_refined_clusters.csv``) — used to colour nodes by cluster in Cytoscape

Both files are produced by ``gemsparcl cluster``.


Options
-------

.. option:: --existing-distances PATH

   **Required.** Path to the ``.dists`` file containing pairwise ANI distances.

.. option:: --clusters-file PATH

   **Required.** Path to a clusters CSV (e.g. ``my_run_clusters.csv``). Used to annotate each node with its cluster ID in the GraphML output.

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
     - Cytoscape-compatible network file. Each node is a genome; edges connect genomes above the ANI threshold.
   * - ``<prefix>_annotations_part<N>.csv``
     - Node metadata: genome ID and cluster ID. Import into Cytoscape to colour nodes by cluster.

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


Opening in Cytoscape
--------------------

1. Open `Cytoscape <https://cytoscape.org>`_
2. **File → Import → Network from File** — select a ``_partN.graphml`` file
3. **File → Import → Table from File** — select the matching ``_annotations_partN.csv`` file, mapping the ``ID`` column to node names
4. Use the Style panel to colour nodes by ``cluster_id``
