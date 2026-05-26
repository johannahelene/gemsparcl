gemsparcl
=========

.. image:: _static/logo.png
   :align: right
   :width: 200px
   :alt: gemsparcl logo

**Fast, scalable genome clustering using sketch-based ANI and network analysis.**

gemsparcl clusters bacterial genomes at any scale — from hundreds to millions — using sketch-based ANI estimation and network-based connected-component clustering.
New genomes can be assigned to an existing clustering locally, without sharing sequences, making it suitable for privacy-sensitive datasets.

.. grid:: 3
   :gutter: 2

   .. grid-item-card:: Getting Started
      :link: installation
      :link-type: doc

      Install gemsparcl and sketchlib, then cluster your first genome set in minutes.

   .. grid-item-card:: Guides
      :link: guides/index
      :link-type: doc

      Cluster, query, visualise, and work with MAGs — task-based guides for every workflow.

   .. grid-item-card:: Genome Privacy
      :link: guides/privacy
      :link-type: doc

      Query your genomes locally against a reference database. Your sequences never leave your machine.

Key features
------------

- **Scales to millions of genomes** — streaming, chunk-based distance processing avoids loading everything into memory
- **Three-command pipeline** — ``cluster`` once, ``query`` incrementally, ``visualise`` any time
- **Privacy-preserving** — download reference sketches and query entirely locally; no sequences shared
- **MAG-aware** — completeness correction adjusts distances for incomplete assemblies
- **Contamination detection** — network refinement isolates genomes that bridge otherwise-distinct clusters


.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   installation
   quickstart

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
