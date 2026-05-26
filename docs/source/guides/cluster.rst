The ``cluster`` command
=======================

``gemsparcl cluster`` runs the full genome clustering pipeline: sketching, distance computation, network construction, and cluster assignment.

.. code-block:: bash

   gemsparcl cluster -i <genome_list> -o <output_prefix> [options]

Pipeline steps
--------------

The command always runs these steps in order, though individual steps can be skipped by supplying pre-computed files:

1. **Validate input** — check that the rfile is correctly formatted
2. **Sketch genomes** — call sketchlib to create MinHash sketches for every genome
3. **Compute distances** — call sketchlib to estimate pairwise ANI from the sketches
4. **Build network** — connect genomes whose ANI exceeds the threshold
5. **Find clusters** — extract connected components from the network
6. **Refine** *(optional)* — remove bridge nodes and edges that indicate contamination
7. **Select representatives** *(optional)* — choose one or more representative genomes per cluster
8. **Save config** — write ``_config.json`` for future ``query`` runs

To visualise the network in Cytoscape, use :doc:`visualise` after clustering.

A log file is written to ``<output_prefix>.log``.


Input / Output options
----------------------

.. option:: -i, --input PATH

   **Required.** Tab-separated genome list (rfile). Each line must have exactly two fields:

   .. code-block:: text

      genome_id<TAB>/path/to/genome.fna

   Lines beginning with ``#`` are ignored. Common FASTA extensions (``.fna``, ``.fasta``, ``.fa``, ``.gz``) are stripped from ``genome_id`` in all outputs.

.. option:: -o, --output STR

   Output prefix used as the base name for all output files. Defaults to ``gemsparcl_out``.

   Example: ``-o my_run`` produces ``my_run_clusters.csv``, ``my_run_config.json``, etc.

.. option:: --existing-sketch PATH

   Skip the sketching step and use a pre-existing sketch file (``*.skm``).
   gemsparcl expects the matching ``*.skd`` dictionary file in the same directory.

   Useful when you want to re-cluster with a different threshold without re-running sketchlib.

.. option:: --existing-distances PATH

   Skip both sketching and distance computation and use an existing ``*.dists`` file.
   This is the fastest way to experiment with different ANI thresholds.

.. option:: --no-sketches

   Delete the sketch files (``*.skm``, ``*.skd``) after clustering. By default they are kept.

   .. warning::
      The ``query`` command requires the sketch files from the original clustering run. Using ``--no-sketches`` will make querying impossible on this dataset.

.. option:: --remove-intermediates

   Delete the distance file (``*.dists``) after clustering. By default it is kept. Sketch files are not affected by this flag.


Sketching options
-----------------

These options control how sketchlib sketches the genomes and how many neighbours it retains.

.. option:: -s, --sketch-size INT

   Number of hash values per sketch. Larger sketches give more accurate ANI estimates at the cost of more memory and compute time. Default: ``1000``.

   **Guideline:** 1000 is appropriate for most datasets. For very divergent genomes (ANI < 85 %) or when high precision is needed, increase to 5000–10000.

.. option:: -k, --kmer-length INT

   K-mer length used for sketching. Default: ``31``.

   **Guideline:** 31 is standard for bacterial genomes. Shorter k-mers (e.g. 21) increase sensitivity for more divergent comparisons but also increase false positives.

.. option:: --knn INT

   Number of nearest neighbours to retain per genome when computing distances. Default: ``50``.

   sketchlib only returns the ``knn`` closest genomes for each query, rather than all pairwise distances. This dramatically reduces the output size for large datasets.

   **Guideline:** The default of 50 is safe for most datasets. If you expect very large clusters (> 50 close neighbours), increase this value accordingly.

.. option:: --threads INT

   Number of CPU threads to use for sketching and distance computation. Default: ``4``.

.. option:: --use-inverted-index

   Build an inverted index before computing distances. This is significantly faster for datasets with > 100 000 genomes because it pre-clusters similar genomes before computing exact ANI.

   When this flag is set, gemsparcl calls ``sketchlib inverted precluster`` instead of the standard ``sketchlib dist``.

   .. note::
      The inverted index uses a reduced sketch size of 10 internally. This is a speed/precision trade-off that is well-suited for large-scale pre-clustering.


Clustering options
------------------

.. option:: -t, --threshold FLOAT

   ANI threshold for connecting genomes in the similarity network. Genome pairs with ANI ≥ this value are connected by an edge. Default: ``0.98`` (98 % ANI).

   - ``0.98`` — species-level clustering (standard for prokaryotes)
   - ``0.95`` — looser grouping, suitable for genus-level or divergent datasets
   - ``0.999`` — very tight, sub-species or strain-level clustering

   .. warning::
      Lowering the threshold significantly increases the number of edges and memory usage. Very low thresholds (< 0.90) on large datasets may require substantial RAM.


Completeness correction (for MAGs)
-----------------------------------

These options enable completeness correction, which adjusts ANI distances when one or both genomes are incomplete.
See :doc:`mags` for a detailed explanation of the algorithm.

.. option:: --completeness-file PATH

   Tab-separated file with genome completeness scores (values between 0 and 1):

   .. code-block:: text

      genome_id<TAB>0.95
      genome_id2<TAB>0.72

   Genomes not in this file are assumed to be complete (score = 1.0).

.. option:: --completeness-cutoff FLOAT

   Minimum completeness score below which correction is applied. Default: ``0.64``.
   Genomes with completeness ≥ this cutoff are treated as complete and are not corrected.


Refinement options
------------------

Network refinement detects and isolates genomes that act as bridges between otherwise-distinct clusters — a signature of genome contamination.
See :doc:`../background/refinement` for a full description of the algorithm.

.. option:: --refine

   Enable network refinement. After clustering, the network topology is analysed using jump detection on betweenness centrality to find bridge nodes and edges automatically — no threshold parameters to tune. A refined cluster assignment file is written alongside the original one.


Representatives options
-----------------------

.. option:: --representatives

   Select representative genomes for each cluster and write them to ``<prefix>_representatives.txt``.
   The clusters CSV is also updated with a boolean ``is_representative`` column.

   The number of representatives per cluster scales with cluster size: 1 representative per 500 genomes, with a minimum of 1.

   If a ``--completeness-file`` is provided, the genome(s) with the highest completeness score are chosen. Otherwise, selection is random.


Examples
--------

Minimal run:

.. code-block:: bash

   gemsparcl cluster -i genomes.txt -o run1

All features enabled:

.. code-block:: bash

   gemsparcl cluster \
     -i genomes.txt \
     -o run1 \
     --completeness-file completeness.tsv \
     --refine \
     --representatives \
     --threads 16

   # Then visualise separately
   gemsparcl visualise \
     --existing-distances run1.dists \
     --clusters-file run1_clusters.csv \
     -o run1_vis

Large dataset with inverted index:

.. code-block:: bash

   gemsparcl cluster \
     -i million_genomes.txt \
     -o big_run \
     --use-inverted-index \
     --threads 32 \
     --knn 100

Re-cluster with a lower threshold using existing distances:

.. code-block:: bash

   gemsparcl cluster \
     -i genomes.txt \
     -o run_95 \
     --existing-distances run1.dists \
     -t 0.95
