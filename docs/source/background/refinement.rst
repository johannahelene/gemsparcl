Network Refinement and Contamination Detection
===============================================

Enable with ``gemsparcl cluster --refine``.


The problem: contaminated genomes as bridges
--------------------------------------------

A contaminated genome assembly contains sequence from two or more distinct organisms. In a genome similarity network, a contaminated genome will have sequence that matches genomes in multiple distinct clusters — it acts as a *bridge* connecting clusters that should be separate.

Without refinement, this bridge causes the two clusters to merge into one.

Jump-detection: the core idea
------------------------------

Rather than setting fixed percentile thresholds, gemsparcl uses **jump detection** to find outliers automatically.
The idea is simple: sort all betweenness values from lowest to highest and look for the largest gap between consecutive values. Everything *above* that gap is an outlier — a node (or edge) with disproportionately high betweenness compared to its neighbours in the distribution.

This approach is parameter-free and self-calibrating: it adapts to the actual distribution of values in each component rather than applying a fixed cutoff. If all betweenness values are similar (no meaningful gap), nothing is flagged.

.. code-block:: text

   Sorted betweenness:  0.01  0.02  0.02  0.03  0.04  0.31  0.33
                                                      ↑
                                               largest gap here
                                         → 0.31 and 0.33 are flagged


How bridge nodes are identified
---------------------------------

For each component with three or more nodes, gemsparcl runs a two-step process:

**Step 1 — Jump detection on node betweenness centrality**

Betweenness centrality measures how often a node lies on the shortest path between other pairs of nodes. A bridge genome connecting two otherwise-separate clusters will have disproportionately high betweenness — most shortest paths between the two sides must pass through it.

gemsparcl sorts the betweenness values for all nodes in the component, finds the largest gap, and flags every node above that gap as a candidate. If there is no meaningful gap (all values identical), no candidates are selected.

**Step 2 — Sanity check: below-median degree**

Not every high-betweenness node is a contamination bridge. A node can have high betweenness simply because it is a highly-connected hub. To filter these out, gemsparcl checks that each candidate also has **below-median degree** within its component. A true bridge genome has few genuine connections to either side of the bridge; a hub has many.

A node is classified as a bridge node only if it passes *both* checks: outlier betweenness **and** below-median degree.


How bridge edges are identified
---------------------------------

Independently of the node analysis, gemsparcl applies the same jump-detection approach to **edge betweenness centrality** — the fraction of shortest paths that pass through each edge. Edges with outlier betweenness are flagged as bridge edges.


Removal strategy
-----------------

gemsparcl uses a conservative two-step removal strategy that tries to be as minimally invasive as possible:

1. **For bridge edges that connect two bridge nodes** — gemsparcl first tries cutting just the edge. It checks whether removing only that edge is enough to split the component. If it is, both nodes are *not* isolated (the edge cut alone was sufficient) and the nodes are left in place.

2. **For remaining bridge nodes** — any bridge node not resolved by an edge-only cut has all of its edges removed, turning it into a singleton. The node itself is retained in the output.

3. **All bridge edges are also removed** — both those already handled by node isolation and any remaining bridge edges between non-bridge nodes.

After all removals the connected components are recalculated. Clusters that were artificially merged by a bridge will now appear as separate components.

The refined assignments are written to ``<prefix>_refined_clusters.csv``. The original ``_clusters.csv`` is always kept so you can compare before and after.


Approximation for large components
------------------------------------

Exact betweenness centrality is O(N·E) — too slow for components with tens of thousands of nodes. For components with more than 10 000 nodes, gemsparcl uses an approximation: it samples 1 000 nodes as sources for shortest-path calculations, giving a good statistical estimate of the betweenness distribution in a fraction of the time.


No parameters to tune
----------------------

The jump-detection algorithm requires no threshold configuration — it adapts automatically to the betweenness distribution of each component. The only option is ``--refine`` itself.

This is by design: percentile-based thresholds require the user to know what "high" betweenness looks like in their specific dataset. Jump detection sidesteps this by finding structural outliers directly.

.. note::

   Refinement is only applied to components with **three or more nodes**. Singletons and pairs are not analysed, as betweenness is not meaningful for components that small.
