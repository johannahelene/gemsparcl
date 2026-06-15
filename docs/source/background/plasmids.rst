Plasmids and Clustering
========================

Bacterial genome assemblies often include plasmids alongside the chromosome. Plasmids can be gained, lost, or exchanged between strains via horizontal transfer, so two genomes of the same species may carry different plasmid complements — and the same plasmid can occasionally turn up in genomes from different species.

Despite this, plasmid content has very little effect on gemsparcl's clustering.


Why plasmids don't dominate the sketch
----------------------------------------

A MinHash sketch is built from k-mers drawn across the whole assembly. Plasmids are typically small relative to the chromosome — often a few kilobases to a few hundred kilobases, against a chromosome of several megabases. As a result, plasmid sequence usually makes up only a small fraction of the total k-mer content, and therefore only a small fraction of the sketch.

Gaining or losing a plasmid shifts the estimated ANI between two genomes by roughly the plasmid's share of the genome — typically well under a percentage point. This is far smaller than the gap between the clustering threshold (98% by default) and typical within-species ANI, so plasmid differences alone are very unlikely to move a genome pair across the threshold in either direction. We have done some experiments with plasmid-rich datasets and found that plasmid content has very little effect on the resulting clusters. (von Wachsmann et al. 2026 <https://doi.org/10.64898/2025.12.30.695181>_).

In practice, this means clustering is driven primarily by chromosomal similarity, and strains that differ only in their plasmid content will still cluster together.
