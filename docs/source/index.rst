gemsparcl
=========

**Fast, scalable genome clustering using sketch-based ANI and network analysis.**

gemsparcl clusters bacterial genomes at any scale — from hundreds to millions — using sketch-based ANI estimation and network-based connected-component clustering.
New genomes can be assigned to an existing clustering locally, without sharing sequences, making it suitable for privacy-sensitive datasets.

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: Installation
      :link: installation
      :link-type: doc
      :class-card: square-card

      Install gemsparcl and sketchlib, then cluster your first genome set in minutes.

   .. grid-item-card:: How-To Guides
      :link: guides/index
      :link-type: doc
      :class-card: square-card

      Cluster, query, visualise, wrangle MAGs — step-by-step instructions for everything gemsparcl can do.

   .. grid-item-card:: Example Dataset
      :link: guides/example
      :link-type: doc
      :class-card: square-card

      Grab a small real dataset and run the whole pipeline yourself, start to finish.

   .. grid-item-card:: Background
      :link: background/index
      :link-type: doc
      :class-card: square-card

      How the clustering actually works, and why we made the choices we did — for when you want more than the gist.

The problem
-----------

If you have a large collection of bacterial genomes — say, everything from a public database — a natural first question is: which of these genomes are essentially "the same" (the same species/close relatives), and which are different?

Answering this by comparing every genome to every other genome becomes impossibly slow once you have more than a few thousand genomes. For a million genomes, that's 1 trillion comparisons.

What gemsparcl does
--------------------

gemsparcl works in three steps:

1. **Sketching**: each genome is turned into a small "fingerprint" (a MinHash sketch) that can be compared in microseconds instead of minutes. This step is handled by `sketchlib <https://github.com/bacpop/sketchlib.rust>`_.
2. **Estimating similarity**: sketches are compared to estimate Average Nucleotide Identity (ANI), the standard measure of how similar two bacterial genomes are.
3. **Building a network and finding clusters**: genomes that are similar enough (≥ 98% ANI by default — higher than the more commonly used 95% species boundary, see :ref:`why-98-percent`) are connected to each other. Groups of connected genomes form a cluster, there's no need to decide in advance how many clusters there should be.

Sketches keep memory use low even for millions of genomes. By default, gemsparcl still compares every genome against every other genome — just using sketches instead of full alignments, which is already orders of magnitude faster than traditional approaches. For very large datasets, an **inverted index** can pre-filter candidate pairs first, avoiding the all-vs-all comparison — see :doc:`background/how_it_works`.

Key features
------------

- **Low memory footprint** — cluster large genome collections without needing a high-memory machine
- **Three-command pipeline** — ``cluster`` once, ``query`` incrementally, ``visualise`` any time. New genomes can be assigned to existing clusters without re-clustering everything — see :doc:`guides/query`.
- **MAG-aware** — completeness correction adjusts distances for incomplete assemblies, so an incomplete genome isn't left out of a cluster just because part of it is missing — see :doc:`guides/mags`.
- **Privacy-preserving** — download reference sketches and query entirely locally; no sequences shared — see :doc:`guides/privacy`.

Read the paper!
----------------

von Wachsmann, J., Lorenz, L., Russell, M., Gurbich, T., Rodríguez-Bouza, V., Horsfield, S., Lees, J. A., & Finn, R. D. *Rapid and Consistent Genome Clustering at the Scale of Millions of MAGs and Isolates.* bioRxiv (2025). https://doi.org/10.64898/2025.12.30.695181

For more detail on the algorithm itself, see :doc:`background/how_it_works`.


.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   installation
   quickstart
   guides/example

.. toctree::
   :maxdepth: 2
   :caption: Guides
   :hidden:

   guides/index

.. toctree::
   :maxdepth: 2
   :caption: Background
   :hidden:

   background/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   api/index

.. toctree::
   :maxdepth: 1
   :caption: Project
   :hidden:

   changelog
