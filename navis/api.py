"""
Navis Python API
================

High-level Python API for the Navis device framework using Zenoh.

This module provides a comprehensive interface for building robotics
and IoT applications. It includes a generic client for devices, a
controller for sending commands, and utilities for device discovery.

Key abstractions:
    - ``DeviceInterface`` (ABC): Defines the contract for a device.
    - ``DeviceClient``: Task runner for any device implementing the interface.
    - ``DeviceController``: Tool for sending commands.
    - ``list_devices``: Discover devices on the network.
"""
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, List

import msgspec
import zenoh
from zenoh import Config

from navis.categories import ROBOTS
from navis.messages import Register, Move


class DeviceInterface(ABC):
    """
    Abstract interface defining the contract for a Navis device implementation.

    Devices implementing this interface must provide a method to handle
    commands received from the network.
    """

    @abstractmethod
    def dispatch_command(self, command: msgspec.Struct):
        """
        Process an incoming command object from the network.

        Args:
            command (msgspec.Struct): The decoded command received.
        """
        pass


@dataclass
class PublisherTask:
    """
    Defines a periodic publishing task for a device.

    Attributes:
        topic_suffix (str): Suffix of the topic to publish to.
        data_provider (Callable): Function returning the data to publish.
        interval_seconds (float): Period between successive publishes.
    """
    topic_suffix: str
    data_provider: Callable
    interval_seconds: float


def list_devices(category: str, timeout_seconds: float = 3.0) -> Dict[str, str]:
    """
    Discover devices on the network by listening for ``Register`` messages.

    Args:
        category (str): Device category (e.g., ``ROBOTS``).
        timeout_seconds (float): How long to listen for devices.

    Returns:
        Dict[str, str]: Mapping of ``robot_id`` -> ``robot_id`` for discovered devices.
    """
    session = zenoh.open(Config())
    devices_found: Dict[str, str] = {}
    lock = threading.Lock()
    decoder = msgspec.msgpack.Decoder(Register)

    def callback(sample):
        """
        Handle incoming ``Register`` messages and store discovered devices.

        Args:
            sample: The Zenoh sample containing registration data.
        """
        try:
            reg = decoder.decode(bytes(sample.payload))
            with lock:
                devices_found[reg.robot_id] = reg.robot_id
                print(f"[Navis API] Discovered device: {reg.robot_id}")
        except Exception as e:
            print(f"[DEBUG DISCOVERY] Error decoding Register: {e}")

    selector = f"navis/{category}/*/register"
    print(f"[Navis API] Listening on '{selector}' for {timeout_seconds}s...")
    sub = session.declare_subscriber(selector, callback)
    try:
        time.sleep(timeout_seconds)
    finally:
        try:
            if hasattr(sub, "close"):
                sub.close()
        except Exception:
            pass
        session.close()

    with lock:
        return dict(devices_found)

# [TODO] Some routings are hardcoded to publish to **/robots/**. Fix so that any device can publish to their corresponding
# device category.


