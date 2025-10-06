"""
Navis Robot Controller
===============================================

A script that sends a sequence of movement commands to a robot using
the high-level ``navis.api.DeviceController``.

This script automatically discovers the robot to control. It polls the
network for a few seconds and will only run if it finds exactly one robot.
"""
import sys
import time
import navis
from navis.categories import ROBOTS


def scripted_moves(controller: navis.DeviceController):
    """
    Executes a predefined sequence of movements using the given controller.

    Args:
        controller: An initialized DeviceController instance.
    """
    path = [
        # (v, omega, duration_seconds)
        (3.0, 0.0, 3),   # Forward for 3s
        (0.0, -0.7, 2),  # Turn right for 2s
        (3.0, 0.0, 3),   # Forward for 3s
        (0.0, -0.7, 2),  # Turn right for 2s
        (3.0, 0.0, 6),   # Forward for 6s
        (0.0, -0.7, 2),  # Turn right for 2s
        (3.0, 0.0, 6),   # Forward for 6s
        (0.0, -0.7, 2),  # Turn right for 2s
        (3.0, 0.0, 3),   # Forward for 3s
    ]

    for v, omega, duration in path:
        print(f"[CONTROL] Sending v={v:.1f}, ω={omega:.1f} for {duration}s")
        controller.move(linear_vel=v, angular_vel=omega)
        time.sleep(duration)

    print("[CONTROL] Path finished. Stopping robot.")
    controller.move(linear_vel=0.0, angular_vel=0.0)


if __name__ == "__main__":
    print("[CONTROL] Discovering a single robot (waiting up to 5s)...")

    # The API call is now a single, powerful line. The loop is gone.
    available_robots = navis.list_devices(
        category=ROBOTS,
        timeout_seconds=5
    )

    # Check the results (which is now a dictionary).
    if not available_robots:
        print("[ERROR] No robots of the correct type found. Exiting.")
        sys.exit(1)

    robot_id_to_control = None
    if len(available_robots) >= 1:
        robot_id_to_control = list(available_robots.keys())[0]
        print(f"[CONTROL] Found robot: {robot_id_to_control}")

    # Initialize a controller for the discovered robot.
    controller = None
    if robot_id_to_control:
        controller = navis.DeviceController(device_id=robot_id_to_control)

    try:
        scripted_moves(controller)
    except KeyboardInterrupt:
        print("\n[CONTROL] Script interrupted by user. Stopping robot.")
        controller.move(linear_vel=0.0, angular_vel=0.0)
    finally:
        print("[CONTROL] Shutting down controller.")
        controller.close()
