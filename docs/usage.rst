Usage
=====

Starting the Server
-------------------

Start the Navis server:

.. code-block:: bash

   uv run navis-server

Creating a Minimal Simulated Robot
---------------------------------

A minimal synchronous robot client using ``RobotClient``:

.. code-block:: python

   import threading
   from navis.api import RobotClient
   from navis.messages import Measurement, DifferentialDriveState, MoveCommand

   ROBOT_ID = "robot001"

   class SimulatedRobot:
       def __init__(self):
           self.x = self.y = self.theta = 0.0
           self.v = self.omega = 0.0

       def handle_command(self, command: MoveCommand):
           self.v, self.omega = command.v, command.omega
           print(f"Command received: v={self.v}, ω={self.omega}")

       def get_measurement(self) -> Measurement:
           return Measurement(
               x=self.x,
               y=self.y,
               theta=self.theta,
               state=DifferentialDriveState(v=self.v, omega=self.omega)
           )

   def main():
       robot = SimulatedRobot()
       client = RobotClient(
           robot_id=ROBOT_ID,
           robot_type="DifferentialDriveRobot",
           robot_object=robot
       )

       thread = threading.Thread(target=client.start)
       thread.start()
       print(f"[{ROBOT_ID}] Client running. Ctrl+C to exit.")
       thread.join()

   if __name__ == "__main__":
       main()

Controlling the Robot
---------------------

Send movement commands using ``RobotController``:

.. code-block:: python

   import time
   from navis.api import RobotController

   controller = RobotController(robot_id="robot001")
   controller.move(linear_vel=1.0, angular_vel=0.0)
   time.sleep(2)
   controller.move(linear_vel=0.0, angular_vel=0.0)

