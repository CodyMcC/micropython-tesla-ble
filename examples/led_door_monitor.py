"""
LED Door Monitor Example

This example demonstrates how to use the Tesla BLE library to monitor door state
and control an LED (or other GPIO device) based on whether any doors are open.

The example uses the stateful state management feature, which retains last known
values when responses contain None, ensuring reliable monitoring even with
intermittent missing data.

LED Control Logic:
- Light ON: Any door is open
- Light OFF: All doors are closed

This example can be used as:
1. A test script to verify door monitoring works
2. A template for GPIO integration (see GPIO comments below)
3. A main.py for autonomous operation on Pico W

Requirements:
- VIN configured in /config/config.json
- Vehicle within BLE range
- (Optional) LED connected to GPIO pin for physical control

Usage:
    # Test on Pico W without modifying device
    ./scripts/test-on-pico.sh examples/led_door_monitor.py
    
    # Deploy as main.py for autonomous operation (rarely needed)
    # Note: This makes the script run on every boot
    mpremote cp examples/led_door_monitor.py :main.py

Example Output:
    Loaded VIN from config: 7G2CEHED7RA003723
    
    === Connecting to Vehicle ===
    Connected successfully!
    🔦 Light OFF
    
    === Starting Door Monitor (Ctrl+C to stop) ===
    Polling vehicle state every 1 second...
    LED will turn ON when any door opens
    
    [1] Door status: CLOSED - LED changed to OFF
    [10] Door status: CLOSED - LED remains OFF
    [20] Door status: CLOSED - LED remains OFF
    
    # User opens driver door...
    💡 Light ON
    [23] Door status: OPEN - LED changed to ON
    [30] Door status: OPEN - LED remains ON
    
    # User closes driver door...
    🔦 Light OFF
    [35] Door status: CLOSED - LED changed to OFF
    
    ^C
    
    === Monitoring Stopped by User ===
    
    === Cleaning Up ===
    🔦 Light OFF
    Disconnected. Goodbye!
"""

try:
    import uasyncio as asyncio
    import utime as time
except ImportError:
    import asyncio
    import time

# Import the Tesla BLE library
import sys
sys.path.insert(0, '/lib')
from tesla_ble import TeslaClient


# GPIO Configuration (uncomment when ready to use physical LED)
# ================================================================
# from machine import Pin
# LED_PIN = 15  # GPIO pin number for LED (adjust for your setup)
# led = Pin(LED_PIN, Pin.OUT)
# 
# def set_led(state):
#     """Control LED state.
#     
#     Args:
#         state: True for ON, False for OFF
#     """
#     led.value(1 if state else 0)
# ================================================================


def set_led(state):
    """Simulated LED control (prints to console).
    
    Replace this function with actual GPIO control when ready.
    See GPIO Configuration section above.
    
    Args:
        state: True for ON, False for OFF
    """
    if state:
        print("💡 Light ON")
    else:
        print("🔦 Light OFF")


async def monitor_doors(client):
    """
    Monitor door state and control LED.
    
    This function polls the vehicle state every 1 second and updates the LED
    based on whether any doors are open. The stateful state management ensures
    that the LED state remains accurate even when some responses contain None.
    
    Args:
        client: Connected TeslaClient instance
    """
    previous_led_state = None
    iteration = 0
    
    print("\n=== Starting Door Monitor (Ctrl+C to stop) ===")
    print("Polling vehicle state every 1 second...")
    print("LED will turn ON when any door opens\n")
    
    while True:
        try:
            iteration += 1
            
            # Query current state
            state = await client.send_body_controller_state_request()
            
            # Check if any doors are open
            any_open = state.any_doors_open()
            
            # Determine LED state
            if any_open is None:
                # Unknown state - keep LED in previous state
                led_state = previous_led_state if previous_led_state is not None else False
                status = "UNKNOWN (keeping LED {})".format("ON" if led_state else "OFF")
            elif any_open:
                # At least one door is open - turn LED ON
                led_state = True
                status = "OPEN"
            else:
                # All doors are closed - turn LED OFF
                led_state = False
                status = "CLOSED"
            
            # Update LED if state changed
            if led_state != previous_led_state:
                set_led(led_state)
                print("[{}] Door status: {} - LED changed to {}".format(
                    iteration,
                    status,
                    "ON" if led_state else "OFF"
                ))
            else:
                # No change - print heartbeat every 10 iterations
                if iteration % 10 == 0:
                    print("[{}] Door status: {} - LED remains {}".format(
                        iteration,
                        status,
                        "ON" if led_state else "OFF"
                    ))
            
            # Store current LED state for next comparison
            previous_led_state = led_state
            
            # Wait 1 second before next check
            await asyncio.sleep(1)
            
        except Exception as e:
            print("[{}] Error querying state: {}".format(iteration, e))
            # Continue monitoring even if one query fails
            await asyncio.sleep(1)


async def main():
    """Main function demonstrating LED control based on door state."""
    
    # Load VIN from config
    try:
        import ujson as json
    except ImportError:
        import json
    
    try:
        with open('/config/config.json', 'r') as f:
            config = json.load(f)
            vin = config['vin']
        print("Loaded VIN from config: {}".format(vin))
    except Exception as e:
        print("Error loading config: {}".format(e))
        print("Please ensure /config/config.json exists with your VIN")
        return
    
    # Create client instance (debug mode disabled for cleaner output)
    client = TeslaClient(vin=vin, debug=False)
    
    try:
        # Connect to vehicle
        print("\n=== Connecting to Vehicle ===")
        await client.connect()
        print("Connected successfully!")
        
        # Initialize LED to OFF
        set_led(False)
        
        # Start monitoring loop
        await monitor_doors(client)
        
    except KeyboardInterrupt:
        # User pressed Ctrl+C - exit gracefully
        print("\n\n=== Monitoring Stopped by User ===")
        
    except Exception as e:
        # Handle connection errors
        print("\n=== Error ===")
        print("Failed: {}".format(e))
        import sys
        sys.print_exception(e)
        
    finally:
        # Turn off LED and disconnect
        print("\n=== Cleaning Up ===")
        set_led(False)
        await client.disconnect()
        print("Disconnected. Goodbye!")


# Run the example
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
