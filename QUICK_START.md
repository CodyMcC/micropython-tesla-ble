# Quick Start Guide

## What This Library Does

A MicroPython library for Raspberry Pi Pico W that reads Tesla vehicle state via BLE:
1. Connects to Tesla via BLE using VIN only
2. Reads vehicle state (doors, locks, trunks, charge port)
3. Maintains stateful state across polling cycles
4. No authentication or key management required

## Key Features

- **Simple VIN-only setup** - No keys or pairing needed
- **Stateful state management** - Handles intermittent None values automatically
- **Reliable monitoring** - State accumulates knowledge across polls
- **Debug logging** - See state changes in real-time

## Before You Start

### 1. Set Up VIN

Store your VIN in a config file:

```bash
# Create config directory
mkdir -p config

# Create config.json
cat > config/config.json << EOF
{
  "vin": "YOUR_VIN_HERE"
}
EOF
```

Replace `YOUR_VIN_HERE` with your actual 17-character VIN.

### 2. Deploy to Pico W

```bash
# Connect Pico W via USB, then:
./scripts/deploy.sh
```

This copies:
- VIN → `/config/config.json` on Pico W
- Library files → `/lib/` on Pico W

### 3. Verify Deployment

```bash
mpremote run test_config.py
```

You should see:
```
✓ Config loaded
✓ VIN: YOUR_VIN
✓ BLE Name: S<hash>C
```

### 4. Have Hardware Ready
- Raspberry Pi Pico W
- USB cable for deployment
- Access to your Tesla for testing

## Basic Usage

### Simple State Check

```python
from tesla_ble import TeslaClient

# Create client with VIN only
client = TeslaClient(vin="YOUR_VIN")

# Connect and get state
await client.connect()
state = await client.send_body_controller_state_request()

# Check status
print(f"All doors closed: {state.all_doors_closed}")
print(f"Vehicle locked: {state.is_locked}")

await client.disconnect()
```

### Continuous Monitoring

```python
from tesla_ble import TeslaClient

# Enable debug logging to see state changes
client = TeslaClient(vin="YOUR_VIN", debug=True)
await client.connect()

try:
    while True:
        state = await client.send_body_controller_state_request()
        
        # State accumulates across polls
        if state.any_doors_open():
            print("Door is open!")
        
        await asyncio.sleep(1)
finally:
    await client.disconnect()
```

## Stateful State Behavior

The library automatically handles intermittent None values:

```python
# First poll: Partial state
state = await client.send_body_controller_state_request()
# front_driver_door: "CLOSED", lock_state: "LOCKED", others: None

# Second poll: Different partial state
state = await client.send_body_controller_state_request()
# front_driver_door: None (retained as "CLOSED")
# lock_state: "UNLOCKED" (updated)

# State now has: front_driver_door="CLOSED", lock_state="UNLOCKED"
```

**Benefits:**
- No need to handle missing data in your code
- State builds up knowledge over time
- Reliable for monitoring applications
- Debug mode shows what's changing

## Examples

See the `examples/` directory:

- **`examples/led_door_monitor.py`** - LED control based on door state (START HERE)
- `examples/monitor_state.py` - Continuous state monitoring

## Testing on Pico W

```bash
# Deploy library
./scripts/deploy.sh

# Test without saving (recommended)
./scripts/test-on-pico.sh test_stateful_state.py

# Connect to REPL for debugging
./scripts/repl.sh
```

## Documentation

- **[Library Usage Guide](LIBRARY_USAGE.md)** - Complete API reference
- **[Pico Quick Reference](PICO_QUICK_REFERENCE.md)** - Common commands
- **[Wireless Deployment](docs/wireless-deployment/)** - WiFi deployment setup

## Common Questions

**Q: Do I need to pair keys with my vehicle?**  
A: No! The body-controller-state command works without authentication.

**Q: Why do some fields show None?**  
A: The vehicle sometimes returns partial responses. The library handles this automatically by retaining last known values.

**Q: How do I see what's changing?**  
A: Enable debug mode: `TeslaClient(vin="YOUR_VIN", debug=True)`

**Q: Can I use this for commands like lock/unlock?**  
A: No, this library only supports the unauthenticated body-controller-state command.

## Next Steps

1. Deploy to your Pico W
2. Run `examples/led_door_monitor.py`
3. Build your own monitoring application
4. Check `LIBRARY_USAGE.md` for advanced patterns
