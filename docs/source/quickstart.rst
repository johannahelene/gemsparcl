Quick Start
===========

This guide walks you through a complete clustering run from scratch. You should have gemsparcl and sketchlib installed (see :doc:`installation`).

Prepare your genome list
-------------------------

gemsparcl reads a tab-separated genome input file listing genome identifiers and their file paths. Create one like this:

.. code-block:: bash

   # genomes.txt
   GCA_000001405  /data/genomes/GCA_000001405.fna
   GCA_000002125  /data/genomes/GCA_000002125.fna
   GCA_000005845  /data/genomes/GCA_000005845.fna

Each line must have exactly two tab-separated fields: a genome ID and the path to its FASTA file.
Lines beginning with ``#`` are ignored.

If you have a directory of genome assemblies, you can generate this file automatically:

.. code-block:: bash

   find /data/genomes/ -name "*.fna" | sort | \
       awk -F'/' '{id=$NF; sub(/\.fna$/, "", id); print id"\t"$0}' \
       > genomes.txt

Adjust the ``-name`` pattern (and the ``sub()`` suffix) to match your file extension, e.g. ``*.fa.gz`` or ``*.fasta``.

.. note::

   File extensions (``.fna``, ``.fasta``, ``.fa``, ``.gz``) are stripped from genome IDs in the output
   so that ``GCA_000001405.fna.gz`` and ``GCA_000001405`` are treated as the same genome.


Cluster your genomes
--------------------

Run the ``cluster`` command:

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o my_run

This will:

1. Sketch all genomes with sketchlib (k = 31, sketch size = 1000 by default)
2. Compute all-vs-all ANI distances (keeping the ``--knn`` = 50 nearest neighbours per genome)
3. Build a similarity network — genomes with ANI ≥ 0.98 are connected
4. Find connected components — each component is a cluster
5. Write cluster assignments to ``my_run_clusters.csv``

Sketch files (``.skm``/``.skd``) and the distance file (``.dists``) are always kept alongside the cluster outputs — the sketch files are needed for ``query``. Delete them yourself afterwards if you don't need them.


Check the results
-----------------

.. code-block:: bash

   # Quick summary
   cat my_run_cluster_stats.txt

   # First few assignments
   head my_run_clusters.csv

The clusters CSV has two columns:

.. code-block:: text

   genome_id,cluster
   GCA_000001405,1
   GCA_000002125,1
   GCA_000005845,2


Common options
--------------

**Use a different ANI threshold** (default: 0.98 = 98% ANI):

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o my_run -t 0.95

**Speed up large datasets** with the inverted index (recommended for > 100k genomes):

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o my_run --use-inverted-index --threads 16

**Re-use existing sketch files** (skips sketching, saves time):

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o my_run --existing-sketch my_run.skm

**Re-use existing distances** (skips both sketching and distance computation):

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o my_run --existing-distances my_run.dists

**Refine Network** (Contaminated genomes might connect distinct GCUs)

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o my_run --refine

**Visualise the network in Cytoscape** (run after clustering, any time):

.. code-block:: bash

   gemsparcl visualise \
     --existing-distances my_run.dists \
     --clusters-file my_run_clusters.csv \
     -o vis_out


Query new genomes
-----------------

After clustering, you can assign new genomes to the existing clusters without re-running the full pipeline.
You need the sketch files from the original run and the clusters CSV.

Pass the reference database prefix and the clusters CSV directly to ``query``:

.. code-block:: bash

   gemsparcl query my_run new_genomes.txt \
     --clusters-file my_run_clusters.csv \
     -o query_out

Sketch parameters (k-mer length, sketch size) are read automatically from the reference database — you do not need to specify them again.

Results are written to ``query_out_query_results.csv`` and ``query_out_query_full.csv``.

See :doc:`guides/query` for full details on the query output and classification logic.


Next steps
----------

- :doc:`guides/cluster` — all options for the ``cluster`` command explained in detail
- :doc:`guides/query` — full guide to querying existing clusterings
- :doc:`guides/visualise` — exporting networks to Cytoscape
- :doc:`guides/privacy` — querying locally without sharing sequences
- :doc:`guides/outputs` — what every output file contains
- :doc:`background/how_it_works` — the algorithms behind the clustering
- :doc:`guides/mags` — using completeness correction for MAG datasets
