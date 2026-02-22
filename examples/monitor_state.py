"""
Vehicle State Monitoring Example

This example demonstrates continuous monitoring of Tesla vehicle state via BLE,
showcasing the library's stateful state management capabilities.

What This Example Shows:
1. VIN → Connect → Command → Disconnect pattern
2. Continuous state polling with change detection
3. Stateful state management (retains last known values when vehicle returns None)
4. Clean error handling and graceful shutdown

Key Features Demonstrated:
- Stateful state management: When the vehicle returns None for a field, the last
  known value is retained. This provides reliable monitoring even when the vehicle
  returns partial responses.
- Change detection: Only prints when state actually changes, reducing noise
- Heartbeat logging: Shows monitoring is active even when no changes occur
- Keyboard interrupt handling: Clean shutdown with Ctrl+C

Requirements:
- Raspberry Pi Pico W with MicroPython
- VIN configured in /config/config.json
- Vehicle within BLE range (no authentication required)

Expected Output:
  [1] Initial State:
    Doors: FD=CLOSED FP=CLOSED RD=CLOSED RP=CLOSED
    Trunks: Front=CLOSED Rear=CLOSED
    Charge Port: CLOSED
    Lock State: LOCKED
    User Presence: NOT_PRESENT
  
  [2] No changes (locked=True, all_closed=True)
  [3] No changes (locked=True, all_closed=True)
  
  [4] Changes Detected:
    - Front Driver Door: CLOSED -> OPEN
    - Lock State: LOCKED -> UNLOCKED
  
  [5] No changes (locked=False, all_closed=False)

Note: The stateful state management means that even if the vehicle returns None
for some fields in later polls, the last known values are retained and displayed.
"""

try:
    import uasyncio as asyncio
    import utime as time
except ImportError:
    import asyncio
    import time

# Import the Tesla BLE library
import sys
sys.path.insert(0, '/lib')  # MicroPython path for Pico W
from tesla_ble import TeslaClient, VehicleState


def state_to_dict(state):
    """
    Convert VehicleState to dictionary for comparison.
    
    This extracts the key fields we want to monitor for changes.
    We don't include all fields to keep the comparison focused on
    the most important state information.
    """
    return {
        'front_driver_door': state.front_driver_door,
        'front_passenger_door': state.front_passenger_door,
        'rear_driver_door': state.rear_driver_door,
        'rear_passenger_door': state.rear_passenger_door,
        'front_trunk': state.front_trunk,
        'rear_trunk': state.rear_trunk,
        'charge_port': state.charge_port,
        'lock_state': state.lock_state,
        'user_presence': state.user_presence,
    }


def print_changes(old_state, new_state):
    """
    Print only the fields that changed between states.
    
    This demonstrates the stateful state management: even if the vehicle
    returns None for some fields, we compare against the last known values
    (which are retained by the library).
    
    Args:
        old_state: Previous VehicleState (or None for first poll)
        new_state: Current VehicleState
    
    Returns:
        List of change descriptions
    """
    old_dict = state_to_dict(old_state) if old_state else {}
    new_dict = state_to_dict(new_state)
    
    changes = []
    for key, new_value in new_dict.items():
        old_value = old_dict.get(key)
        if old_value != new_value:
            # Format the key nicely (MicroPython compatible - no f-strings)
            display_key = key.replace('_', ' ')
            # Capitalize first letter of each word manually
            words = display_key.split(' ')
            display_key = ' '.join(w[0].upper() + w[1:] if len(w) > 0 else w for w in words)
            changes.append("{}: {} -> {}".format(
                display_key,
                old_value or "Unknown",
                new_value or "Unknown"
            ))
    
    return changes


