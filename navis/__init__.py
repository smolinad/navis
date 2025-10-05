"""Navis API

This package provides a high-level Python interface for controlling and
monitoring robots connected to the Navis server.

To get started, configure the server address:
    >>> import navis
    >>> navis.set_server_address("your_server_ip")

Then, use the API functions to interact with your robots:
    >>> state = navis.get_state("robot_001")
    >>> navis.move("robot_001", linear_vel=0.5)
"""

# Promote the core API functions and classes to the top-level namespace.
from .api import (
    set_server_address,
    get_rest_api_uri,
    get_websocket_uri,
    get_state,
    move,
    RobotConnection,
    ServerAddress
)

# Promote the base robot classes for users who want to create their own robots.
from .robot import (
    BaseRobot,
    DifferentialDriveRobot
)

# Make the messages sub-package directly accessible.
from . import messages

# Define the public API for `from navis import *`
__all__ = [
    # From api.py
    "set_server_address",
    "get_rest_api_uri",
    "get_websocket_uri",
    "get_state",
    "move",
    "RobotConnection",
    "ServerAddress",

    # From robot.py
    "BaseRobot",
    "DifferentialDriveRobot",

    # Sub-package
    "messages"
]
