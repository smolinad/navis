"""
Navis Router
============

Runs the Zenoh router (``zenohd``) and ID service together.

The router handles all message routing between devices and controllers.
The ID service assigns unique UUIDs to connecting devices.

Usage:
    uv run navis-router.py
"""

import subprocess
import sys
import threading
import time
import uuid
import zenoh


class IDService:
    """
    ID Service for Navis devices.

    Assigns unique UUIDs to devices that request them via a Zenoh queryable.

    Attributes:
        session (zenoh.Session | None): The active Zenoh session.
        queryable (zenoh.Queryable | None): The declared Zenoh queryable for ID requests.
    """

    def __init__(self):
        """Initialize the ID service with no active session or queryable."""
        self.session = None
        self.queryable = None

    def start(self):
        """
        Start the ID service.

        Opens a Zenoh session and declares a queryable at
        ``navis/admin/id_service`` that generates and returns a new UUID
        whenever a device queries it.
        """
        print("[ID Service] Starting...")
        self.session = zenoh.open(zenoh.Config())

        def id_handler(query):
            """
            Handle incoming ID requests.

            Generates a new UUID and replies to the query.

            Args:
                query (zenoh.Query): The incoming Zenoh query object.
            """
            new_id = str(uuid.uuid4())
            print(f"[ID Service] Assigned ID: {new_id}")
            query.reply(query.key_expr, new_id.encode())

        self.queryable = self.session.declare_queryable(
            "navis/admin/id_service",
            id_handler
        )
        print("[ID Service]  Ready on ``navis/admin/id_service``\n")

    def stop(self):
        """
        Stop the ID service.

        Closes the Zenoh session if active.
        """
        print("[ID Service] Stopping...")
        if self.session:
            self.session.close()


def run_zenohd():
    """
    Launch the Zenoh router as a subprocess.

    Streams the stdout of ``zenohd`` to the console. Exits the program
    if the ``zenohd`` executable is not found or if an unexpected error occurs.
    """
    print("[Router] Starting ``zenohd``...")
    try:
        process = subprocess.Popen(
            ["zenohd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"[Router] ``zenohd`` started (PID: {process.pid})\n")

        # Stream zenohd output line by line
        for line in process.stdout:
            print(f"[zenohd] {line.rstrip()}")

    except FileNotFoundError:
        print("[Router] ERROR: ``zenohd`` command not found!")
        sys.exit(1)
    except Exception as e:
        print(f"[Router] ERROR: {e}")
        sys.exit(1)


def main():
    """
    Main entry point for the Navis Router.

    Starts the Zenoh router in a background thread, initializes the
    ID service, and keeps the services running until interrupted.
    """
    print("[·_·]Navis Router - Starting...")
    print()

    # Start Zenoh router in a daemon thread
    router_thread = threading.Thread(target=run_zenohd, daemon=True)
    router_thread.start()

    print("[·_·] Waiting for ``zenohd`` to initialize...")
    time.sleep(2)

    # Start ID service
    id_service = IDService()
    id_service.start()

    # Show ready message and running services
    print("Navis Router Ready")
    print("Services running:")
    print("  - Zenoh router (``zenohd``)")
    print("  - ID service (``navis/admin/id_service``)")
    print("\nPress Ctrl+C to stop")
    print()

    try:
        # Keep the program alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        print("\n[·_·] Shutting down...")
        id_service.stop()
        print("[·_·] Stopped")


if __name__ == "__main__":
    main()
