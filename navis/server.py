"""
Navis Zenoh Server
==================

A Zenoh-based server for Navis robots.
- Subscribes to robot registrations ("navis/robots/*/register").
- Subscribes to robot measurements ("navis/robots/*/measurement").
- Can publish MoveCommands to robots.
"""
import time
import traceback
from navis.messages import *
from typing import List
import msgspec
import zenoh
from zenoh import Config


class NavisServer:
    """Zenoh server for Navis robots."""

    def __init__(self):
        """Initializes the Zenoh session and message encoders/decoders."""
        # Open a Zenoh session
        self.session = zenoh.open(Config())

        # Encoders/Decoders for msgspec
        self.encoder = msgspec.msgpack.Encoder()
        self.measurement_decoder = msgspec.msgpack.Decoder(Measurement)
        self.register_decoder = msgspec.msgpack.Decoder(Register)

    def start(self):
        """Declares the Zenoh subscribers and starts listening."""
        self.session.declare_subscriber(
            "navis/robots/*/register", self._on_register)
        self.session.declare_subscriber(
            "navis/robots/*/measurement", self._on_measurement)
        print("[NAVIS SERVER] Server started, listening to Zenoh topics.")

    def _on_register(self, sample):
        """Callback for handling incoming registration messages."""
        try:
            # Convert the Zenoh payload to standard bytes before decoding
            reg = self.register_decoder.decode(bytes(sample.payload))
            print(f"[REGISTERED] Robot {
                  reg.robot_id} (Type: {reg.robot_type})")
        except Exception:
            print(f"[ERROR] An exception occurred in _on_register for key '{
                  sample.key_expr}':")
            traceback.print_exc()

    def _on_measurement(self, sample):
        """Callback for handling incoming measurement messages."""
        try:
            # It's good practice to only process data samples (PUT)
            if sample.kind != zenoh.SampleKind.PUT:
                return

            # 1. Get the robot ID from the key expression string
            key_str = str(sample.key_expr)
            robot_id = key_str.split("/")[2]

            # 2. Convert the Zenoh payload to standard bytes before decoding
            meas = self.measurement_decoder.decode(bytes(sample.payload))

            # 3. Print the formatted result
            print(f"[MEASUREMENT] {robot_id}: x={meas.x:.3f}\ty={
                  meas.y:.3f}\ttheta={meas.theta:.3f}")

        except Exception:
            print(f"[ERROR] An exception occurred in _on_measurement for key '{
                  sample.key_expr}':")
            traceback.print_exc()

    def move_robot(self, robot_id: str, linear_vel: float = 0.0, angular_vel: float = 0.0):
        """Publishes a MoveCommand to a specific robot."""
        cmd = MoveCommand(v=linear_vel, omega=angular_vel)
        key = f"navis/robots/{robot_id}/command"
        self.session.put(key, self.encoder.encode(cmd))
        print(f"[COMMAND] Sent to {robot_id}: v={
              linear_vel}, omega={angular_vel}")

    def close(self):
        """Closes the Zenoh session."""
        self.session.close()


def main():
    """Main function to instantiate and run the server."""
    server = NavisServer()
    server.start()

    try:
        # Keep the main thread alive to let the Zenoh subscribers work
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[NAVIS SERVER] Shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
