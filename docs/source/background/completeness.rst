Completeness Correction for MAGs
=================================

Enable with ``gemsparcl cluster --completeness-file <file>``. See :doc:`../guides/mags` for the file format and usage.


The problem: incomplete assemblies underestimate ANI
-----------------------------------------------------

Metagenome-Assembled Genomes (MAGs) are frequently incomplete. A typical MAG may contain only 70–90% of the expected genomic sequence, depending on for example sequencing depth and the binning algorithm used.

This incompleteness directly biases pairwise ANI estimates. If genome A has 80% completeness, it shares at most 80% of its k-mers with a perfect reference — even if the shared portion is 100% identical. The sketching-based ANI estimate will therefore be systematically **lower** than the true ANI between the two organisms, pushing genome pairs below the clustering threshold and causing them to be placed in separate clusters when they should be together.


How the correction works
-------------------------

When you supply a ``--completeness-file``, gemsparcl applies a correction to the ANI estimates based on the completeness scores of both genomes in each pair.

For example, two MAGs from the same species but each assembled to 80% completeness will share less k-mer content than two complete genomes from the same species, causing their raw Jaccard similarity to be deflated. The completeness correction adjusts for this, recovering an accurate similarity estimate despite the missing sequence.

The correction is applied by sketchlib internally during distance computation and does not affect the sketch files themselves.

Genomes not listed in the completeness file are assumed to be complete (completeness = 1.0) and receive no correction.


The completeness cutoff
-------------------------

For a genome pair with completeness ``c1`` and ``c2``, correction is only applied if ``c1 * c2 >= --completeness-cutoff`` (default: 0.64). Below this product, the raw, uncorrected ANI estimate is used instead.

This means correction kicks in once both genomes are reasonably complete — for two equally-complete genomes, ``c^2 >= 0.64`` requires ``c >= 0.8``, so by default both need to be at least ~80% complete (a more complete genome can compensate for a less complete partner). Below this combined threshold, the correction itself becomes unreliable — highly fragmented assemblies may have too little shared sequence for meaningful ANI estimation.
