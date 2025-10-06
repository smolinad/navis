import msgspec
from typing import List, Optional, Union


class DifferentialDriveState(msgspec.Struct, tag="diff_drive"):
    """State specific to a two-wheeled differential drive robot."""
    v: float
    omega: float
    wheel_velocities: List[float]


class SpotState(msgspec.Struct, tag="spot"):
    """State specific to a quadruped robot (Spot)."""
    body_height: float
    is_standing: bool


class MoveCommand(msgspec.Struct):
    """Command to control robot velocities."""
    v: float = 0.0
    omega: float = 0.0


class Register(msgspec.Struct):
    """Robot registration message sent once upon connection."""
    robot_id: str
    robot_type: str


class Measurement(msgspec.Struct):
    """Robot measurement (state) message.

    The robot-specific state can be either DifferentialDriveState or SpotState,
    but not both. If no state has been set yet, this field can be None.
    """
    x: float
    y: float
    theta: float
    state: Optional[Union[DifferentialDriveState, SpotState]] = None
