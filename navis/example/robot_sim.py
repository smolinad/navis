"""
Navis Zenoh Simulated Robot Client (Synchronous)
================================================

Simulates a DifferentialDrive robot and publishes its state to a Navis Zenoh server.
Measurements are automatically sent, and incoming MoveCommands are handled.

- Logs x and y coordinates of each measurement.
- Fully synchronous; no asyncio required.
"""

import math
import random
import threading
import time

from navis.api import RobotClient
from navis.messages import DifferentialDriveState, Measurement, MoveCommand

# --- Robot Identity ---
ROBOT_ID = "robot001"
ROBOT_TYPE = "DifferentialDriveRobot"


class SimulatedRobot:
    """Simulates the state and physics of a differential drive robot.

    This class holds the robot's pose (x, y, theta), current velocities,
    and physical parameters. It provides methods to update its state based on
    incoming commands and to generate simulated sensor measurements.
    """

    def __init__(self):
        self.x, self.y, self.theta = 0.0, 0.0, 0.0
        self.v, self.omega = 0.0, 0.0
        self.wheel_velocities = [0.0, 0.0]
        self.wheel_base = 0.15
        self.time_step = 0.1  # seconds

    def handle_command(self, command: MoveCommand):
        """Updates the robot's target velocities based on a command.

        Args:
            command: A `MoveCommand` message containing the target linear (v)
                and angular (omega) velocities.
        """
        print(f"[SIM] Received Command: v={
              command.v:.2f}, omega={command.omega:.2f}")
        self.v, self.omega = command.v, command.omega
        v_l = self.v - (self.omega * self.wheel_base / 2)
        v_r = self.v + (self.omega * self.wheel_base / 2)
        self.wheel_velocities = [v_l, v_r]

    def get_measurement(self) -> Measurement:
        """Updates the robot's pose and generates a new measurement.

        This method simulates one time step of movement based on the current
        velocities, updates the robot's internal pose, and returns a
        `Measurement` message with slight random noise added.

        Returns:
            A `Measurement` message containing the new simulated pose and state.
        """
        v_l, v_r = self.wheel_velocities
        v_actual = (v_l + v_r) / 2
        omega_actual = (v_r - v_l) / self.wheel_base

        # Update pose
        self.theta += omega_actual * self.time_step
        self.x += v_actual * math.cos(self.theta) * self.time_step
        self.y += v_actual * math.sin(self.theta) * self.time_step

        # Build state
        diff_drive_state = DifferentialDriveState(
            v=self.v,
            omega=self.omega,
            wheel_velocities=self.wheel_velocities
        )

        measurement = Measurement(
            x=self.x + random.uniform(-0.01, 0.01),
            y=self.y + random.uniform(-0.01, 0.01),
            theta=self.theta + random.uniform(-0.01, 0.01),
            state=diff_drive_state
        )

        print(f"[SIM] Measurement: x={
              measurement.x:.3f}\ty={measurement.y:.3f}")

        return measurement


def main():
    """Initializes and runs the simulated robot client."""
    robot_object = SimulatedRobot()

    client = RobotClient(
        robot_id=ROBOT_ID,
        robot_type=ROBOT_TYPE,
        robot_object=robot_object
    )

    # Run the blocking client.start() method in a separate thread
    client_thread = threading.Thread(target=client.start)
    client_thread.start()

    print(f"[{ROBOT_ID}] Client is running. Press Ctrl+C to exit.")

    try:
        # The main thread will wait here until a KeyboardInterrupt is received.
        client_thread.join()
    except KeyboardInterrupt:
        print(f"\n[{ROBOT_ID}] Shutdown signal received. Closing client...")
        client.close()
        client_thread.join()

    print(f"[{ROBOT_ID}] Client shut down successfully.")


if __name__ == "__main__":
    main()
