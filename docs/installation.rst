Installation
============

Navis is distributed directly from GitHub and uses ``uv`` to manage dependencies and environments.
Make sure you have both Python (≥3.13) and ``uv`` installed before proceeding.

Requirements and Installation
-----------------------------

============= ==============================================================================
 Requirement   Installation / Documentation                                                                                         
============= ==============================================================================
``uv``        `UV Installation <https://docs.astral.sh/uv/getting-started/installation/>`_                                         
Zenoh Router  `Zenoh Installation <https://zenoh.io/docs/getting-started/installation/>`_                               
============= ==============================================================================

Quick Setup
-----------

.. code-block:: bash

   git clone https://github.com/smolinad/navis.git
   cd navis
   uv sync

This will create a virtual environment and install all dependencies defined in ``pyproject.toml``.

Alternatively, you can install it directly using ``uv``:

.. code-block:: bash

   uv pip install git+https://github.com/smolinad/navis.git

Scripts
-------

Navis installs two helpful CLI scripts for managing experiments:

- ``navis-router`` — starts the navigation router (the central control node)
- ``navis-visualizer`` — runs a live visualizer for connected robots

Both are available after installation.

To confirm the setup, run:

.. code-block:: bash

   uv run navis-router

Troubleshooting
---------------

If you encounter missing dependencies, ensure your environment is managed by uv:

.. code-block:: bash

   uv pip check

Continue to :doc:`usage` to learn how to launch a robot client and start interacting with the server.

