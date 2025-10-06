import msgspec
from typing import List


class DifferentialDriveState(msgspec.Struct, tag="diff_drive"):
    """State specific to a two-wheeled differential drive robot."""
    v: float
    omega: float
    wheel_velocities: List[float]


class SpotState(msgspec.Struct, tag="spot"):
    """State specific to a quadruped robot (Spot)."""
    body_height: float
    is_standing: bool


RobotStateTypes = (DifferentialDriveState, SpotState)


class Measurement(msgspec.Struct):
    """Robot measurement (state) message.

    The `state` field can be any robot-specific state type defined above.
    """
    x: float
    y: float
    theta: float
    state: object = None  # will decode dynamically using RobotStateTypes


class Move(msgspec.Struct):
    """Command to control robot velocities."""
    v: float = 0.0
    omega: float = 0.0


class SetGripperCommand(msgspec.Struct):
    """Command to control a gripper."""
    position: float = 0.0


class PanTiltCommand(msgspec.Struct):
    """Command to control a pan/tilt unit."""
    pan: float = 0.0
    tilt: float = 0.0


class Register(msgspec.Struct):
    """Robot registration message sent once upon connection."""
    robot_id: str
