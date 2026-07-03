"""
Scan for nearby Tesla vehicles over BLE.

Use this when you don't yet know your vehicle's BLE advertisement name, or to
check that your Tesla is awake and in range before connecting. Tesla vehicles
advertise as "S" + 16 hex chars + "C", derived one-way from the VIN (you cannot
recover a VIN from the name), so this lists what's nearby and how strong each
signal is -- pick yours by proximity (strongest RSSI) or by pre-computing your
own name from your VIN.

Requirements:
- Raspberry Pi Pico W with MicroPython
- A Tesla within BLE range (~10 m), awake

Notes:
- Keep scans short (~5 s) to limit WiFi interference on the Pico W.
- The vehicle must be awake to advertise.
"""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import sys
sys.path.insert(0, '/lib')

from tesla_ble import scan_for_teslas, ble_name_for_vin


async def main():
    # Optional: if you know your VIN, compute the exact name to look for.
    # VIN = "YOUR_VIN_HERE"
    # print("Expected BLE name for VIN: {}".format(ble_name_for_vin(VIN)))

    print("Scanning for nearby Teslas (5s)...")
    vehicles = await scan_for_teslas(timeout_ms=5000, debug=True)

    if not vehicles:
        print("\nNo Teslas found. Is the vehicle awake and in range?")
        return

    # Strongest signal first.
    vehicles.sort(key=lambda v: v["rssi"], reverse=True)

    print("\nFound {} vehicle(s):".format(len(vehicles)))
    for v in vehicles:
        print("  {}  RSSI {} dBm".format(v["name"], v["rssi"]))

    print("\nTo connect, pass your VIN to TeslaClient(vin=...). The client derives")
    print("the BLE name above from the VIN automatically.")


if __name__ == "__main__":
    asyncio.run(main())
