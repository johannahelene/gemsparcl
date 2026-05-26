Installation
============

gemsparcl requires two components: the **sketchlib** binary (a Rust tool for fast ANI estimation) and the **gemsparcl** Python package itself.

Step 1 — Install sketchlib
--------------------------

sketchlib is an external binary that gemsparcl calls to perform all sketching and distance calculations.
Choose the installation method that suits your setup.

**conda (recommended)**

.. code-block:: bash

   conda install -c bioconda sketchlib

No further configuration is needed — sketchlib will be found automatically on your ``PATH``.

**Pre-built binary (Linux)**

Download the latest binary from the `sketchlib releases page <https://github.com/bacpop/sketchlib.rust/releases>`_, then make it executable:

.. code-block:: bash

   chmod +x sketchlib
   export SKETCHLIB_PATH=/path/to/sketchlib

Add the ``export`` line to your ``~/.bashrc`` or ``~/.zshrc`` to make it permanent.

**Build from source (Mac M1/M2/M3/M4 or custom optimisation)**

This requires the `Rust toolchain <https://rustup.rs>`_:

.. code-block:: bash

   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env

   # Standard install via cargo:
   cargo install sketchlib

   # Or compile with native CPU optimisations (recommended for M-series Macs):
   git clone https://github.com/bacpop/sketchlib.rust.git
   cd sketchlib.rust
   RUSTFLAGS="-C target-cpu=native" cargo install --path .

   export SKETCHLIB_PATH=$(which sketchlib)

.. note::

   **Mac users:** If macOS warns that the binary is from an unidentified developer, remove the quarantine attribute:

   .. code-block:: bash

      xattr -d "com.apple.quarantine" ./sketchlib


Step 2 — Install gemsparcl
---------------------------

gemsparcl requires **Python ≥ 3.10**.

.. code-block:: bash

   git clone https://github.com/johannahelene/gemsparcl.git
   cd gemsparcl
   pip install .

To install in editable mode (for development):

.. code-block:: bash

   pip install -e ".[dev]"

This also installs the test dependencies (``pytest``, ``pytest-cov``, ``ruff``).


Step 3 — Verify
---------------

Check that both tools are available:

.. code-block:: bash

   gemsparcl --version
   sketchlib --version   # or: $SKETCHLIB_PATH --version

You should see version strings for both. If gemsparcl cannot find sketchlib, set the environment variable explicitly:

.. code-block:: bash

   export SKETCHLIB_PATH=/path/to/your/sketchlib


Dependencies
------------

gemsparcl's Python dependencies are installed automatically by ``pip install .``:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Package
     - Version
     - Purpose
   * - click
     - ≥ 8.1
     - Command-line interface framework
   * - rich-click
     - ≥ 1.6
     - Styled, colour-coded CLI output
   * - pandas
     - ≥ 2.0
     - Reading and writing CSV/TSV data
   * - numpy
     - ≥ 1.24
     - Numerical operations (percentile thresholds)
   * - networkx
     - ≥ 3.0
     - Graph construction and community detection
