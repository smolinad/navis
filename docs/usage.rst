Usage
=====

Starting the Server
-------------------

Start the Navis router:

.. code-block:: bash

   uv run navis-router

Creating a Minimal Simulated Robot
---------------------------------

A minimal synchronous robot client using ``DeviceClient`` and implementing ``DeviceInterface``:

.. code-block:: python

   import threading
   import time
   from navis.api import DeviceClient, DeviceInterface
   from navis.messages import Measurement, DifferentialDriveState, Move

   class SimulatedRobot(DeviceInterface):
       """Simulated DifferentialDrive robot implementing DeviceInterface."""

       def __init__(self):
           self.x = self.y = self.theta = 0.0
           self.v = self.omega = 0.0

       def dispatch_command(self, command: Move):
           """Handle incoming Move commands from the client."""
           self.v, self.omega = command.v, command.omega
           print(f"[SIM] Command received: v={self.v}, ω={self.omega}")

       def get_measurement(self) -> Measurement:
           """Return the current robot state as a Measurement object."""
           return Measurement(
               x=self.x,
               y=self.y,
               theta=self.theta,
               state=DifferentialDriveState(v=self.v, omega=self.omega)
           )

   def main():
       # 1. Create the robot logic object
       robot = SimulatedRobot()

       # 2. Create the DeviceClient. The router assigns the client an unique ID
       under the hood.
       client = DeviceClient(device_object=robot)

       # 3. Register a measurement publisher (every 0.1s)
       client.add_publisher(
           topic_suffix="measurement",
           data_provider=robot.get_measurement,
           interval_seconds=0.1
       )

       # 4. Start the client in a separate thread
       thread = threading.Thread(target=client.start)
       thread.start()

       try:
           while True:
               time.sleep(1)
       except KeyboardInterrupt:
           print(f"[{ROBOT_ID}] Shutdown signal received.")
       finally:
           client.close()
           print(f"[{ROBOT_ID}] Client shut down successfully.")

   if __name__ == "__main__":
       main()

Controlling the Robot
---------------------

Send movement commands using ``DeviceController``:

.. code-block:: python

   import time
   from navis.api import DeviceController, list_devices
   from navis.categories import ROBOTS

   # Find the robots connected to the router
   available_robots = navis.list_devices(
        category=ROBOTS,
        timeout_seconds=5
   )

   # Control the first robot from the ``available_robots`` dictionary.
   controller = DeviceController(device_id=available_robots.keys()[0])

   # Move forward for 2 seconds
   controller.move(linear_vel=1.0, angular_vel=0.0)
   time.sleep(2)

   # Stop
   controller.move(linear_vel=0.0, angular_vel=0.0)


Tip
---

Check ``navis/example`` for a more comprehensive example.
