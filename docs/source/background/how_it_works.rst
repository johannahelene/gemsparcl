Pipeline Overview
=================

gemsparcl clusters genomes in three main stages: sketching, distance estimation, and network construction.

gemsparcl uses `sketchlib <https://github.com/bacpop/sketchlib.rust>`_ for sketching and distance estimation — a Rust implementation of MinHash sketching for genomic distances.

Stage 1 — Sketching
--------------------

Whole-genome ANI (Average Nucleotide Identity) is the standard measure of genomic similarity between bacteria. Traditional approaches compute ANI by aligning genome pairs, which does not scale to millions of genomes.

**MinHash sketching**

Rather than comparing genomes nucleotide-by-nucleotide, sketchlib converts each genome into a small, fixed-size *sketch* — a set of hash values derived from the k-mers in the genome, so a fingerprint. Two sketches can be compared in microseconds to estimate the Jaccard similarity of the underlying k-mer sets, from which ANI is derived.

The key parameters are:

- **k-mer length** (``-k``, default 31): the length of substrings used to build the sketch. Longer k-mers are more specific; shorter k-mers are more sensitive.
- **Sketch size** (``-s``, default 1000): the number of hash values retained per genome. Larger sketches give more accurate ANI estimates. (Larger sketch sizes also increase runtime and memory use, but the default of 1000 is a good balance for most applications.)


Stage 2 — Distance estimation
-------------------------------

**Nearest-neighbour distances**

By default, sketchlib does not save all pairwise distances — for N genomes that would be N²/2 pairwise distances (so for 1M genomes that would be 500 billion pairwise distances). Instead, it uses a k-nearest-neighbours (kNN) approach: for each genome it returns only the ``--knn`` most similar genomes (default: 50). This keeps the output file manageable.

**Inverted index (for very large datasets)**

For datasets of > 100 000 genomes we suggest using the ``--use-inverted-index`` flag, which activates a pre-clustering step. sketchlib builds an inverted index from reduced sketches (size 10) and uses it to identify candidate pairs before computing exact ANI. This further reduces the number of full comparisons that need to be evaluated (leading to a sub-quadratic runtime).


Stage 3 — Network construction
--------------------------------

After distance computation, gemsparcl builds a **similarity network** (also called a genome graph):

- Each genome is a **node**
- Two genomes are connected by an **edge** if their estimated ANI ≥ the threshold (``-t``, default 0.98)

The threshold determines what counts as "the same species" in your dataset.

.. _why-98-percent:

Why 98% and not 95%?
~~~~~~~~~~~~~~~~~~~~~~~

95% ANI is often quoted as *the* bacterial species boundary, but in practice species boundaries are fuzzy: ANI between genomes from two different species can exceed 95%, and ANI between genomes of the same species can dip below it (`Parks et al. 2022 <https://doi.org/10.1093/nar/gkab776>`_). GTDB handles this fuzziness by anchoring each species cluster around a representative genome.

Because gemsparcl does not anchor clusters around representative genomes, any pair above the threshold will be clustered together. By default, gemsparcl therefore uses a stricter 98% threshold rather than the conventional 95% ANI species cutoff, to avoid merging distinct species into the same cluster. This is a conservative choice that prioritises **precision over recall**:

- **Precision** — of the genomes placed in the same cluster, how many truly belong to the same species? A higher threshold reduces the risk of merging genomes from distinct species into one cluster.
- **Recall** — of the genomes belonging to a given species, how many end up together in the same cluster? A lower threshold reduces the risk of splitting a single, diverse species across several clusters.

The figures below show the same 640-genome dataset from :doc:`../guides/example`, clustered at both thresholds:

.. grid:: 2
   :gutter: 2

   .. grid-item::

      .. figure:: /_static/cluster_network_098.png
         :alt: Similarity network clustered at 98% ANI

         **98% ANI** — 27 clusters

   .. grid-item::

      .. figure:: /_static/cluster_network_095.png
         :alt: Similarity network clustered at 95% ANI

         **95% ANI** — 17 clusters

At 98%, the highly diverse *E. coli* genomes split across several separate clusters — but members of the *Bacillus cereus* group (*B. cereus*, *B. thuringiensis*, *B. anthracis* and *B. paraanthracis*) remain in distinct, "clean" clusters that reflect their separate species designations.

At 95%, those *Bacillus* clusters merge into a single larger cluster — losing the distinction between species — while the *E. coli* genomes are unified into one cluster.

Neither threshold is "correct"; which matters more depends on your dataset and question. The threshold can be changed cheaply by re-clustering from existing distances — see :doc:`../guides/cluster`. For large, diverse datasets we found 98% to resolve genomes better overall, which is why it is the default.

The network is built using `networkx <https://networkx.org>`_ so that datasets with hundreds of millions of distance pairs can be handled without loading everything into memory at once.

Clusters are numbered 1, 2, 3, … in descending order of size (cluster 1 is always the largest).

**Singletons**

Genomes that have no neighbours above the threshold form *singleton clusters* — components of size 1. These may represent truly novel lineages, highly incomplete assemblies, or sequencing errors.
