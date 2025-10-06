"""
Navis Multi-Robot Visualizer
==================================

Visualizes the live state of all robots in the arena using Zenoh Pub/Sub.
Discovers and displays robots automatically by listening to wildcard topics.
"""

import argparse
import math
import threading
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import msgspec
import zenoh
from zenoh import Config

from navis.messages import Measurement  # Assuming this is accessible

# --- Global State Management ---
# A thread-safe dictionary to store the latest state of each robot.
# Format: { "robot_id": {"x": float, "y": float, "theta": float}, ... }
ROBOT_STATES = defaultdict(dict)
STATE_LOCK = threading.Lock()

# Decoder for incoming measurement messages
DECODER = msgspec.msgpack.Decoder(Measurement)


def measurement_listener(sample):
    """
    Callback to update the shared state when a new measurement arrives.
    This function is called by the Zenoh subscriber thread.
    """
    try:
        # Extract robot_id from the topic key (e.g., "navis/robots/robot001/measurement")
        robot_id = str(sample.key_expr).split("/")[2]
        meas = DECODER.decode(bytes(sample.payload))

        with STATE_LOCK:
            ROBOT_STATES[robot_id] = {
                "x": meas.x,
                "y": meas.y,
                "theta": meas.theta
            }

        # Log for debugging
        print(f"[VISUALIZER] Updated {robot_id}: x={
              meas.x:.2f}, y={meas.y:.2f}")

    except Exception as e:
        print(f"[ERROR] Failed to process measurement on '{
              sample.key_expr}': {e}")


def main():
    """
    Parses command-line arguments, initializes Zenoh, and runs the visualizer.
    """
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Navis Zenoh Multi-Robot Visualizer")
    parser.add_argument(
        "--dims", type=int, default=30,
        help="Plot dimensions in meters (from -dims to +dims)")
    args = parser.parse_args()
    dims = args.dims

    # --- Zenoh Setup ---
    session = zenoh.open(Config())
    # Subscribe to all robot measurement topics
    sub = session.declare_subscriber(
        "navis/robots/*/measurement", measurement_listener)
    print("[VISUALIZER] Listening for robot measurements...")
    print(f"[VISUALIZER] Arena dimensions set to: (-{dims}m, +{dims}m)")

    # --- Matplotlib Setup ---
    fig, ax = plt.subplots(figsize=(10, 10))
    heading_arrow_length = dims * 0.05  # Scale arrow size to plot dims

    def update(frame):
        """Animation function that redraws all robots from the latest state."""
        with STATE_LOCK:
            states_copy = {rid: state.copy()
                           for rid, state in ROBOT_STATES.items()}

        ax.clear()

        # Set plot properties (must be done each frame after clearing)
        ax.set_xlim(-dims, dims)
        ax.set_ylim(-dims, dims)
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.set_title("Live Robot Visualization")
        ax.grid(True)
        ax.set_aspect('equal', adjustable='box')

        if not states_copy:
            ax.text(0.5, 0.5, "Waiting for robot data...",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes)
            return

        # Iterate through the copied states and draw each robot
        for robot_id, state in states_copy.items():
            x, y, theta = state["x"], state["y"], state["theta"]
            robot_plot = ax.plot(x, y, "o", markersize=12, label=robot_id)
            color = robot_plot[0].get_color()
            heading_x = x + heading_arrow_length * math.cos(theta)
            heading_y = y + heading_arrow_length * math.sin(theta)
            ax.plot([x, heading_x], [y, heading_y],
                    "-", linewidth=3, color=color)

        ax.legend(loc="upper right")

    # Create and run the animation
    _ = animation.FuncAnimation(fig, update, interval=100)

    try:
        plt.show()  # This is a blocking call
    finally:
        # Clean up Zenoh session when the plot window is closed
        print("\n[VISUALIZER] Plot window closed, shutting down.")
        session.close()


if __name__ == "__main__":
    main()
