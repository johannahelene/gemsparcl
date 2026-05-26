Completeness Correction for MAGs
=================================

Enable with ``gemsparcl cluster --completeness-file <file>``.

The problem: incomplete assemblies underestimate ANI
-----------------------------------------------------

Metagenome-Assembled Genomes (MAGs) are frequently incomplete — a typical MAG may contain only 70–90 % of the genome's genes, depending on the sequencing depth and binning algorithm used.

This incompleteness directly biases pairwise ANI estimates. If genome A has 80 % completeness, it shares at most 80 % of its k-mers with a perfect reference — even if the shared portion is 100 % identical. The sketching-based ANI estimate will therefore be systematically **lower** than the true ANI between the two organisms, pushing genome pairs below the clustering threshold and causing them to be placed in separate clusters when they should be together.


Completeness correction
-----------------------

When you supply a ``--completeness-file``, gemsparcl applies a correction to the ANI estimates based on the completeness scores of both genomes in each pair.

The correction adjusts for the fraction of the genome that is missing, so that a pair of 80 %-complete MAGs that share 100 % identical sequence will receive a corrected ANI close to 1.0 rather than 0.8.

The correction is applied by sketchlib internally during distance computation and does not affect the sketch files themselves.

Genomes not listed in the completeness file are assumed to be complete (completeness = 1.0) and receive no correction.


Completeness file format
-------------------------

Tab-separated, one genome per line:

.. code-block:: text

   genome_id<TAB>0.95
   another_genome<TAB>0.72
   third_genome<TAB>1.0

Completeness values should be between 0 and 1. A value of 1.0 means the genome is considered complete. The ``genome_id`` must match the identifiers in your rfile (after stripping file extensions).

You can use tools like `CheckM <https://github.com/Ecogenomics/CheckM>`_ or `CheckM2 <https://github.com/chklovski/CheckM2>`_ to estimate genome completeness before running gemsparcl.


The completeness cutoff
-----------------------

The ``--completeness-cutoff`` parameter (default: 0.64) sets the minimum completeness below which correction is applied. Genomes with completeness ≥ this cutoff are treated as effectively complete and are **not** corrected.

The default of 0.64 reflects the practical lower bound at which completeness correction produces reliable results. Highly fragmented assemblies (< 64 % completeness) may have too little shared sequence for meaningful ANI estimation regardless of correction.


Using completeness correction with ``query``
--------------------------------------------

If the original ``cluster`` run used completeness correction, provide a combined completeness file that covers **both** the reference genomes and the new query genomes:

.. code-block:: bash

   gemsparcl query bactdb new_genomes.rfile \
     --clusters-file bactdb_clusters.csv \
     --completeness-file combined_completeness.tsv \
     -o query_out

If the reference clustering used completeness correction and you do not provide a ``--completeness-file`` for the query, distances will be computed without correction. This can cause new genomes to fall below the ANI threshold even when they genuinely belong to an existing cluster, resulting in incorrect ``no_hit`` classifications.


Recommendations for MAG datasets
----------------------------------

1. Always run completeness estimation (CheckM/CheckM2) before clustering MAGs
2. Use ``--completeness-file`` with completeness values for all genomes
3. Consider using ``--refine`` to catch contaminated bins that survived binning QC
4. If you have very incomplete genomes (< 50 %), consider filtering them out before clustering — they add noise and may not cluster reliably even with correction
