Example Walkthrough
====================

This tutorial walks you through a complete gemsparcl run on a small, real dataset: 640 bacterial genomes from `AllTheBacteria <https://allthebacteria.org>`_, covering 15 species, plus 12 query genomes from `MGnify <https://www.ebi.ac.uk/metagenomics>`_. You will:

1. Build an input file (rfile) for gemsparcl
2. Cluster the genomes
3. Inspect and interpret the output
4. Visualise the network in Cytoscape
5. Query new genomes against the existing clusters
6. Visualise the query results alongside the reference network

Expected runtime: **~5–10 minutes** on a laptop with 4 threads.

Requirements
------------

- gemsparcl and sketchlib installed and on your ``PATH`` — see :doc:`/installation`
- ~2 GB free disk space for the genomes, plus ~500 MB for the outputs
- ~4 GB RAM
- 4 CPU cores recommended (adjust ``--threads`` if you have more or fewer)


Download the tutorial data
---------------------------

.. code-block:: bash

   wget https://ftp.ebi.ac.uk/pub/databases/metagenomics/software/gemsparcl/tutorial_data.tar.gz
   tar -xzf tutorial_data.tar.gz
   cd tutorial/

The tutorial directory contains:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Description
   * - ``genomes/``
     - 640 genome assemblies (``.fa.gz``)
   * - ``tutorial_metadata.tsv``
     - Known species labels for each genome, used for verification
   * - ``query_genomes/``
     - 12 MGnify query genomes (``.fa.gz``), used in `Querying New Genomes`_
   * - ``query_metadata.tsv``
     - Species and completeness class for the query genomes
   * - ``run_tutorial.sh``
     - Shell script that runs every step below automatically


Basic Clustering
------------------

Step 1: Build the input file (rfile)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

gemsparcl takes an **rfile** as input: a tab-separated file with two columns — a genome ID and the path to its assembly. Build one from the downloaded genomes:

.. code-block:: bash

   find genomes/ -name "*.fa.gz" | sort | \
       awk -F'/' '{id=$NF; sub(/\.fa\.gz$/, "", id); print id"\t"$0}' \
       > tutorial.rfile

Inspect the first few lines:

.. code-block:: bash

   head tutorial.rfile

.. code-block:: text

   SAMD00030057    genomes/SAMD00030057.fa.gz
   SAMD00053581    genomes/SAMD00053581.fa.gz
   SAMD00053584    genomes/SAMD00053584.fa.gz
   ...

Each line is ``<genome_id><TAB><path_to_assembly>``.


Step 2: Cluster the genomes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   gemsparcl cluster \
       -i tutorial.rfile \
       -o tutorial_basic \
       --threads 4 \
       --knn 50 \
       --threshold 0.98 \
       --sketch-size 1000 \
       --kmer-length 31

What these options mean:

.. list-table::
   :header-rows: 1
   :widths: 22 14 64

   * - Option
     - Value
     - Description
   * - ``-i``
     - ``tutorial.rfile``
     - The input rfile built in Step 1
   * - ``-o``
     - ``tutorial_basic``
     - Prefix for all output files
   * - ``--kmer-length``
     - 31
     - K-mer size for sketching — the standard choice for bacterial genomes
   * - ``--sketch-size``
     - 1000
     - Number of hash values per sketch. Higher gives more accurate ANI estimates at the cost of speed
   * - ``--threshold``
     - 0.98
     - ANI threshold for connecting genomes in the network. The default of 98% is intentionally stricter than the often-quoted 95% species boundary — see :ref:`why-98-percent`
   * - ``--knn``
     - 50
     - Number of nearest neighbours to keep per genome
   * - ``--threads``
     - 4
     - Number of CPU threads. Increase on larger machines

Sketch and distance files are kept by default, so they can be reused in `Querying New Genomes`_ without re-sketching.


Step 3: Inspect the output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After this run you will see several files prefixed with ``tutorial_basic``:

.. code-block:: text

   tutorial_basic_clusters.csv          <- main result: genome -> cluster assignment
   tutorial_basic_cluster_stats.txt     <- summary statistics
   tutorial_basic.skm / .skd            <- sketch files (reusable, see Querying New Genomes below)
   tutorial_basic.dists                 <- pairwise distance matrix
   tutorial_basic.log                   <- run log

