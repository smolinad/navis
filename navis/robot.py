"""Data classes and registry for representing and managing robot state.
"""

from dataclasses import dataclass, field
import asyncio
from typing import List, Optional, Dict
from fastapi import WebSocket
from abc import ABC, abstractmethod

from navis.messages import Measurement, DifferentialDriveState


@dataclass
class BaseRobot(ABC):
    """Abstract base class representing a generic robot.

    This dataclass defines a common interface and shared attributes for all robot
    types managed by the server. It includes basic pose information, server-side
    connection details, and an abstract method for state updates.

    Attributes:
        robot_id (str): The unique identifier for the robot.
        x (float): The robot's x-coordinate in a global frame. Defaults to 0.0.
        y (float): The robot's y-coordinate in a global frame. Defaults to 0.0.
        theta (float): The robot's orientation (angle) in a global frame.
            Defaults to 0.0.
        last_measurement (Optional[Measurement]): The last raw Protobuf
            measurement message received from the robot. Defaults to None.
        ws (Optional[WebSocket]): The active WebSocket connection for this
            robot, if currently connected. Defaults to None.
        lock (asyncio.Lock): An asyncio lock to ensure thread-safe access to
            the robot's attributes, as multiple server tasks might access them.
    """
    robot_id: str

    # Common state for all robot types (e.g., from a localization system)
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

    # Server-side attributes for managing the connection and state
    last_measurement: Optional[Measurement] = None
    ws: Optional[WebSocket] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    @abstractmethod
    def update_from_proto(self, meas: Measurement):
        """Abstract method to update the robot's state from a Protobuf message.

        Args:
            meas (Measurement): The Protobuf message containing new state data.
        """
        self.last_measurement = meas
        self.x = meas.x
        self.y = meas.y
        self.theta = meas.theta


@dataclass
class DifferentialDriveRobot(BaseRobot):
    """Represents a two-wheeled differential drive robot.

    Inherits from `BaseRobot` and adds state and properties specific to a
    differential drive configuration, such as linear and angular velocities.

    Attributes:
        v (float): The robot's forward linear velocity. Defaults to 0.0.
        omega (float): The robot's angular velocity. Defaults to 0.0.
        wheel_velocities (List[float]): The individual velocities of the left
            and right wheels. Defaults to [0.0, 0.0].
        wheel_base (float): The distance between the two wheels. Defaults to 0.15.
        time_step (float): The simulation or control time step. Defaults to 0.1.
    """
    # Attributes specific to this robot type
    v: float = 0.0
    omega: float = 0.0
    wheel_velocities: List[float] = field(default_factory=lambda: [0.0, 0.0])

    # Physical properties
    wheel_base: float = 0.15
    time_step: float = 0.1

    def update_from_proto(self, meas: Measurement):
        """Updates the robot's state from a Protobuf `Measurement` message.

        Args:
            meas (Measurement): The Protobuf message from the robot.
        """
        # Call the parent method to update common fields (x, y, theta)
        super().update_from_proto(meas)

        # Check that the message contains the correct robot-specific state
        if meas.WhichOneof('robot_specific_state') == 'diff_drive_state':
            diff_state: DifferentialDriveState = meas.diff_drive_state

            # Update the specific fields for this robot
            self.v = diff_state.v
            self.omega = diff_state.omega
            self.wheel_velocities = list(diff_state.wheel_velocities)
        else:
            print(f"[WARN] Received a measurement for {
                  self.robot_id} without DifferentialDriveState.")

    def set_velocities(self, v: float, omega: float):
        """Sets target velocities and calculates the required wheel speeds.

        This method applies inverse kinematics to translate a desired body
        velocity (linear `v` and angular `omega`) into the necessary
        velocities for the left and right wheels to achieve that motion.

        Args:
            v (float): The target linear velocity.
            omega (float): The target angular velocity.
        """
        self.v = v
        self.omega = omega

        v_l = self.v - (self.omega * self.wheel_base / 2)
        v_r = self.v + (self.omega * self.wheel_base / 2)
        self.wheel_velocities = [v_l, v_r]


# In-memory Robot registry
robots_registry: Dict[str, BaseRobot] = {}
