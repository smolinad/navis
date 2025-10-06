"""
Navis Robot Data Classes 
==========================================

Defines robot types and state using Python dataclasses and msgspec.Struct
for typed, zero-boilerplate serialization with Zenoh.

These classes replace the previous Protobuf-based implementation.
"""

import asyncio
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from navis.messages import Measurement


@dataclass
class BaseRobot(ABC):
    """Abstract base class for a generic robot.

    Attributes:
        robot_id (str): Unique robot identifier.
        x (float): Robot's x position in global frame.
        y (float): Robot's y position in global frame.
        theta (float): Robot orientation (radians).
        lock (asyncio.Lock): Ensures safe concurrent updates.
    """
    robot_id: str
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    @abstractmethod
    async def update_from_message(self, meas: Measurement):
        """Update the robot state from a msgspec message.

        Args:
            meas (Measurement): The decoded measurement message.
        """
        self.x = meas.x
        self.y = meas.y
        self.theta = meas.theta


@dataclass
class DifferentialDriveRobot(BaseRobot):
    """Two-wheeled differential drive robot.

    Attributes:
        v (float): Linear velocity.
        omega (float): Angular velocity.
        wheel_velocities (list[float]): [left_wheel, right_wheel].
        wheel_base (float): Distance between wheels.
    """
    v: float = 0.0
    omega: float = 0.0
    wheel_velocities: list[float] = field(default_factory=lambda: [0.0, 0.0])
    wheel_base: float = 0.15

    async def update_from_message(self, meas: Measurement):
        """Update robot state from msgspec Measurement.

        Args:
            meas (Measurement): The measurement message.
        """
        # Update common pose
        await super().update_from_message(meas)

        # Update differential-drive-specific state
        self.v = getattr(meas, "v", 0.0)
        self.omega = getattr(meas, "omega", 0.0)
        # Compute wheel velocities via inverse kinematics
        v_l = self.v - (self.omega * self.wheel_base / 2)
        v_r = self.v + (self.omega * self.wheel_base / 2)
        self.wheel_velocities = [v_l, v_r]

    def set_velocities(self, v: float, omega: float):
        """Set linear and angular velocities and compute wheel speeds."""
        self.v = v
        self.omega = omega
        v_l = self.v - (self.omega * self.wheel_base / 2)
        v_r = self.v + (self.omega * self.wheel_base / 2)
        self.wheel_velocities = [v_l, v_r]