See :doc:`outputs` for a full description of every file.

Cluster assignments
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   head tutorial_basic_clusters.csv

.. code-block:: text

   genome_id,cluster
   SAMN20483705,1
   SAMN10171290,1
   SAMN30869336,1
   SAMN02253080,1
   ...

Genomes assigned to the same cluster number are similar enough (above the ANI threshold) to be grouped together. Cluster IDs are arbitrary integers, numbered from 1 in descending order of cluster size.

Summary statistics
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cat tutorial_basic_cluster_stats.txt

.. code-block:: text

   Total clusters: 27
   Total genomes: 640
   Largest cluster: 55
   Singleton clusters: 7

**Singleton clusters** contain a single genome — no other genome was similar enough to link to it. This is expected for the rarer species in this dataset.

Verify clusters against known species
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``tutorial_metadata.tsv`` provides the true species label for each genome, so you can check that gemsparcl's clusters line up with species boundaries:

.. code-block:: bash

   join -t',' -1 1 -2 1 \
       <(tail -n +2 tutorial_basic_clusters.csv | sort) \
       <(sort tutorial_metadata.tsv | tr '\t' ',') \
       | sort -t',' -k2,2n | head -30

Genomes in the same cluster should belong to the same species (e.g. all *Salmonella enterica* genomes grouped together).


Visualisation
----------------

Step 4: Visualise the network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Export the network for Cytoscape:

.. code-block:: bash

   gemsparcl visualise \
       --existing-distances tutorial_basic.dists \
       --clusters-file tutorial_basic_clusters.csv \
       -o tutorial_vis

Open ``tutorial_vis_part1.graphml`` in `Cytoscape <https://cytoscape.org/>`_, apply a layout (e.g. "Prefuse Force Directed") and colour nodes by ``cluster`` (from ``tutorial_vis_annotations_part1.csv``). At the default 98% threshold, the 640 genomes form 27 clusters:

.. figure:: /_static/cluster_network_098.png
   :alt: Similarity network clustered at 98% ANI

   The tutorial dataset clustered at 98% ANI (27 clusters)

.. note::

   ``visualise`` rebuilds the network from the ``.dists`` file using its own ``--threshold`` (default 0.98), independently of whatever threshold was used for ``cluster``. If you re-cluster at a different threshold, pass the same ``--threshold`` to ``visualise`` so the network matches the cluster assignments — see :doc:`visualise`.

For comparison, here is the same dataset re-clustered and visualised at a 95% threshold (see :doc:`cluster` for re-clustering from existing distances with a different ``-t``):

.. figure:: /_static/cluster_network_095.png
   :alt: Similarity network clustered at 95% ANI

   The same dataset clustered at 95% ANI (17 clusters)

Notice that the *Escherichia coli* genomes, split across several clusters at 98%, merge into a single cluster at 95% — while the *Bacillus cereus* group clusters merge into one, losing the separation between *B. cereus*, *B. thuringiensis*, *B. anthracis* and *B. paraanthracis*. See :ref:`why-98-percent` for why 98% is the default and how to choose between the two.


Querying New Genomes
----------------------

Step 5: Build the query rfile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``query_genomes/`` contains 12 MGnify genomes from four species already present in the tutorial dataset (*Escherichia coli*, *Salmonella enterica*, *Klebsiella pneumoniae*, *Clostridioides difficile*). For each species there are two high-completeness genomes (≥ 0.90) and one low-completeness genome (~0.55–0.75):

.. code-block:: bash

   cat query_metadata.tsv

.. code-block:: text

   genome_id        species                  completeness  completeness_class
   MGYG000021310    Salmonella enterica      0.9988        high
   MGYG000026604    Klebsiella pneumoniae    0.6379        low
   MGYG000042272    Salmonella enterica      0.5776        low
   MGYG000050515    Clostridioides difficile 0.9951        high
   MGYG000104004    Klebsiella pneumoniae    0.9665        high
   MGYG000174365    Clostridioides difficile 0.6735        low
   MGYG000186038    Klebsiella pneumoniae    0.9998        high
   MGYG000189994    Salmonella enterica      1.0000        high
   MGYG000247767    Clostridioides difficile 0.9886        high
   MGYG000312773    Escherichia coli         0.9996        high
   MGYG000312778    Escherichia coli         0.5945        low
   MGYG000319183    Escherichia coli         0.9929        high

