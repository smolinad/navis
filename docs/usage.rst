Usage
=====

Once installed, you can start a complete Navis simulation in just a few steps.

Starting the Server
-------------------

First, start the Navis server on your host machine. This handles robot communication
and command dispatch.

.. code-block:: bash

   uv run navis-server

If desired, you can also run the visualizer in a separate terminal:

.. code-block:: bash

   uv run navis-visualizer --robot-id robot001 --host 199.199.1.1 

Creating a Simulated Robot
--------------------------

Robots connect to the Navis server by implementing a simple interface — they just
need two methods: `get_measurement()` and `handle_command(cmd)`.

Here’s a minimal example:

.. code-block:: python

   import asyncio
   import navis
   from navis.messages import Measurement, MoveCommand, DifferentialDriveState

   navis.set_server_address("192.168.1.188")

   class SimulatedRobot:
       def __init__(self):
           self.x, self.y, self.theta = 0.0, 0.0, 0.0

       def handle_command(self, command: MoveCommand):
           print(f"Received: v={command.v:.2f}, ω={command.omega:.2f}")

       def get_measurement(self) -> Measurement:
           return Measurement(x=self.x, y=self.y, theta=self.theta,
                              diff_drive_state=DifferentialDriveState(v=0, omega=0))

   async def main():
       robot = SimulatedRobot()
       conn = navis.RobotConnection(robot_id="robot001",
                                    robot_type="DifferentialDriveRobot",
                                    robot_object=robot)
       conn.start()
       await asyncio.Event().wait()

   if __name__ == "__main__":
       asyncio.run(main())

Controlling the Robot
---------------------

Once the simulated robot is running, you can command it from another script or REPL:

.. code-block:: python

   import time
   import navis

   navis.set_server_address("192.168.1.188")
   ROBOT_ID = "robot001"

   path = [
       (3, 0.0, 3),
       (0.0, -0.7, 2),
       (3, 0.0, 3),
   ]

   for v, omega, duration in path:
       navis.move(ROBOT_ID, linear_vel=v, angular_vel=omega)
       time.sleep(duration)

   navis.move(ROBOT_ID, linear_vel=0.0, angular_vel=0.0)


For more details check out the test example: 
`robot_sim.py <../../navis/tests/robot_sim.py>`_

Tip
---

You can connect multiple robots to the same server — each with its own `robot_id`.
The Navis API will automatically route commands to the correct client.

Next Steps
----------

Explore the :doc:`navis/modules` reference for detailed class and function documentation.

