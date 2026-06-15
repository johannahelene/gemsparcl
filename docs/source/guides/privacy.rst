Genome Privacy & Local Analysis
================================

gemsparcl is designed to support privacy-preserving analysis. Your genome sequences never need to leave your machine.


The privacy problem
-------------------

Standard genome clustering requires computing pairwise distances between all genomes. For clinical isolates, proprietary strains, or data subject to access restrictions, sharing raw genome sequences with an external service may not be possible.

gemsparcl solves this by separating **sketching** from **querying**. The two steps can happen on different machines, and only sketches — not sequences — need to be exchanged.


How sketches protect your data
-------------------------------

A MinHash sketch is a compact mathematical representation of a genome's k-mer content. Sketches are **one-way**: it is not computationally feasible to reconstruct the original genome sequence from a sketch. Sharing a sketch reveals which genomic regions are present, but not the sequence itself.

This property is what makes local analysis possible: you sketch your genomes locally and query them against a reference database without ever sharing the underlying sequences.


Privacy-preserving workflows
-----------------------------

There are two ways to cluster or assign genomes without sharing sequences:

**Workflow 1 — Download reference sketches and query locally**

1. Download the pre-built reference sketch database from our FTP:

   .. code-block:: bash

      # FTP access — coming soon
      # ftp://[placeholder]/gemsparcl/reference/

2. Sketch your own genomes locally (sketchlib runs on your machine):

   .. code-block:: bash

      gemsparcl cluster -i my_genomes.txt -o my_sketch

   Or sketch directly with sketchlib if you only want sketches without clustering:

   .. code-block:: bash

      sketchlib sketch -l my_genomes.txt -o my_sketches -k 31 -s 1000

3. Query your local sketches against the reference database — everything runs locally:

   .. code-block:: bash

      gemsparcl query /path/to/reference_db my_genomes.txt \
        --clusters-file /path/to/reference_clusters.csv \
        -o my_query_results

At no point do your genome sequences leave your machine. The query command computes distances locally between your sketches and the reference sketches.

**Workflow 2 — Cluster entirely locally**

If you have your own reference collection, you can run the entire pipeline locally with no external data at all:

.. code-block:: bash

   # Step 1: cluster your reference genomes
   gemsparcl cluster -i reference_genomes.txt -o ref_db

   # Step 2: assign new genomes to the reference clustering
   gemsparcl query ref_db new_genomes.txt \
     --clusters-file ref_db_clusters.csv \
     -o query_out

   # Step 3: visualise the network
   gemsparcl visualise \
     --existing-distances ref_db.dists \
     --clusters-file ref_db_clusters.csv \
     -o vis_out

This is fully self-contained — no internet connection required after installing gemsparcl and sketchlib.


What the reference FTP provides
---------------------------------

.. note::

   The reference sketch database is coming soon. The FTP server and download instructions will be available at:

   ``ftp://[placeholder]/gemsparcl/reference/``

   The database will include pre-built sketches and cluster assignments for a large reference collection of prokaryotic genomes. Once available, you will be able to query your genomes against millions of reference genomes without sharing any sequences.

The FTP will provide:

- ``reference.skm`` / ``reference.skd`` — sketchlib sketch database
- ``reference_clusters.csv`` — cluster assignments for all reference genomes
- ``reference_cluster_stats.txt`` — summary statistics


Notes on data minimisation
---------------------------

- ``gemsparcl query`` outputs only cluster assignments and ANI scores — not the distances file itself, which you can delete after the run
- Sketches can be deleted after querying; they are only needed at query time
- The ``_query_results.csv`` output contains genome IDs and cluster assignments only — no sequence data
