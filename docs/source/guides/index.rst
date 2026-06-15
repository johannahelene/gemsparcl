Guides
======

Task-based guides for everything you can do with gemsparcl.

.. toctree::
   :maxdepth: 2

   cluster
   query
   visualise
   privacy
   mags
   outputs
   scaling

Workflow
--------

The three commands form a natural pipeline:

.. code-block:: text

   gemsparcl cluster   →   gemsparcl query   →   gemsparcl visualise
   (build clusters)        (assign new genomes)    (export to Cytoscape)

**cluster** computes ANI distances, builds a similarity network, and assigns each genome to a cluster.
Run this once on your reference set and keep the sketch and distance files.

**query** assigns new genomes to the existing clustering without re-sketching the reference.
Sketch parameters are read automatically from the reference database.
For privacy-sensitive datasets, reference sketches can be downloaded and queried entirely locally — see :doc:`privacy`.

**visualise** takes an existing distances file and exports the similarity network as GraphML files for Cytoscape.
It is independent of ``cluster`` and ``query`` — run it any time, with any threshold.
