"""
Tesla BLE MicroPython Library

A stable, user-friendly library for controlling Tesla vehicles via Bluetooth Low Energy.

Example usage:
    from tesla_ble import TeslaClient, VehicleState
    
    client = TeslaClient(vin="YOUR_VIN")
    await client.connect()
    state = await client.send_body_controller_state_request()
    print(f"Doors locked: {state.is_locked}")
    await client.disconnect()
"""

__version__ = "0.1.0"

# Public API exports
try:
    from .client import MinimalTeslaClient as TeslaClient
    from .vehicle_state import VehicleState
    from .parser import parse_body_controller_state
except ImportError:
    from client import MinimalTeslaClient as TeslaClient
    from vehicle_state import VehicleState
    from parser import parse_body_controller_state

# Backward compatibility alias
MinimalTeslaClient = TeslaClient

__all__ = ["TeslaClient", "MinimalTeslaClient", "VehicleState", "parse_body_controller_state", "__version__"]
