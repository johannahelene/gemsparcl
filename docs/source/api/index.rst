API Reference
=============

This section provides auto-generated documentation for all Python modules in gemsparcl.
It is primarily useful for developers who want to import gemsparcl functions in their own code or extend the tool.

.. toctree::
   :maxdepth: 1

   cli
   sketching
   clustering
   query
   refinement
   cytoscape
   representatives

Module overview
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Module
     - Responsibility
   * - :doc:`cli`
     - Entry points for the ``cluster`` and ``query`` commands (Click-based)
   * - :doc:`sketching`
     - Wraps sketchlib for genome sketching and ANI distance computation
   * - :doc:`clustering`
     - Builds the similarity network and extracts connected-component clusters
   * - :doc:`query`
     - Loads an existing clustering and assigns new query genomes to it
   * - :doc:`refinement`
     - Identifies and removes bridge nodes and edges (contamination detection)
   * - :doc:`cytoscape`
     - Exports the similarity network in GraphML format for Cytoscape
   * - :doc:`representatives`
     - Selects representative genomes per cluster
