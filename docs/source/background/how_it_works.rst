Pipeline Overview
=================

gemsparcl clusters genomes in three main stages: sketching and distance estimation, network construction, and cluster extraction via connected components.

Stage 1 — Sketching and ANI estimation
---------------------------------------

Whole-genome ANI (Average Nucleotide Identity) is the standard measure of genomic similarity between bacteria. Traditional approaches compute ANI by aligning genome pairs, which does not scale to millions of genomes.

gemsparcl delegates this step entirely to `sketchlib <https://github.com/bacpop/sketchlib.rust>`_, a Rust implementation of MinHash sketching for genomic distances.

**MinHash sketching**

Rather than comparing genomes nucleotide-by-nucleotide, sketchlib converts each genome into a small, fixed-size *sketch* — a set of hash values derived from the k-mers in the genome. Two sketches can be compared in microseconds to estimate the Jaccard similarity of the underlying k-mer sets, from which ANI is derived.

The key parameters are:

- **k-mer length** (``-k``, default 31): the length of substrings used to build the sketch. Longer k-mers are more specific; shorter k-mers are more sensitive for divergent comparisons.
- **Sketch size** (``-s``, default 1000): the number of hash values retained per genome. Larger sketches give more accurate ANI estimates.

**Nearest-neighbour distances**

By default, sketchlib does not compute all pairwise distances — for N genomes that would be N² comparisons. Instead, it uses a k-nearest-neighbours (kNN) approach: for each genome it returns only the ``--knn`` most similar genomes (default: 50).

This makes the computation roughly linear in N rather than quadratic, and keeps the output file manageable.

**Inverted index (for very large datasets)**

For datasets of > 100 000 genomes, the ``--use-inverted-index`` flag activates a pre-clustering step. sketchlib builds an inverted index from reduced sketches (size 10) and uses it to identify candidate pairs before computing exact ANI. This further reduces the number of comparisons that need to be evaluated.


Stage 2 — Similarity network construction
------------------------------------------

After distance computation, gemsparcl builds a **similarity network** (also called a genome graph):

- Each genome is a **node**
- Two genomes are connected by an **edge** if their estimated ANI ≥ the threshold (``-t``, default 0.98)

The threshold determines what counts as "the same species" in your dataset. At 98 % ANI, gemsparcl clusters at approximately the bacterial species boundary as defined by GTDB and widely used in the field.

The network is built using `networkx <https://networkx.org>`_ and is processed in a streaming, chunk-based fashion so that datasets with hundreds of millions of distance pairs can be handled without loading everything into memory at once.


Stage 3 — Cluster extraction via connected components
------------------------------------------------------

Clustering is performed by finding the **connected components** of the similarity network. A connected component is a maximal set of nodes where every node can reach every other node via edges — in other words, a group of genomes that are all similar to at least one other member of the group, even if not all pairs are directly connected.

This approach has several desirable properties:

- **Transitive similarity** — if genome A is similar to B, and B is similar to C, then A and C end up in the same cluster even if A and C are not directly connected. This reflects the fact that diversity within a species is continuous.
- **No parameters to tune** — unlike k-means or DBSCAN, connected-component clustering does not require specifying the number of clusters or a neighbourhood radius. The ANI threshold is the only parameter.
- **Scalable** — NetworkX's connected-components algorithm is O(N + E) where N is the number of nodes and E is the number of edges.

Clusters are numbered 1, 2, 3, … in descending order of size (cluster 1 is always the largest).

**Singletons**

Genomes that have no neighbours above the threshold form *singleton clusters* — components of size 1. These may represent truly novel lineages, highly incomplete assemblies, or sequencing errors.


Memory-efficient processing
----------------------------

The distance file produced by sketchlib for a million-genome dataset can contain hundreds of millions of lines. gemsparcl reads it in chunks of 100 000 rows and processes each chunk in parallel using Python's ``multiprocessing`` module. The filtered edges from all chunks are then merged into the final network.

This design means gemsparcl's memory footprint is determined by the network (the kept edges after thresholding), not by the raw distance file.