Build an rfile for the query genomes, just as in Step 1:

.. code-block:: bash

   find query_genomes/ -name "*.fa.gz" | sort | \
       awk -F'/' '{id=$NF; sub(/\.fa\.gz$/, "", id); print id"\t"$0}' \
       > query.rfile


Step 6: Query the existing clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``gemsparcl query`` assigns each new genome to a cluster directly, using the reference sketches (``tutorial_basic.skm``/``.skd``) and cluster assignments (``tutorial_basic_clusters.csv``) from Step 2 — no re-sketching or re-clustering of the reference dataset required:

.. code-block:: bash

   gemsparcl query tutorial_basic query.rfile \
       --clusters-file tutorial_basic_clusters.csv \
       -o query_basic

This produces ``query_basic_query_results.csv``, one row per query genome:

.. code-block:: text

   query_id,GCU,note,top_hit_genome,top_hit_ani
   MGYG000021310,1,assigned,SAMN10505653,0.9989
   MGYG000026604,11,assigned,SAMEA110448741,0.9975
   MGYG000042272,1,assigned,SAMN10268380,0.9910
   MGYG000050515,14,assigned,SAMEA2187309,0.9947
   MGYG000104004,11,assigned,SAMD00163748,0.9919
   MGYG000174365,14,assigned,SAMEA3375129,0.9919
   MGYG000186038,11,assigned,SAMD00163748,0.9943
   MGYG000189994,1,assigned,SAMN10505653,0.9991
   MGYG000247767,14,assigned,SAMEA2187309,0.9930
   MGYG000312773,10,assigned,SAMN11811181,0.9951
   MGYG000312778,10,assigned,SAMN08462632,0.9857
   MGYG000319183,10,assigned,SAMD00136949,0.9847

All 12 query genomes are ``assigned`` (no contamination, no unassigned genomes), and each species lands in a single cluster shared by all three of its query genomes — including the low-completeness ones:

- *Salmonella enterica* → cluster 1 (``MGYG000021310``, ``MGYG000042272``, ``MGYG000189994``)
- *Klebsiella pneumoniae* → cluster 11 (``MGYG000026604``, ``MGYG000104004``, ``MGYG000186038``)
- *Clostridioides difficile* → cluster 14 (``MGYG000050515``, ``MGYG000174365``, ``MGYG000247767``)
- *Escherichia coli* → cluster 10 (``MGYG000312773``, ``MGYG000312778``, ``MGYG000319183``)

Even the genomes down to ~58% completeness (``MGYG000042272``, ``MGYG000312778``, ``MGYG000026604``, ``MGYG000174365``) are assigned correctly here without any completeness correction — this dataset's reference genomes are themselves ≥98% complete, so correction makes no difference. For real MAG datasets, ``gemsparcl query`` also accepts ``--ref-completeness-file``/``--query-completeness-file``; see :doc:`query` and :doc:`mags`.

See :doc:`query` for the full meaning of the ``note`` and ``GCU`` columns, including how contaminated or novel query genomes are flagged.


.. _step7-visualise-queries:

Step 7: Visualise queries alongside the reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``gemsparcl visualise`` can merge the query-vs-reference distances from Step 6 (``query_basic.dists``) with the reference distances from Step 2 (``tutorial_basic.dists``) into a single network, and use ``query_basic_query_full.csv`` — which already has ``GCU``, ``is_query`` and ``note`` for all 652 genomes — to annotate every node. Adding ``tutorial_metadata.tsv`` and ``query_metadata.tsv`` as ``--metadata-file`` inputs also brings in the known ``species`` (and, for queries, ``completeness``/``completeness_class``) for every genome:

.. code-block:: bash

   gemsparcl visualise \
       --existing-distances tutorial_basic.dists \
       --query-distances query_basic.dists \
       --clusters-file query_basic_query_full.csv \
       --metadata-file tutorial_metadata.tsv \
       --metadata-file query_metadata.tsv \
       -o tutorial_query_vis

This builds a network of all 652 genomes (the 640 reference genomes plus the 12 query genomes) and finds the same 27 clusters as Step 4 — with the query genomes connected into the clusters they were assigned to in Step 6:

