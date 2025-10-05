Introduction
============

**Navis** is a minimal, plug-and-play navigation stack for Python robotics experiments.

It provides a simple, consistent API for running navigation servers and robot clients,
allowing users to quickly connect simulated (or later, physical) robots to a centralized
controller.


Key Features
------------

- 🚀 **Plug-and-Play Architecture** — connect any robot object implementing a simple interface.
- 🌐 **Client–Server Model** — robots communicate with a central `navis-server` over the network.
- 🔧 **Extensible API** — designed to be clear, composable, and easy to extend.
- 🧩 **Visualization Tools** — includes a built-in visualizer for real-time state monitoring.

Example Workflow
----------------

1. Start the Navis server on your host machine.
2. Run a robot client that connects automatically.
3. Send control commands or visualize motion — all through the same Python API.

For example:

.. code-block:: bash

   # Start the Navis server on the host machine
   uv run navis-server

   # (Optional) Launch the visualizer on the client machine
   uv run navis-visualizer --robot-id robot001 --host 199.199.1.1 

Then, in Python:

.. code-block:: python

   import navis

   navis.set_server_address("192.168.1.188")
   navis.move("robot001", linear_vel=1.0, angular_vel=0.0)

Next Steps
----------

Continue with the :doc:`installation` guide to get Navis set up locally.

