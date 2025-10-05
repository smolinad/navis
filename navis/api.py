"""Navis API Client for interacting with the robot control server.

This module provides a simple, high-level Python interface for controlling
and monitoring robots connected to the Navis server. It handles HTTP requests
for sending commands and fetching state, and includes a real-time visualization
tool and a "plug-and-play" real-time connection manager.
"""

import requests
import math
import threading
import time
import asyncio
import websockets
from dataclasses import dataclass
from urllib.parse import quote
from typing import Callable, Awaitable
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from navis.messages import MoveCommand, ClientToServer, Register, Measurement


@dataclass
class ServerAddress:
    """A dataclass to hold server connection details."""
    host: str = "localhost"
    port: int = 4321


# Module-level configuration object, initialized with defaults.
_server_config = ServerAddress()


def set_server_address(host: str, port: int = 4321):
    """Programmatically sets the server address for all subsequent API calls."""
    global _server_config
    _server_config.host = host
    _server_config.port = port
    print(f"[NAVIS API] Server address set to: {
          _server_config.host}:{_server_config.port}")


def get_rest_api_uri() -> str:
    """Constructs the base URI for the REST API."""
    return f"http://{_server_config.host}:{_server_config.port}/api"


def get_websocket_uri(robot_id: str) -> str:
    """Constructs the full WebSocket URI for a specific robot."""
    safe_robot_id = quote(robot_id)
    return f"ws://{_server_config.host}:{_server_config.port}/ws/robot/{safe_robot_id}"


class RobotConnection:
    """Manages a persistent real-time connection to a robot on the server.

    This class provides a "plug-and-play" interface. You provide an object
    that represents your robot's logic, and this class handles the WebSocket
    connection, registration, sending state updates, and receiving commands
    in the background.

    The provided `robot_object` must have two methods:
    - `get_measurement()`: Must return a Protobuf `Measurement` object.
    - `handle_command(cmd)`: Will be called with a Protobuf `MoveCommand` object.

    Args:
        robot_id (str): The unique ID of the robot.
        robot_type (str): The type string (e.g., "DifferentialDriveRobot").
        robot_object (object): An instance of your robot's logic class.
    """

    def __init__(self, robot_id: str, robot_type: str, robot_object: object):
        if not all([MoveCommand, ClientToServer, Register]):
            raise ImportError(
                "Protobuf messages not loaded. Cannot create RobotConnection.")

        if not hasattr(robot_object, 'get_measurement') or not callable(getattr(robot_object, 'get_measurement')):
            raise TypeError(
                "The robot object must have a 'get_measurement' method.")
        if not hasattr(robot_object, 'handle_command') or not callable(getattr(robot_object, 'handle_command')):
            raise TypeError(
                "The robot object must have a 'handle_command' method.")

        self.robot_id = robot_id
        self.robot_type = robot_type
        self.robot = robot_object
        self._task = None

    async def _listen_for_commands(self, ws):
        try:
            async for message_bytes in ws:
                cmd = MoveCommand()
                cmd.ParseFromString(message_bytes)
                # Run the synchronous robot handler in a separate thread to avoid blocking the event loop
                await asyncio.to_thread(self.robot.handle_command, cmd)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def _send_updates(self, ws):
        register_msg = Register(robot_id=self.robot_id,
                                robot_type=self.robot_type)
        wrapper = ClientToServer(register=register_msg)
        await ws.send(wrapper.SerializeToString())
        print(f"[NAVIS CLIENT] Sent registration as type '{self.robot_type}'")
        while True:
            try:
                # Run the synchronous get_measurement method in a thread
                measurement = await asyncio.to_thread(self.robot.get_measurement)
                wrapper = ClientToServer(measurement=measurement)
                await ws.send(wrapper.SerializeToString())
                await asyncio.sleep(0.1)  # Send at 10 Hz
            except websockets.exceptions.ConnectionClosed:
                print("[NAVIS CLIENT] Connection closed, stopping updates.")
                break

    async def _main_loop(self):
        uri = get_websocket_uri(self.robot_id)
        while True:
            try:
                print(f"[NAVIS CLIENT] Attempting to connect to {uri}...")
                async with websockets.connect(uri) as ws:
                    print("[NAVIS CLIENT] Connection successful.")
                    listener_task = asyncio.create_task(
                        self._listen_for_commands(ws))
                    sender_task = asyncio.create_task(self._send_updates(ws))
                    await asyncio.gather(listener_task, sender_task)
            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError):
                print("[NAVIS CLIENT] Connection lost. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[NAVIS CLIENT] An unexpected error occurred: {
                      e}. Reconnecting...")
                await asyncio.sleep(5)

    def start(self):
        """Starts the robot connection loop in the background."""
        if self._task is None:
            self._task = asyncio.create_task(self._main_loop())
            print(f"[NAVIS CLIENT] Connection task for {
                  self.robot_id} started.")

    def stop(self):
        """Stops the robot connection loop."""
        if self._task:
            self._task.cancel()
            self._task = None
            print(f"[NAVIS CLIENT] Connection task for {
                  self.robot_id} stopped.")


def get_state(robot_id: str) -> dict:
    base_url = get_rest_api_uri()
    safe_robot_id = quote(robot_id)
    try:
        resp = requests.get(f"{base_url}/state/{safe_robot_id}", timeout=1.0)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {}


def move(robot_id: str, linear_vel: float = 0.0, angular_vel: float = 0.0):
    base_url = get_rest_api_uri()
    payload = {"robot_id": robot_id, "v": linear_vel, "omega": angular_vel}
    try:
        requests.post(f"{base_url}/move", json=payload,
                      timeout=1.0).raise_for_status()
    except requests.RequestException as e:
        print(f"[API WARN] Failed to move robot {robot_id}: {e}")
