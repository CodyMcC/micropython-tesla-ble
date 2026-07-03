# MicroPython Tesla BLE Library

A lightweight MicroPython library for Raspberry Pi Pico W to communicate with Tesla vehicles via Bluetooth Low Energy (BLE).

## Features

- 🚗 **Simple VIN-only setup** - No authentication or key management required
- 📡 **BLE communication** - Direct wireless connection to your Tesla
- 🔄 **Stateful state management** - Automatically handles intermittent data
- 🎯 **MicroPython optimized** - Designed specifically for Raspberry Pi Pico W
- 🪶 **Lightweight** - Minimal memory footprint for embedded systems

## What It Does

This library allows you to read your Tesla's vehicle state using the unauthenticated `body-controller-state` BLE command. You can check:

- Door status (all doors, trunks, charge port)
- Lock state
- User presence
- Sleep status

Perfect for building custom monitoring solutions, home automation integrations, or IoT projects.

## Quick Start

### 1. Hardware Setup

- Raspberry Pi Pico W with MicroPython installed
- Tesla vehicle within BLE range (~10 meters)

### 2. Installation

Copy the `lib/` directory to your Pico W:

```bash
# Using mpremote (USB)
mpremote cp -r lib/ :lib/

# Or using upydev (WiFi)
upydev sync lib/ /lib/
```

### 3. Basic Usage

```python
import uasyncio as asyncio
import sys
sys.path.insert(0, '/lib')

from tesla_ble import TeslaClient

async def main():
    # Create client with your VIN
    client = TeslaClient(vin="YOUR_VIN_HERE")

    try:
        # Connect to vehicle
        await client.connect()

        # Get vehicle state
        state = await client.send_body_controller_state_request()

        # Check status
        print("All doors closed: {}".format(state.all_doors_closed))
        print("Vehicle locked: {}".format(state.is_locked))

    finally:
        await client.disconnect()

asyncio.run(main())
```

See `examples/basic_usage.py` for a complete working example.

### Finding your vehicle

If you don't know your vehicle's BLE name, scan for nearby Teslas. The name is
derived one-way from the VIN as `"S" + hex(SHA1(VIN)[:8]) + "C"`, so you can
also compute it directly:

```python
from tesla_ble import scan_for_teslas, ble_name_for_vin

print(ble_name_for_vin("YOUR_VIN_HERE"))     # -> "S....C"

vehicles = await scan_for_teslas(timeout_ms=5000)   # vehicle must be awake
for v in vehicles:
    print(v["name"], v["rssi"])                 # pick the strongest signal
```

See `examples/scan_vehicles.py`.

## Library Structure

```
lib/
├── tesla_ble/              # Main library package
│   ├── __init__.py         # Package exports
│   ├── client.py           # TeslaClient + scan_for_teslas / ble_name_for_vin
│   ├── vehicle_state.py    # VehicleState data structure
│   ├── parser.py           # Response parser (hand-decoded protobuf)
│   ├── response_validator.py  # Response sanity checks
│   └── constants.py        # UUIDs, enums, exceptions
└── config_loader.py        # VIN config helper (reads /config/config.json)
```

The parser decodes the protobuf response by walking field numbers directly, so
the library ships **no generated protobuf classes** and has no build step. If
Tesla ever changes the wire format, the fix lives in `parser.py`.

## API Reference

### TeslaClient

Main class for interacting with your Tesla.

```python
client = TeslaClient(vin: str, debug: bool = False)
```

**Parameters:**
- `vin` (str): Your vehicle's VIN (required)
- `debug` (bool): Enable debug logging (default: False)

**Methods:**
- `await connect()` - Connect to vehicle via BLE
- `await disconnect()` - Disconnect from vehicle
- `await send_body_controller_state_request()` - Get current vehicle state

### Module functions

- `ble_name_for_vin(vin) -> str` - Derive the BLE advertisement name from a VIN
  (pure; runs on host or device).
- `await scan_for_teslas(timeout_ms=5000, match_vin=None, debug=False) -> list` -
  Discover nearby Teslas. Returns `[{"name", "rssi", "addr"}, ...]`.

### VehicleState

Data structure containing vehicle state information.

**Door Status:**
- `front_driver_door`, `front_passenger_door`
- `rear_driver_door`, `rear_passenger_door`
- `front_trunk`, `rear_trunk`
- `charge_port`
- `tonneau` (Cybertruck bed cover)

**Vehicle Status:**
- `lock_state` - "LOCKED" | "UNLOCKED" | "INTERNAL_LOCKED" | "SELECTIVE_UNLOCKED"
- `user_presence` - "PRESENT" | "NOT_PRESENT"
- `sleep_status` - "AWAKE" | "ASLEEP"

Any field may be `None` (unknown / not yet reported). See *Data availability* below.

**Convenience Properties:**
- `all_doors_closed` (bool) - True if all four cabin doors are closed (`None` if unknown)
- `is_locked` (bool) - True if vehicle is locked
- `any_doors_open()` (bool) - True if any cabin door reads `"OPEN"`

### Data availability

The vehicle's response format varies by model and firmware. Some vehicles return
full per-door closure data; others return a session-specific blob from which
individual door states cannot be decoded. `user_presence` is the most reliably
reported field across formats; `lock_state` and `sleep_status` are best-effort;
door-level detail is available when the vehicle sends the full-closure format.
Because responses are often partial, the library retains the last known value
for any field that comes back `None` (see *Stateful State Management*).

## Stateful State Management

The library automatically handles intermittent `None` values in vehicle responses:

- **State Retention**: When a field is `None`, the last known value is retained
- **State Updates**: When a field has a valid value, it updates immediately
- **Knowledge Accumulation**: State builds up across multiple polling cycles

This makes monitoring reliable even when the vehicle returns partial responses.

## Examples

### Continuous Monitoring

```python
client = TeslaClient(vin="YOUR_VIN", debug=True)
await client.connect()

try:
    while True:
        state = await client.send_body_controller_state_request()
        
        if state.any_doors_open():
            print("Warning: Door is open!")
        
        await asyncio.sleep(5)  # Poll every 5 seconds
finally:
    await client.disconnect()
```

See `examples/monitor_state.py` for a complete monitoring example.

## Requirements

- **Hardware**: Raspberry Pi Pico W
- **Firmware**: MicroPython 1.20+
- **Vehicle**: Tesla with BLE support (most modern Teslas)

## Limitations

- Only supports unauthenticated commands (body-controller-state)
- Does not support sending commands to the vehicle (lock/unlock, etc.)
- Requires vehicle to be within BLE range (~10 meters)
- No authentication or key management included

## Development

This library is designed for production use on Pico W. For development:

```bash
# Install development tools
pip install mpremote upydev

# Deploy to Pico W
mpremote cp -r lib/ :lib/

# Run example
mpremote run examples/basic_usage.py
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Based on Tesla's official BLE protocol
- Inspired by [tesla-control](https://github.com/teslamotors/vehicle-command)
- Built for the MicroPython community

---

**Note**: This is an unofficial library and is not affiliated with Tesla, Inc.