class DeviceClient:
    """
    Generic client for a Navis device.

    Handles device registration, publishing periodic messages, and
    subscribing to commands.
    """

    def __init__(self, device_object: DeviceInterface, additional_messages: List[type] = None):
        """
        Initialize a ``DeviceClient`` for a device.

        Args:
            device_object (DeviceInterface): Object implementing ``dispatch_command``.
            additional_messages (List[type], optional): Additional command types to register.
        """
        if not hasattr(device_object, "dispatch_command") or not callable(getattr(device_object, "dispatch_command")):
            raise TypeError(
                "device_object must implement a callable ``dispatch_command(command)`` method.")

        self.device = device_object
        self.session = zenoh.open(Config())
        self.encoder = msgspec.msgpack.Encoder()

        # --- Get unique device ID ---
        print("[CLIENT] Requesting a unique ID from the server...")
        replies = self.session.get("navis/admin/id_service")
        try:
            reply = next(replies)
        except StopIteration:
            self.session.close()
            raise RuntimeError(
                "Could not get a unique ID from the server (no replies).")

        try:
            if reply.ok:
                self.device_id = bytes(reply.ok.payload).decode()
                print(f"[CLIENT] Assigned ID: {self.device_id}")
            else:
                self.session.close()
                raise RuntimeError("ID request failed: reply not ok.")
        except Exception as e:
            self.session.close()
            raise RuntimeError(f"Failed to decode ID service reply: {e}")

        # --- Publishers ---
        self.publish_tasks: List[dict] = []
        self.add_publisher(
            topic_suffix="register",
            data_provider=self._get_registration_msg,
            interval_seconds=5.0
        )

        # --- Command decoder ---
        self.decoder = msgspec.msgpack.Decoder()
        self.command_registry = {'Move': Move}
        if additional_messages:
            for msg_type in additional_messages:
                self.command_registry[msg_type.__name__] = msg_type

        # --- Thread control ---
        self._running = threading.Event()
        self._thread = None

    def add_publisher(self, topic_suffix: str, data_provider: Callable, interval_seconds: float):
        """
        Register a periodic publisher task.

        Args:
            topic_suffix (str): Suffix for the Zenoh topic.
            data_provider (Callable): Function providing the data.
            interval_seconds (float): Publish interval in seconds.
        """
        full_topic = f"navis/{ROBOTS}/{self.device_id}/{topic_suffix}"
        task_state = {"topic": full_topic, "provider": data_provider,
                      "interval": interval_seconds, "last_run": 0}
        self.publish_tasks.append(task_state)
        print(f"[{self.device_id}] Registered publisher for '{
              topic_suffix}' ({interval_seconds}s)")

    def _get_registration_msg(self) -> Register:
        """Return a ``Register`` message with the device ID."""
        return Register(robot_id=self.device_id)

    def _publish_loop(self):
        """Run all publishers periodically until stopped."""
        while not self._running.is_set():
            now = time.time()
            for task in self.publish_tasks:
                try:
                    if now - task["last_run"] >= task["interval"]:
                        data = task["provider"]()
                        if data is not None:
                            self.session.put(
                                task["topic"], self.encoder.encode(data))
                        task["last_run"] = now
                except Exception as e:
                    print(f"[{getattr(self, 'device_id', 'unknown')}] Publisher error on topic {
                          task.get('topic')}: {e}")
            time.sleep(0.05)

    def _command_callback(self, sample):
        """
        Decode and dispatch any incoming command.

        Args:
            sample: Zenoh sample containing the command message.
        """
        try:
            data = self.decoder.decode(bytes(sample.payload))
            if isinstance(data, msgspec.Struct):
                print(f"[{self.device_id}] Received command: {
                      type(data).__name__}")
                self.device.dispatch_command(data)
                return

            if isinstance(data, dict) and '__type__' in data:
                msg_type_name = data.pop('__type__')
                if msg_type_name in self.command_registry:
                    cmd_class = self.command_registry[msg_type_name]
                    cmd = cmd_class(**data)
                    print(f"[{self.device_id}] Received command: {
                          msg_type_name}")
                    self.device.dispatch_command(cmd)
                else:
                    print(f"[{self.device_id}] Unknown command type: {
                          msg_type_name}")
            else:
                print(f"[{self.device_id}] Invalid command format: {type(data)}")

        except Exception as e:
            print(f"[{self.device_id}] Command error: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """Start publishing tasks and subscribe to commands."""
        if self._thread and self._thread.is_alive():
            return
        print(f"[{self.device_id}] Starting client...")
        self._running.clear()
        command_topic = f"navis/{ROBOTS}/{self.device_id}/commands"
        print(f"[{self.device_id}] Subscribing to: {command_topic}")
        self.session.declare_subscriber(command_topic, self._command_callback)
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def close(self):
        """Stop the client and close the Zenoh session."""
        print(f"[{self.device_id}] Closing client...")
        self._running.set()
        if self._thread:
            self._thread.join()
        try:
            self.session.close()
        except Exception as e:
            print(f"[{self.device_id}] Error closing session: {e}")


class DeviceController:
    """
    Send commands to a specific Navis device.

    Provides convenience methods for common commands like ``Move``.
    """

    def __init__(self, device_id: str):
        """
        Initialize a controller for a device.

        Args:
            device_id (str): The target device ID.
        """
        self.device_id = device_id
        self.session = zenoh.open(Config())
        self.encoder = msgspec.msgpack.Encoder()
        print(f"[Navis API] Controller initialized for device '{
              self.device_id}'.")

    def send_command(self, command_object: msgspec.Struct):
        """
        Send any valid ``msgspec.Struct`` command to the device.

        Args:
            command_object (msgspec.Struct): The command to send.
        """
        key = f"navis/{ROBOTS}/{self.device_id}/commands"
        try:
            msg_dict = msgspec.structs.asdict(command_object)
            msg_dict['__type__'] = type(command_object).__name__
            payload = self.encoder.encode(msg_dict)
            print(f"[Controller:{self.device_id}] Sending {
                  type(command_object).__name__} to {key}")
            self.session.put(key, payload)
        except Exception as e:
            print(f"[Controller:{self.device_id}] Failed to send command: {e}")
            import traceback
            traceback.print_exc()

    def move(self, linear_vel: float = 0.0, angular_vel: float = 0.0):
        """
        Convenience method to send a ``Move`` command.

        Args:
            linear_vel (float): Forward velocity.
            angular_vel (float): Rotational velocity.
        """
        from navis.messages import Move
        self.send_command(Move(v=linear_vel, omega=angular_vel))

    def close(self):
        """Close the controller's Zenoh session."""
        try:
            self.session.close()
        except Exception as e:
            print(f"[Controller:{self.device_id}] Error closing session: {e}")
        print(f"[Navis API] Controller for '{self.device_id}' closed.")
