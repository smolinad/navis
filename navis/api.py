"""
Navis API
===========================

High-level Python interface for interacting with robots using Zenoh.

This module provides two main functionalities:

1.  A ``RobotClient`` class for a robot or simulator to connect to the
    network, publish its state, and receive commands.

2.  A ``RobotController`` class for external scripts to connect to the
    network and send commands to a specific robot.
"""

import threading
import time
import msgspec
import zenoh
from zenoh import Config
from navis.messages import Measurement, MoveCommand, Register

class RobotClient:
    """High-level synchronous client for a robot to connect to the network."""

    def __init__(self, robot_id: str, robot_type: str, robot_object: object, publish_interval: float = 0.1):
        """Initializes the RobotClient.

        Args:
            robot_id: Unique robot identifier.
            robot_type: Robot type string, e.g., 'DifferentialDriveRobot'.
            robot_object: An object that implements `get_measurement()` and
                          `handle_command(cmd)`.
            publish_interval: How often to send measurements (seconds).
        """
        if not all(hasattr(robot_object, attr) for attr in ["get_measurement", "handle_command"]):
            raise TypeError(
                "robot_object must implement get_measurement() and handle_command()")

        self.robot_id = robot_id
        self.robot_type = robot_type
        self.robot = robot_object
        self.publish_interval = publish_interval
        self.session = zenoh.open(Config())
        self.encoder = msgspec.msgpack.Encoder()
        self.decoder = msgspec.msgpack.Decoder(MoveCommand)
        self._running = threading.Event()
        self._thread = None

    def _publish_loop(self):
        reg_key = f"navis/robots/{self.robot_id}/register"
        meas_key = f"navis/robots/{self.robot_id}/measurement"
        reg_msg = Register(robot_id=self.robot_id, robot_type=self.robot_type)

        print(f"[{self.robot_id}] Publishing registration.")
        self.session.put(reg_key, self.encoder.encode(reg_msg))

        while not self._running.is_set():
            meas = self.robot.get_measurement()
            self.session.put(meas_key, self.encoder.encode(meas))
            time.sleep(self.publish_interval)

    def _command_callback(self, sample):
        try:
            cmd = self.decoder.decode(bytes(sample.payload))
            self.robot.handle_command(cmd)
        except Exception as e:
            print(f"[{self.robot_id}] Failed to decode command: {e}")

    def start(self):
        """Starts the client's publishing and subscribing loops."""
        if self._thread is not None and self._thread.is_alive():
            return
        print(f"[{self.robot_id}] Starting client...")
        self._running.clear()
        self.session.declare_subscriber(
            f"navis/robots/{self.robot_id}/command", self._command_callback)
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def close(self):
        """Stops the client and closes the Zenoh session."""
        print(f"[{self.robot_id}] Closing client...")
        self._running.set()
        if self._thread:
            self._thread.join()
        self.session.close()

class RobotController:
    """A client for sending movement commands to a specific robot."""

    def __init__(self, robot_id: str):
        """Initializes the RobotController for a specific robot.

        Args:
            robot_id: The unique identifier of the robot to control.
        """
        self.robot_id = robot_id
        self.session = zenoh.open(Config())
        self.encoder = msgspec.msgpack.Encoder()
        print(f"[Navis API] Controller for robot '{
              self.robot_id}' initialized.")

    def move(self, linear_vel: float = 0.0, angular_vel: float = 0.0):
        """Sends a movement command to the controlled robot.

        Args:
            linear_vel: The target linear velocity (v).
            angular_vel: The target angular velocity (omega).
        """
        key = f"navis/robots/{self.robot_id}/command"
        cmd = MoveCommand(v=linear_vel, omega=angular_vel)
        self.session.put(key, self.encoder.encode(cmd))

    def close(self):
        """Closes the Zenoh session.

        It's important to call this method when the controller is no longer
        needed to ensure a clean disconnection.
        """
        self.session.close()
        print(f"[Navis API] Controller for robot '{self.robot_id}' closed.")
