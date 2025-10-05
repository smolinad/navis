"""Simulated robot client for the Navis server.

This script demonstrates the "plug-and-play" nature of the Navis API.
It defines a `SimulatedRobot` class that implements the required interface
(the `get_measurement` and `handle_command` methods), and then passes an
instance of this class to the `navis.RobotConnection` to be run.
"""

import asyncio
import random
import math
import navis

from navis.messages import (
    Measurement,
    MoveCommand,
    DifferentialDriveState,
)


# --- Robot Identity & Server Configuration ---
ROBOT_ID = "robot001"
ROBOT_TYPE = "DifferentialDriveRobot"

# Configure the navis API to connect to the correct server
# Replace "localhost" with your server's IP if needed.
navis.set_server_address("192.168.1.188")


class SimulatedRobot:
    """A class that encapsulates the robot's state and logic.

    This class adheres to the interface required by `navis.RobotConnection`:
    - It has a `get_measurement()` method.
    - It has a `handle_command(cmd)` method.
    """

    def __init__(self):
        self.x, self.y, self.theta = 0.0, 0.0, 0.0
        self.v, self.omega = 0.0, 0.0
        self.wheel_velocities = [0.0, 0.0]
        self.wheel_base = 0.15
        self.time_step = 0.1  # Simulation physics update rate

    def handle_command(self, command: MoveCommand):
        """Handles an incoming command by setting the robot's target velocities."""
        print(f"[SIM] Received Command: v={
              command.v:.2f}, omega={command.omega:.2f}")
        self.v, self.omega = command.v, command.omega
        # Inverse kinematics
        v_l = self.v - (self.omega * self.wheel_base / 2)
        v_r = self.v + (self.omega * self.wheel_base / 2)
        self.wheel_velocities = [v_l, v_r]

    def get_measurement(self) -> Measurement:
        """Updates the pose and returns the new measurement state."""
        # Update pose using forward kinematics
        v_l, v_r = self.wheel_velocities
        v_actual = (v_l + v_r) / 2
        omega_actual = (v_r - v_l) / self.wheel_base
        self.theta += omega_actual * self.time_step
        self.x += v_actual * math.cos(self.theta) * self.time_step
        self.y += v_actual * math.sin(self.theta) * self.time_step

        # Create the Protobuf message with simulated noise
        diff_drive_state = DifferentialDriveState(
            v=self.v, omega=self.omega, wheel_velocities=self.wheel_velocities
        )
        measurement = Measurement(
            x=self.x + random.uniform(-0.01, 0.01),
            y=self.y + random.uniform(-0.01, 0.01),
            theta=self.theta + random.uniform(-0.01, 0.01),
            diff_drive_state=diff_drive_state,
        )
        print(f"[SIM] Sending Measurement: x={
              measurement.x:.3f}, y={measurement.y:.3f}")
        return measurement


async def main():
    """Sets up the robot and runs the connection loop using the Navis API."""
    # 1. Create an instance of your robot logic.
    robot_object = SimulatedRobot()

    # 2. Pass the instance directly to the RobotConnection.
    #    The API will now call the methods on your robot_object.
    connection = navis.RobotConnection(
        robot_id=ROBOT_ID,
        robot_type=ROBOT_TYPE,
        robot_object=robot_object
    )

    # 3. Start the connection. It runs in the background.
    connection.start()

    # Keep the main script alive to allow the background task to run.
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{ROBOT_ID}] Shutting down.")
