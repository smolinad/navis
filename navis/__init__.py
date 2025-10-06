"""
This package provides a high-level Python interface for controlling and
monitoring robots connected to the Navis server.

To get started, use the API classes  to interact with your robots:

.. code-block:: python

    import navis.api
    import time

    # Initialize a controller for a specific robot
    controller = navis.api.RobotController("robot001")

    # Send a command
    controller.move(linear_vel=1.0, angular_vel=0.0)
    time.sleep(2)
    controller.move(linear_vel=0.0, angular_vel=0.0)

"""

# Promote the core API functions and classes to the top-level namespace.
from .api import (
    RobotClient,
    RobotController
)

# Promote the base robot classes for users who want to create their own robots.
from .robot import (
    BaseRobot,
    DifferentialDriveRobot
)

# Make the messages sub-package directly accessible.
from .messages import (
    Measurement,
    MoveCommand,
    Register,
    DifferentialDriveState,
    SpotState
)

# Define the public API for `from navis import *`
__all__ = [
    # From api.py
    "RobotClient",
    "RobotController",

    # From robot.py
    "BaseRobot",
    "DifferentialDriveRobot",

    # Sub-package
    "messages"
]
