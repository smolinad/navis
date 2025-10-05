import time
import navis


ROBOT_ID = "robot001"


def scripted_moves():
    path = [
        # (v, omega, duration)
        (3, 0.0, 3),   # Forward for 3s
        (0.0, -0.7, 2),  # Turn right (~90 deg) for 1s
        (3, 0.0, 3),
        (0.0, -0.7, 2),
        (3, 0.0, 6),
        (0.0, -0.7, 2),
        (3, 0.0, 6),
        (0.0, -0.7, 2),
        (3, 0.0, 3),
    ]

    for v, omega, duration in path:
        print(f"[CONTROL] Sending command: v={v}, ω={omega} for {duration}s")
        navis.move(ROBOT_ID, linear_vel=v, angular_vel=omega)
        time.sleep(duration/1.0)

    print("[CONTROL] Path finished. Stopping robot.")
    navis.move(ROBOT_ID, linear_vel=0.0, angular_vel=0.0)


if __name__ == "__main__":
    scripted_moves()
