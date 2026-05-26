The ``query`` command
=====================

``gemsparcl query`` assigns new genomes to an existing clustering without re-running the full pipeline.
It sketches the new genomes using the same parameters as the reference database, computes their distances against that database, and classifies each query genome based on where its nearest neighbours fall in the existing cluster assignments.

.. code-block:: bash

   gemsparcl query REFDB INPUT_FILE --clusters-file <clusters.csv> [options]

``REFDB`` is the sketchlib reference database prefix — for example, ``bactdb`` if your sketch files are ``bactdb.skm`` and ``bactdb.skd``.
``INPUT_FILE`` is a tab-separated rfile listing the new genomes to query.

.. code-block:: bash

   # Example
   gemsparcl query bactdb new_genomes.rfile --clusters-file bactdb_clusters.csv -o query_out


Prerequisites
-------------

Before running ``query`` you need:

1. The sketchlib reference database files (``<refdb>.skm`` and ``<refdb>.skd``) from the original clustering run — keep these by using ``--no-sketches`` **without** the ``--no-sketches`` flag, or simply not using ``--no-sketches`` at all.
2. The clusters CSV produced by that ``cluster`` run (e.g. ``bactdb_clusters.csv``).

Sketch parameters (k-mer length, sketch size) are read automatically from the reference database — you do not need to specify them.
Clustering parameters (threshold, knn) default to the same values as ``cluster`` (0.98 and 50), or can be set explicitly.

.. note::

   If ``gemsparcl cluster`` was run with ``--no-sketches``, the sketch files will have been deleted and querying is not possible. Re-run clustering without that flag to enable future queries.


How it works
------------

1. **Read sketch parameters** — calls ``sketchlib info`` on the reference database to extract k-mer length and sketch size automatically
2. **Sketch query genomes** — creates MinHash sketches for all new genomes using those same parameters
3. **Compute query distances** — estimates ANI between each query genome and its nearest neighbours in the reference database (not all-vs-all)
4. **Assign to clusters** — for each query genome, collects all reference hits above the ANI threshold and classifies it based on which clusters those hits belong to
5. **Write outputs** — produces per-query and combined result CSVs


Query classification
--------------------

Each query genome receives one of the following classifications in the ``note`` column:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Note
     - Meaning
   * - ``assigned``
     - All hits fall within a single non-singleton cluster. The query is assigned to that cluster.
   * - ``connecting_clusters — potential contamination``
     - Hits span two or more distinct non-singleton clusters. This is a signal of possible contamination or misassembly.
   * - ``connecting_cluster_and_singleton``
     - Hits include at least one non-singleton cluster and at least one singleton. Likely a genuine assignment with some noise.
   * - ``connecting_multiple_singletons``
     - Hits are spread across two or more singleton clusters. Unclear assignment; may be a novel genome.
   * - ``connecting_one_singleton``
     - Hits to exactly one singleton cluster. The query may belong to that singleton's lineage.
   * - ``no_hit``
     - No reference genome exceeds the ANI threshold. The query is novel with respect to the existing database.

The ``GCU`` column (Genome Cluster Unit) records the assigned cluster number. For contaminated queries it contains a comma-separated list of the connected cluster IDs; for ``no_hit`` it is empty.


Options
-------

.. option:: REFDB

   **Required positional argument.** Sketchlib reference database prefix. gemsparcl expects ``<REFDB>.skm`` and ``<REFDB>.skd`` to exist at this path.

.. option:: INPUT_FILE

   **Required positional argument.** Tab-separated rfile listing the new genomes:

   .. code-block:: text

      genome_id<TAB>/path/to/genome.fna

.. option:: --clusters-file PATH

   **Required.** Path to the clusters CSV produced by ``gemsparcl cluster`` for this reference database (e.g. ``bactdb_clusters.csv``).

.. option:: -o, --output STR

   Output prefix for result files. Default: ``gemsparcl_query``.

.. option:: -t, --threshold FLOAT

   ANI threshold for cluster assignment. Default: ``0.98``. Should match the threshold used during clustering.

.. option:: --knn INT

   Number of nearest neighbours to retain per query genome. Default: ``50``.

.. option:: --completeness-file PATH

   Optional completeness file for MAG datasets. If the reference clustering used completeness correction, provide a file covering **both** the existing reference genomes and the new query genomes:

   .. code-block:: text

      ref_genome1<TAB>0.95
      new_genome1<TAB>0.72

.. option:: --completeness-cutoff FLOAT

   Minimum completeness below which correction is applied. Default: ``0.64``.

.. option:: --no-sketches

   Delete query sketch files after the run to save disk space.

.. option:: --threads INT

   Number of threads to use for sketching. Default: ``4``.


Output files
------------

``query`` produces two output CSVs (see :doc:`outputs` for full details):

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Contents
   * - ``<prefix>_query_results.csv``
     - New query genomes only, with their cluster assignment and classification note.
   * - ``<prefix>_query_full.csv``
     - All genomes (existing reference + new queries), with an ``is_query`` flag.


Examples
--------

Basic query:

.. code-block:: bash

   gemsparcl query bactdb new_genomes.rfile \
     --clusters-file bactdb_clusters.csv \
     -o query_out

Query with a different threshold:

.. code-block:: bash

   gemsparcl query bactdb new_genomes.rfile \
     --clusters-file bactdb_clusters.csv \
     -t 0.95 \
     -o query_out

Query with completeness correction (MAG datasets):

.. code-block:: bash

   gemsparcl query bactdb new_genomes.rfile \
     --clusters-file bactdb_clusters.csv \
     --completeness-file combined_completeness.tsv \
     -o query_out

Query and delete sketch files afterwards:

.. code-block:: bash

   gemsparcl query bactdb new_genomes.rfile \
     --clusters-file bactdb_clusters.csv \
     -o query_out \
     --no-sketches
