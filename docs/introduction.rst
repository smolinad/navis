
Introduction
============

**Navis** is a minimal, plug-and-play navigation stack for Python robotics experiments.

It provides a simple, consistent API for running navigation servers and robot clients under the same LAN,
with automatic discovery supported through ``Zenoh``,
allowing users to quickly connect simulated (or later, physical) robots to a centralized
controller.

Key Features
------------

- 🚀 **Plug-and-Play Architecture** — connect any robot object implementing a simple interface.
- 🌐 **Router Model** — robots communicate with a central `navis-server` over the network.
- 🔧 **Extensible API** — designed to be clear, composable, and easy to extend.
- 🧩 **Visualization Tools** — includes a built-in visualizer for real-time state monitoring.

Example Workflow
----------------

1. Start the Navis server on your host machine.
2. Run a robot client that connects automatically.
3. Send control commands or visualize motion — all through the same Python API.

For example:

.. code-block:: bash

    # Start the Navis server on host machine
    uv run navis-server

    # (Optional) Launch the visualizer on client machine
    uv run navis-visualizer --dims 30

Then, if ``robot001`` is already connected to the server, you can control it in Python through the API: 

.. code-block:: python

    import navis
    import time

    # Initialize a controller for a specific robot
    controller = navis.api.RobotController("robot001")

    # Send a command
    controller.move(linear_vel=1.0, angular_vel=0.0)
    time.sleep(2)
    controller.move(linear_vel=0.0, angular_vel=0.0)

Next Steps
----------

Continue with the :doc:`installation` guide to get Navis set up locally.
