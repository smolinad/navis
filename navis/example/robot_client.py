"""
Navis Simulated Device Client
=================================================

This script simulates a DifferentialDrive robot and connects it to the Navis
framework using the API.

- Implements the DeviceInterface abstract base class
- Gets a unique ID automatically from the router's ID service
- Uses the generic publisher API to send measurement data
- Handles incoming commands via the dispatch_command method

Usage:
    uv run python navis/examples/simulated_robot.py

Prerequisites:
    - ``navis-server`` must be running (provides zenohd + ID service)
"""

import math
import random
import time

from navis.api import DeviceClient, DeviceInterface
from navis.messages import Move, Measurement, DifferentialDriveState


class SimulatedRobot(DeviceInterface):
    """
    A simulation of a robot that implements the DeviceInterface contract.

    Contains the robot's internal state (pose, velocity) and the
    logic for its physics and command handling.
    """

    def __init__(self):
        self.x, self.y, self.theta = 0.0, 0.0, 0.0
        self.v, self.omega = 0.0, 0.0
        self.wheel_velocities = [0.0, 0.0]
        self.wheel_base = 0.15
        self.time_step = 0.1  # seconds

    def dispatch_command(self, command):
        """Handles incoming commands from the client."""
        if isinstance(command, Move):
            print(f"[SIM] Received Move: v={
                  command.v:.2f}, omega={command.omega:.2f}")
            self.v, self.omega = command.v, command.omega
            v_l = self.v - (self.omega * self.wheel_base / 2)
            v_r = self.v + (self.omega * self.wheel_base / 2)
            self.wheel_velocities = [v_l, v_r]
        else:
            print(f"[SIM] Ignoring unknown command type: {
                  type(command).__name__}")

    def get_measurement(self) -> Measurement:
        """
        Updates the robot's pose and generates a new measurement.
        This method will be used as a data provider for a publisher task.
        """
        v_l, v_r = self.wheel_velocities
        v_actual = (v_l + v_r) / 2
        omega_actual = (v_r - v_l) / self.wheel_base

        self.theta += omega_actual * self.time_step
        self.x += v_actual * math.cos(self.theta) * self.time_step
        self.y += v_actual * math.sin(self.theta) * self.time_step

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
    """Initializes and runs the simulated device client."""
    client = None
    try:
        # 1. Create the object that contains the device's logic.
        device_logic = SimulatedRobot()

        # 2. Pass the logic object to the generic DeviceClient.
        # Additional messages can be provided if user defines custom msgspec.Struct types
        client = DeviceClient(
            device_object=device_logic,
            additional_messages=[]
        )

        # 3. Register a publisher for the measurement data.
        client.add_publisher(
            topic_suffix="measurement",
            data_provider=device_logic.get_measurement,
            interval_seconds=0.1
        )

        # 4. Start the client's background threads.
        client.start()

        print(f"[{client.device_id}] Client is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

    except RuntimeError as e:
        print(f"[ERROR] Failed to start client: {e}")
        print("\n  Make sure server is running!")
    except KeyboardInterrupt:
        if client:
            print(f"\n[{client.device_id}] Shutdown signal received.")
    finally:
        if client:
            print(f"[{client.device_id}] Closing client...")
            client.close()
            print(f"[{client.device_id}] Client shut down successfully.")


if __name__ == "__main__":
    main()
