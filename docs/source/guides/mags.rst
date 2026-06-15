Completeness Correction for MAGs
=================================

Enable with ``gemsparcl cluster --completeness-file <file>``.

Metagenome-Assembled Genomes (MAGs) are often incomplete, which can artificially lower their estimated ANI to other genomes and split a single species across multiple clusters. ``--completeness-file`` corrects for this. See :doc:`../background/completeness` for why this matters and how the correction works.


Completeness file format
-------------------------

Tab-separated, one genome per line:

.. code-block:: text

   genome_id<TAB>0.95
   another_genome<TAB>0.72
   third_genome<TAB>1.0

Completeness values should be between 0 and 1. A value of 1.0 means the genome is considered complete. The ``genome_id`` must match the identifiers in your rfile.

gemsparcl automatically strips ``.fna``, ``.fasta``, and ``.fa`` (optionally followed by ``.gz``) from genome IDs in your rfile, qfile, and completeness files before processing, so ``genome1.fna.gz`` and ``genome1`` are treated as the same genome everywhere — you don't need to match these manually.

You can use tools like `CheckM <https://github.com/Ecogenomics/CheckM>`_ or `CheckM2 <https://github.com/chklovski/CheckM2>`_ to estimate genome completeness before running gemsparcl.

CheckM and CheckM2 report completeness as a percentage (e.g. ``98.0``), but gemsparcl expects a fraction between 0 and 1 (e.g. ``0.98``). Convert a tab-separated ``genome_id<TAB>completeness`` file with:

.. code-block:: bash

   awk -F'\t' -v OFS='\t' '{print $1, $2/100}' checkm_completeness.tsv > completeness.tsv


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
4. If you have very incomplete genomes (< 50%), consider filtering them out before clustering — they add noise and may not cluster reliably even with correction
