"""
Basic Tesla BLE Usage Example

This example demonstrates the simplest way to connect to your Tesla vehicle
and read its state via Bluetooth Low Energy (BLE). It follows the standard
library pattern: VIN → Connect → Command → Disconnect.

This is a one-time state check - the script connects, reads the current state,
displays it, and disconnects. For continuous monitoring, see monitor_state.py.

Requirements:
- Raspberry Pi Pico W with MicroPython 1.20+
- Tesla vehicle within BLE range (~10 meters)
- Your vehicle's 17-character VIN

What This Example Shows:
- Creating a TeslaClient with just a VIN (no authentication needed)
- Connecting to the vehicle via BLE
- Reading body controller state (doors, locks, sleep status)
- Handling None values for unknown fields
- Proper cleanup with try/finally

No Authentication Required:
The body-controller-state command works WITHOUT private keys or authentication.
This makes it perfect for simple monitoring applications.

Expected Output:
    Connecting to vehicle...
    Connected!
    
    Reading vehicle state...
    
    === Door Status ===
    Front Driver:    CLOSED
    Front Passenger: CLOSED
    Rear Driver:     CLOSED
    Rear Passenger:  CLOSED
    Front Trunk:     CLOSED
    Rear Trunk:      CLOSED
    Charge Port:     CLOSED
    
    === Vehicle Status ===
    Lock State:      LOCKED
    User Presence:   NOT_PRESENT
    Sleep Status:    ASLEEP
    
    === Quick Checks ===
    All Doors Closed: Yes
    Vehicle Locked:   Yes
    
    Disconnecting...
    Done!
"""

# Import asyncio (MicroPython uses uasyncio, standard Python uses asyncio)
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# Add library to path (required for MicroPython on Pico W)
import sys
sys.path.insert(0, '/lib')

# Import the Tesla BLE client
from tesla_ble import TeslaClient


async def main():
    """Connect to Tesla and read vehicle state once."""
    
    # Step 1: Configure your VIN
    # Replace with your vehicle's 17-character VIN
    # Or load from config: from config_loader import get_config; config = get_config(); VIN = config.vin
    VIN = "YOUR_VIN_HERE"
    
    # Step 2: Create client with VIN only (no keys needed)
    # debug=True enables logging to see what's happening
    client = TeslaClient(vin=VIN, debug=True)
    
    try:
        # Step 3: Connect to vehicle via BLE
        # This scans for the vehicle's BLE name (calculated from VIN)
        # and establishes a connection
        print("Connecting to vehicle...")
        await client.connect()
        print("Connected!\n")
        
        # Step 4: Request vehicle state
        # This sends a body-controller-state command and returns a VehicleState object
        # No authentication required for this command
        print("Reading vehicle state...")
        state = await client.send_body_controller_state_request()
        
        # Step 5: Display door status
        # Fields may be None if the vehicle doesn't report them
        # Use "or 'Unknown'" to handle None values gracefully
        print("\n=== Door Status ===")
        print("Front Driver:    {}".format(state.front_driver_door or "Unknown"))
        print("Front Passenger: {}".format(state.front_passenger_door or "Unknown"))
        print("Rear Driver:     {}".format(state.rear_driver_door or "Unknown"))
        print("Rear Passenger:  {}".format(state.rear_passenger_door or "Unknown"))
        print("Front Trunk:     {}".format(state.front_trunk or "Unknown"))
        print("Rear Trunk:      {}".format(state.rear_trunk or "Unknown"))
        print("Charge Port:     {}".format(state.charge_port or "Unknown"))
        
        # Step 6: Display vehicle status
        print("\n=== Vehicle Status ===")
        print("Lock State:      {}".format(state.lock_state or "Unknown"))
        print("User Presence:   {}".format(state.user_presence or "Unknown"))
        print("Sleep Status:    {}".format(state.sleep_status or "Unknown"))
        
        # Step 7: Use convenience properties for quick checks
        # These properties return bool or None
        print("\n=== Quick Checks ===")
        print("All Doors Closed: {}".format("Yes" if state.all_doors_closed else "No"))
        print("Vehicle Locked:   {}".format("Yes" if state.is_locked else "No"))
        
    finally:
        # Step 8: Always disconnect, even if an error occurs
        # This ensures the BLE connection is properly closed
        print("\nDisconnecting...")
        await client.disconnect()
        print("Done!")


# Run the example
if __name__ == "__main__":
    asyncio.run(main())
