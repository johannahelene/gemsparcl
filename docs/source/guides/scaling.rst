Memory and Runtime Requirements
================================

A practical guide to the hardware you'll need for a given number of genomes, based on benchmarking on an Intel Xeon Gold 6336Y (32 threads).

For each dataset size, this is the peak memory used and the total time taken by ``cluster`` (sketching plus distance estimation, using ``--use-inverted-index`` for datasets over 100,000 genomes — see :doc:`cluster`).

.. list-table::
   :header-rows: 1
   :widths: 20 20 20

   * - Genomes
     - Peak memory
     - Total time
   * - 10,000
     - 0.6 GB
     - ~1 minute
   * - 100,000
     - 0.8 GB
     - ~11 minutes
   * - 500,000
     - 1.5 GB
     - ~1 hour
   * - 1,000,000
     - 3 GB
     - ~2 hours
   * - 5,200,000
     - 15 GB
     - ~14 hours

These numbers show that gemsparcl runs comfortably on a laptop or a single standard compute node, even at multi-million genome scale.

.. note::

   Below 100,000 genomes, the inverted-index prefilter (``--use-inverted-index``) adds overhead without much benefit, so it's best left off. Above that, it keeps both memory and runtime close to linear in the number of genomes.
