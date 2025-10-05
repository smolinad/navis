"""Serializes communication messages into binary `Protobuf` message classes for quick communications.
The `robot_comms.proto` file contains the definition of such classes. 
Makes the `Protobuf` message classes directly importable from the package.

This file imports the specific message classes from the auto-generated
`robot_comms_pb2.py` file. This allows for cleaner imports elsewhere in the
package, for example:
    >>> from navis.messages import Measurement

To regenerate the `robot_comms_pb2.py` file after modifying the `robot_comms.proto`
schema, run the following command from your project's root directory:
    >>> python -m grpc_tools.protoc --python_out=. --pyi_out=. -I. navis/messages/robot_comms.proto
"""

from .robot_comms_pb2 import (
    Measurement,
    MoveCommand,
    DifferentialDriveState,
    ClientToServer,
    Register
)

# This line controls what `from navis.messages import *` would import.
__all__ = [
    "Measurement",
    "MoveCommand",
    "DifferentialDriveState",
    "ClientToServer",
    "Register"
]
