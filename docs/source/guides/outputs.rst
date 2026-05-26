Output Files
============

gemsparcl writes its results to files whose names all share the output prefix you specify with ``-o``.
This page describes every output file and its format.

cluster command outputs
-----------------------

``<prefix>_clusters.csv``
^^^^^^^^^^^^^^^^^^^^^^^^^

The primary output. One row per genome with its cluster assignment.

.. code-block:: text

   genome_id,cluster
   GCA_000001405,1
   GCA_000002125,1
   GCA_000005845,2
   GCA_000003745,3

- **genome_id** — genome identifier from the rfile (file extensions stripped)
- **cluster** — integer cluster ID. Clusters are numbered starting from 1 in descending order of size (cluster 1 is the largest)

If ``--representatives`` is used, a third column is added:

.. code-block:: text

   genome_id,cluster,is_representative
   GCA_000001405,1,True
   GCA_000002125,1,False


``<prefix>_cluster_stats.txt``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A plain-text summary of the clustering:

.. code-block:: text

   Total clusters: 3
   Total genomes: 6
   Largest cluster: 3
   Singleton clusters: 1

- **Total clusters** — number of distinct connected components
- **Total genomes** — total number of genomes that were clustered
- **Largest cluster** — size of the largest component
- **Singleton clusters** — number of components that contain exactly one genome


``<prefix>_refined_clusters.csv``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Written only when ``--refine`` is used. Has the same format as ``_clusters.csv`` but reflects the cluster assignments **after** bridge nodes and edges have been removed.

Genomes that were identified as bridge nodes are moved to their own singleton clusters in this file.


``<prefix>_config.json``
^^^^^^^^^^^^^^^^^^^^^^^^^

A JSON file that records all parameters used during clustering, written for reproducibility and record-keeping.

.. code-block:: json

   {
     "threshold": 0.98,
     "knn": 50,
     "sketch_size": 1000,
     "kmer_length": 31,
     "sketch_prefix": "/path/to/my_run",
     "clusters_file": "/path/to/my_run_clusters.csv",
     "completeness_file": null
   }

.. note::

   The ``query`` command reads sketch parameters directly from the reference database and does not use this file.
   It is kept as a human-readable record of the run parameters.


``<prefix>_representatives.txt``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Written only when ``--representatives`` is used. One genome ID per line, listing all selected representatives:

.. code-block:: text

   GCA_000001405
   GCA_000005845


``<prefix>.log``
^^^^^^^^^^^^^^^^^

A detailed log of the run, including timings and any warnings. The verbosity can be increased with ``gemsparcl -v cluster ...``.


Cytoscape visualisation files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Written only when ``--cytoscape`` is used.

``<prefix>_part<N>.graphml``
   The similarity network in `GraphML <http://graphml.graphdrawing.org>`_ format. Each node is a genome; edges connect genomes above the ANI threshold. Open these files directly in `Cytoscape <https://cytoscape.org>`_.

   Large networks are split into multiple files (``_part1.graphml``, ``_part2.graphml``, …), each containing at most 30 000 nodes.

``<prefix>_annotations_part<N>.csv``
   Node metadata for the corresponding GraphML file:

   .. code-block:: text

      ID,cluster_id
      GCA_000001405,1
      GCA_000002125,1


query command outputs
---------------------

``<prefix>_query_results.csv``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Results for the **new query genomes only**.

.. code-block:: text

   query_id,GCU,note,top_hit_genome,top_hit_ani
   new_genome1,5,assigned,GCA_000001405,0.9923
   new_genome2,,no_hit,,
   new_genome3,1,connecting_clusters — potential contamination,GCA_000005845,0.9811

- **query_id** — genome ID of the query genome
- **GCU** — Genome Cluster Unit: the integer cluster ID the query is assigned to; empty if unassigned
- **note** — classification of the query (see :doc:`query` for all possible values)
- **top_hit_genome** — reference genome with the highest ANI to this query
- **top_hit_ani** — ANI value of that top hit


``<prefix>_query_full.csv``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Combined results covering **all genomes** (existing reference + new queries).

.. code-block:: text

   genome_id,GCU,is_query,note
   GCA_000001405,1,False,
   GCA_000002125,1,False,
   new_genome1,5,True,assigned
   new_genome2,,True,no_hit

- **genome_id** — genome identifier
- **GCU** — cluster assignment (integer or empty for ``no_hit``)
- **is_query** — ``True`` for new query genomes, ``False`` for existing reference genomes
- **note** — classification note (empty for reference genomes)

This file is useful for downstream analyses that need to see old and new genomes together in a single table.


Intermediate files (optional)
------------------------------

These are produced during the pipeline. Sketch files are kept by default (use ``--no-sketches`` to delete them). Distance files are also kept by default (use ``--remove-intermediates`` to delete them).

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Extension
     - Contents
   * - ``.skm``
     - Sketch matrix: binary sketchlib format containing all MinHash sketches
   * - ``.skd``
     - Sketch dictionary: maps genome IDs to sketch positions in the ``.skm`` file
   * - ``.ski``
     - Inverted index (only with ``--use-inverted-index``)
   * - ``.skq``
     - Query index (only with ``--use-inverted-index``)
   * - ``.dists``
     - Tab-separated pairwise distances: ``query_id<TAB>reference_id<TAB>ANI``
