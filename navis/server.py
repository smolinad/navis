"""FastAPI server for managing and communicating with robots over WebSockets.
It uses Protobuf for message serialization over the WebSocket connection.
Install `navis` and run navis-server in the command line.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, List, Type
from navis.robot import BaseRobot, DifferentialDriveRobot, robots_registry
from navis.messages import Measurement, MoveCommand, ClientToServer
from google.protobuf.json_format import MessageToDict
from contextlib import asynccontextmanager
import argparse
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[•‿•] NAVIS SERVER RUNNING...")
    print("Awaiting robot connections on the WebSocket...")
    yield
    print("[-.-] NAVIS SERVER SHUTTING DOWN")

app = FastAPI(lifespan=lifespan)

# In-memory storage for move commands for robots that are not currently connected.
command_queues: Dict[str, List[bytes]] = {}

# Maps robot type strings received during registration to their corresponding class.
ROBOT_TYPES: Dict[str, Type[BaseRobot]] = {
    "DifferentialDriveRobot": DifferentialDriveRobot,
}


@app.websocket("/ws/robot/{robot_id}")
async def robot_ws(websocket: WebSocket, robot_id: str):
    """Manages the WebSocket lifecycle for a single robot client.

    This function handles the initial registration of a robot, listens for incoming
    measurement data, and ensures that any queued commands are sent upon connection.
    It also manages graceful disconnection and error handling.

    The communication protocol is as follows:
    1.  Client connects to the WebSocket.
    2.  Client sends a `ClientToServer` Protobuf message containing a `Register` payload.
    3.  Server validates the registration and adds the robot to the registry.
    4.  Client periodically sends `ClientToServer` messages with `Measurement` payloads.
    5.  Server can send `MoveCommand` Protobuf messages to the client at any time.

    Args:
        websocket (WebSocket): The WebSocket connection instance provided by FastAPI.
        robot_id (str): The unique identifier for the robot, passed from the URL path.

    Raises:
        ValueError: If the first message is not a valid registration message,
            if the robot_id in the registration message does not match the URL,
            or if the robot_type is unknown.
    """
    await websocket.accept()
    robot: BaseRobot | None = None

    try:
        # --- REGISTRATION STEP ---
        reg_bytes = await websocket.receive_bytes()
        wrapper_msg = ClientToServer()
        wrapper_msg.ParseFromString(reg_bytes)

        if wrapper_msg.WhichOneof('payload') == 'register':
            reg_msg = wrapper_msg.register
            robot_type_str = reg_msg.robot_type

            if reg_msg.robot_id != robot_id:
                raise ValueError(
                    "Mismatched robot_id in registration message.")

            robot_class = ROBOT_TYPES.get(robot_type_str)
            if not robot_class:
                raise ValueError(f"Unknown robot_type: {robot_type_str}")

            robot = robot_class(robot_id=robot_id)
            robots_registry[robot_id] = robot
            print(f"[REGISTERED] Robot {robot_id} as type {robot_type_str}")
        else:
            raise ValueError("Client must send a registration message first.")

        # --- NORMAL OPERATION ---
        async with robot.lock:
            robot.ws = websocket

        if robot_id in command_queues:
            for cmd_bytes in command_queues[robot_id]:
                await websocket.send_bytes(cmd_bytes)
            command_queues[robot_id] = []

        while True:
            data_bytes = await websocket.receive_bytes()
            wrapper_msg.ParseFromString(data_bytes)

            if wrapper_msg.WhichOneof('payload') == 'measurement':
                measurement = wrapper_msg.measurement
                async with robot.lock:
                    robot.update_from_proto(measurement)
                # print(f"[MEASUREMENT] Robot {robot_id}: x={measurement.x:.3f}\ty={measurement.y:.3f}")
            else:
                print(
                    f"[WARN] Received unexpected message type from {robot_id}")

    except WebSocketDisconnect:
        # This is the expected, graceful way a client disconnects.
        print(f"[DISCONNECT] Robot {robot_id} closed the connection.")
        # No need to call websocket.close() here; it's already done.

    except Exception as e:
        # This handles unexpected errors (e.g., parsing errors, ValueErrors).
        print(f"[ERROR] An unexpected error occurred with {robot_id}: {e}")
        # We can TRY to close gracefully, but it might fail if the socket is dead.
        try:
            await websocket.close(code=1011, reason=str(e))
        except RuntimeError:
            # Ignore the "double-close" error if the socket is already gone.
            pass

    finally:
        # This block will run NO MATTER HOW the try block exits (success, disconnect, or error).
        # It's the safest place to clean up resources.
        print(f"[CLEANUP] Cleaning up resources for {robot_id}.")
        if robot:
            async with robot.lock:
                robot.ws = None


@app.post("/api/move")
async def move_robot(command: dict):
    """Receives a move command and sends it to a specified robot.

    This endpoint accepts a JSON payload to control a robot's movement.
    If the target robot is currently connected via WebSocket, the command is
    sent immediately. If the robot is not connected, the command is queued
    and will be sent the next time it connects.

    Args:
        command (dict): A dictionary containing the command parameters.
            Expected keys: 'robot_id' (str), 'v' (float, optional),
            'omega' (float, optional).

    Returns:
        JSONResponse: A confirmation of the action taken (sent or queued) or an
            error response with an appropriate HTTP status code (400 for bad
            request, 404 for robot not found).
    """
    robot_id = command.get("robot_id")
    if not robot_id:
        return JSONResponse({"error": "robot_id is required"}, status_code=400)

    v = command.get("v", 0.0)
    omega = command.get("omega", 0.0)

    cmd_proto = MoveCommand(v=v, omega=omega)
    cmd_bytes = cmd_proto.SerializeToString()

    robot = robots_registry.get(robot_id)
    if not robot:
        return JSONResponse({"error": f"Robot {robot_id} not registered or found."}, status_code=404)

    async with robot.lock:
        if isinstance(robot, DifferentialDriveRobot):
            robot.set_velocities(v=v, omega=omega)

        if robot.ws:
            try:
                await robot.ws.send_bytes(cmd_bytes)
                # print(f"[CMD SENT] Sent v={v}, omega={omega} to {robot_id}")
            except Exception as e:
                print(f"[WARN] Failed to send to {
                      robot_id}, queuing instead: {e}")
                command_queues.setdefault(robot_id, []).append(cmd_bytes)
        else:
            command_queues.setdefault(robot_id, []).append(cmd_bytes)
            print(f"[CMD QUEUED] Queued v={v}, omega={omega} for {robot_id}")

    return JSONResponse({"status": "ok", "robot_id": robot_id, "v": v, "omega": omega})


@app.get("/api/state/{robot_id}")
async def get_robot_state(robot_id: str):
    """Retrieves the last reported state for a specific robot.

    Queries the in-memory registry for a robot's last known measurement data.
    The data is returned as a JSON object.

    Args:
        robot_id (str): The unique identifier of the robot, from the URL path.

    Returns:
        JSONResponse: A JSON object containing the latest measurement data
            (e.g., position, velocity) converted from its Protobuf format.
            Returns a 404 error if the robot ID is not found in the registry.
    """
    robot = robots_registry.get(robot_id)
    if not robot:
        return JSONResponse({"error": f"Robot {robot_id} not found"}, status_code=404)

    async with robot.lock:
        if robot.last_measurement:
            # Convert the stored Protobuf message to a JSON-friendly dictionary
            data = MessageToDict(robot.last_measurement,
                                 preserving_proto_field_name=True)
        else:
            data = {"message": "No measurement received yet for this robot."}

    return JSONResponse(content=data)


def main():
    """Main function to run the Uvicorn server, callable by the entry point."""
    global DEBUG
    parser = argparse.ArgumentParser(description="Navis Robot Server")
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable detailed logging for measurements and commands."
    )
    args, unknown = parser.parse_known_args()
    if args.debug:
        DEBUG = True

    uvicorn.run("navis.server:app", host="0.0.0.0", port=4321,
                log_level="warning", reload=True)


if __name__ == "__main__":
    main()
