"""Command-line script for real-time robot visualization.

This script uses the Navis API to fetch a robot's state and displays it
using Matplotlib. It is designed to be run from the command line after the
'navis' package is installed.

Example Usage:
    - Visualize `robot_001` connecting to the server at localhost:8000
    >>> navis-visualizer --robot-id robot_001

    - Visualize a different robot on a remote server
    >>> navis-visualizer --robot-id robot_002 --host 192.168.1.100 --port 9999
"""

import threading
import time
import math
import argparse
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from navis.api import get_state, set_server_address

LATEST_ROBOT_STATE = {}
state_lock = threading.Lock()


def state_fetcher_loop(robot_id: str, interval_s: float):
    """Continuously fetches state in a background thread."""
    while True:
        state = get_state(robot_id)
        with state_lock:
            global LATEST_ROBOT_STATE
            LATEST_ROBOT_STATE = state
        time.sleep(interval_s)


def main():
    """Parses arguments, sets up the plot, and runs the animation."""
    parser = argparse.ArgumentParser(description="Navis Robot Visualizer")
    parser.add_argument(
        "--robot-id",
        type=str,
        required=True,
        help="The unique ID of the robot to visualize."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host address of the Navis server."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4321,
        help="Port of the Navis server."
    )
    parser.add_argument(
        "--dims",
        type=int,
        default=30,
        help="Dimensions of the plot, so --dims 30 will span from (-30, -30) to (30, 30)"
    )
    args = parser.parse_args()

    # Configure the API to point to the correct server
    set_server_address(args.host, args.port)

    # --- Matplotlib Setup ---
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-args.dims, args.dims)
    ax.set_ylim(-args.dims, args.dims)
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_title(f"Live Visualization: {args.robot_id}")
    ax.grid(True)
    ax.set_aspect('equal', adjustable='box')

    (robot_body,) = ax.plot([], [], "o", markersize=10, label=args.robot_id)
    (robot_heading,) = ax.plot([], [], "-",
                               linewidth=2, color=robot_body.get_color())
    heading_arrow_length = 0.15
    ax.legend()

    def update(frame):
        """Animation function that reads shared state and draws."""
        with state_lock:
            current_state = LATEST_ROBOT_STATE.copy()

        if "x" in current_state and "y" in current_state and "theta" in current_state:
            x, y, theta = current_state["x"], current_state["y"], current_state["theta"]
            robot_body.set_data([x], [y])
            heading_x = x + heading_arrow_length * math.cos(theta)
            heading_y = y + heading_arrow_length * math.sin(theta)
            robot_heading.set_data([x, heading_x], [y, heading_y])

        return robot_body, robot_heading

    # Start the background thread to fetch data
    fetcher_thread = threading.Thread(
        target=state_fetcher_loop,
        args=(args.robot_id, 0.1),  # Fetch state at 10 Hz
        daemon=True
    )
    fetcher_thread.start()

    # Create and show the animation
    _ = animation.FuncAnimation(
        fig, update, interval=100, blit=True, cache_frame_data=False)

    try:
        plt.show()
    except KeyboardInterrupt:
        print("\n[VISUALIZER] Plot closed via keyboard interrupt. Shutting down.")


if __name__ == "__main__":
    main()