.. code-block:: text

   Network: 652 nodes, 12620 edges, 27 components
   Created 1 GraphML file(s): tutorial_query_vis_part1.graphml

Every node in ``tutorial_query_vis_part1.graphml`` (and the matching ``tutorial_query_vis_annotations_part1.csv``) carries the following attributes:

- ``cluster_id`` — the cluster (GCU) the genome belongs to, for **all** 27 clusters, not just the ones the queries hit (from ``query_basic_query_full.csv``)
- ``is_query`` — ``True`` for the 12 query genomes, ``False`` for the 640 reference genomes (from ``query_basic_query_full.csv``)
- ``note`` — ``existing`` for reference genomes, or the query classification from Step 6 (``assigned`` etc., from ``query_basic_query_full.csv``)
- ``species`` — the known species label for every genome (from ``tutorial_metadata.tsv`` and ``query_metadata.tsv``)
- ``completeness`` and ``completeness_class`` — for the 12 query genomes only (from ``query_metadata.tsv``)

Open ``tutorial_query_vis_part1.graphml`` in `Cytoscape <https://cytoscape.org/>`_, apply a layout (e.g. "Prefuse Force Directed"), then in the Style panel:

- colour nodes by ``cluster_id``, as in Step 4, or by ``species`` to check that clusters line up with species boundaries, and
- map ``is_query`` to a distinct shape or border colour, to see exactly where each of the 12 query genomes landed within the full 27-cluster network.

.. figure:: /_static/cluster_network_query.png
   :alt: Similarity network with the 12 query genomes highlighted in green within the 27 reference clusters

   The 27 clusters from Step 4, with the 12 query genomes (green) shown connected into the clusters they were assigned to in Step 6

See :doc:`visualise` for more on combining query and reference distances and metadata.


Dataset details
----------------

Reference genomes (640 total)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 640 genomes span 15 species (25–55 genomes each), plus 5 additional rare species each represented by a single genome:

.. list-table::
   :header-rows: 1
   :widths: 70 30

   * - Species
     - Genomes
   * - *Salmonella enterica*
     - 55
   * - *Escherichia coli*
     - 55
   * - *Bacillus cereus*
     - 50
   * - *Bacillus anthracis*
     - 50
   * - *Bacillus paranthracis*
     - 50
   * - *Bacillus subtilis*
     - 50
   * - *Staphylococcus aureus*
     - 45
   * - *Mycobacterium tuberculosis*
     - 45
   * - *Streptococcus pneumoniae*
     - 40
   * - *Bacillus thuringiensis*
     - 40
   * - *Klebsiella pneumoniae*
     - 35
   * - *Campylobacter jejuni*
     - 35
   * - *Listeria monocytogenes*
     - 30
   * - *Clostridioides difficile*
     - 30
   * - *Pseudomonas aeruginosa*
     - 25
   * - Rare species (singletons)
     - 5

The four *Bacillus cereus* group species (*B. cereus*, *B. anthracis*, *B. paranthracis*, *B. thuringiensis*) plus *B. subtilis* are featured in the threshold comparison in `Visualisation`_.

All genomes have completeness ≥ 0.98 (CheckM2). Species labels are given in ``tutorial_metadata.tsv`` for verification.

Query genomes (12 total)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Selected from MGnify: 2 high-completeness (≥ 0.90) and 1 low-completeness (~0.55–0.75) genome per species, for the four species used in `Querying New Genomes`_:

.. list-table::
   :header-rows: 1
   :widths: 50 25 25

   * - Species
     - High completeness
     - Low completeness
   * - *Escherichia coli*
     - 2
     - 1
   * - *Salmonella enterica*
     - 2
     - 1
   * - *Klebsiella pneumoniae*
     - 2
     - 1
   * - *Clostridioides difficile*
     - 2
     - 1

Completeness values and species labels are given in ``query_metadata.tsv``.


Next steps
----------

- :doc:`query` — assign new genomes to these clusters without re-clustering everything
- :doc:`visualise` — export the network for Cytoscape
- :doc:`mags` — completeness correction for MAG datasets
- :doc:`/background/refinement` — automatically detect and isolate likely contaminated genomes with ``--refine``
- :doc:`/background/index` — how the clustering algorithm actually works