async def monitor_loop(client):
    """
    Continuously monitor vehicle state and print changes.
    
    This loop demonstrates the stateful state management in action:
    - First poll: Shows initial state (may have some None values)
    - Subsequent polls: Shows only changes, with last known values retained
    - Heartbeat: Shows monitoring is active even when no changes occur
    
    The library's stateful state management means that if the vehicle returns
    None for a field, the last known value is retained. This provides reliable
    monitoring even when the vehicle returns partial responses.
    
    Args:
        client: Connected TeslaClient instance
    """
    previous_state = None
    iteration = 0
    
    print("\n=== Starting Monitoring (Ctrl+C to stop) ===")
    print("Checking vehicle state every 5 seconds...\n")
    
    while True:
        try:
            iteration += 1
            
            # Query current state from vehicle
            # Note: The library retains last known values when vehicle returns None
            current_state = await client.send_body_controller_state_request()
            
            # Check for changes
            if previous_state is None:
                # First iteration - print full state
                print("[{}] Initial State:".format(iteration))
                print("  Doors: FD={} FP={} RD={} RP={}".format(
                    current_state.front_driver_door or "?",
                    current_state.front_passenger_door or "?",
                    current_state.rear_driver_door or "?",
                    current_state.rear_passenger_door or "?"
                ))
                print("  Trunks: Front={} Rear={}".format(
                    current_state.front_trunk or "?",
                    current_state.rear_trunk or "?"
                ))
                print("  Charge Port: {}".format(current_state.charge_port or "?"))
                print("  Lock State: {}".format(current_state.lock_state or "?"))
                print("  User Presence: {}".format(current_state.user_presence or "?"))
            else:
                # Check for changes (comparing against last known state)
                changes = print_changes(previous_state, current_state)
                
                if changes:
                    print("[{}] Changes Detected:".format(iteration))
                    for change in changes:
                        print("  - {}".format(change))
                else:
                    # No changes - print heartbeat to show monitoring is active
                    print("[{}] No changes (locked={}, all_closed={})".format(
                        iteration,
                        current_state.is_locked,
                        current_state.all_doors_closed
                    ))
            
            # Store current state for next comparison
            # This demonstrates stateful state management: we're comparing
            # against the accumulated state, not just the raw response
            previous_state = current_state
            
            # Wait 5 seconds before next check
            await asyncio.sleep(5)
            
        except Exception as e:
            print("[{}] Error querying state: {}".format(iteration, e))
            # Continue monitoring even if one query fails
            await asyncio.sleep(5)


async def main():
    """
    Main function demonstrating continuous state monitoring.
    
    This follows the standard library pattern:
    1. Load VIN from config
    2. Create TeslaClient with VIN only (no authentication required)
    3. Connect to vehicle
    4. Monitor state continuously
    5. Disconnect cleanly (always, via try/finally)
    """
    
    # Step 1: Load VIN from config
    # The library requires only a VIN - no authentication or keys needed
    try:
        from config_loader import get_config
        config = get_config()
        vin = config.vin
        print("Loaded VIN from config: {}".format(vin))
    except Exception as e:
        print("Error loading config: {}".format(e))
        print("Please ensure /config/config.json exists with your VIN")
        return
    
    # Step 2: Create client instance (VIN only, no keys required)
    client = TeslaClient(vin=vin)
    
    try:
        # Step 3: Connect to vehicle via BLE
        print("\n=== Connecting to Vehicle ===")
        await client.connect()
        print("Connected successfully!")
        
        # Step 4: Start monitoring loop
        # This demonstrates stateful state management in action
        await monitor_loop(client)
        
    except KeyboardInterrupt:
        # User pressed Ctrl+C - exit gracefully
        print("\n\n=== Monitoring Stopped by User ===")
        
    except Exception as e:
        # Handle connection errors
        print("\n=== Error ===")
        print("Failed: {}".format(e))
        
    finally:
        # Step 5: Always disconnect cleanly
        # This ensures BLE connection is properly closed
        print("\n=== Disconnecting ===")
        await client.disconnect()
        print("Disconnected. Goodbye!")


# Run the example
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
