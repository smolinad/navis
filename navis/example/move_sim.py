"""
Navis Zenoh Robot Controller (Scripted Example)
===============================================

A script that sends a sequence of movement commands to a robot using
the high-level `navis.api.RobotController`.
"""
import time
import navis.api as navis


def scripted_moves(controller: navis.RobotController):
    """
    Executes a predefined sequence of movements using the given controller.

    Args:
        controller: An initialized RobotController instance.
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
    ROBOT_ID = "robot001"

    # Initialize a controller for the specific robot
    controller = navis.RobotController(robot_id=ROBOT_ID)

    try:
        # Run the scripted movement sequence
        scripted_moves(controller)
    except KeyboardInterrupt:
        # Ensure the robot stops if the script is cancelled
        print("\n[CONTROL] Script interrupted by user. Stopping robot.")
        controller.move(linear_vel=0.0, angular_vel=0.0)
    finally:
        # Cleanly close the connection to the Zenoh network
        print("[CONTROL] Shutting down controller.")
        controller.close()
