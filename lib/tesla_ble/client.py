"""Minimal Tesla BLE client for unauthenticated commands.

This client implements a minimal subset of Tesla BLE functionality for commands
that do not require authentication, specifically the body-controller-state command.

Based on the official Tesla vehicle-command implementation which shows that
body-controller-state has requiresAuth: false.

Key differences from full TeslaClient:
- No private/public key loading
- No authentication handshake
- No message signing
- Only supports body-controller-state command
- Simpler connection flow

Compatible with MicroPython on Raspberry Pi Pico W.
"""

try:
    import uasyncio as asyncio
    import ustruct as struct
    import utime as time
    import uhashlib as hashlib
    import ubinascii as binascii
except ImportError:
    import asyncio
    import struct
    import time
    import hashlib
    import binascii

try:
    import usys as sys
except ImportError:
    import sys

# Import aioble for BLE operations
try:
    import aioble
except ImportError:
    aioble = None

try:
    from bluetooth import UUID
except ImportError:
    UUID = None

# Import constants
from tesla_ble.constants import (
    SERVICE_UUID,
    WRITE_UUID,
    READ_UUID,
    ConnectionError,
    TimeoutError,
    ProtocolError,
)


class MinimalTeslaClient:
    """Minimal Tesla BLE client for unauthenticated commands.
    
    This client provides a simplified interface for sending commands that do not
    require authentication, such as body-controller-state. It skips the handshake
    and message signing steps, making it faster and simpler than the full client.
    
    Usage:
        client = MinimalTeslaClient(vin="YOUR_VIN", debug=False)
        await client.connect()
        response = await client.send_body_controller_state_request()
        await client.disconnect()
    
    Args:
        vin: Vehicle Identification Number (17 characters)
        debug: If True, log all TX/RX messages and operations (default: False)
    """
    
    def __init__(self, vin, debug=False, device_cache_timeout_ms=300000):
        """Initialize minimal client with VIN only.

        Args:
            vin: Vehicle VIN (17 characters)
            debug: If True, log all TX/RX messages (default: False)
            device_cache_timeout_ms: Cache timeout in ms (default: 300000 = 5 minutes)

        Raises:
            ValueError: If VIN is invalid
        """
        if not vin or len(vin) != 17:
            raise ValueError("VIN must be exactly 17 characters")

        self.vin = vin
        self.debug = debug

        # Calculate BLE name from VIN
        self.ble_name = self._calculate_ble_name()

        # Connection state
        self._connection = None
        self._write_char = None
        self._read_char = None
        self._device = None

        # Device caching - cache MAC address instead of device object
        # This avoids issues with stale device objects after disconnect
        self._cached_mac = None
        self._cache_timestamp = None
        self._cache_timeout_ms = device_cache_timeout_ms

        # Stateful vehicle state (initialized on connect)
        self._vehicle_state = None

        if self.debug:
            print("[MinimalTeslaClient] Initialized with VIN: {}".format(vin))
            print("[MinimalTeslaClient] BLE Name: {}".format(self.ble_name))
            print("[MinimalTeslaClient] Cache timeout: {}ms".format(device_cache_timeout_ms))
    
    def _calculate_ble_name(self):
        """Calculate BLE advertisement name from VIN.
        
        The BLE name is calculated as:
        - Take SHA1 hash of VIN
        - Take first 8 bytes of hash
        - Format as "S{hex}C"
        
        Returns:
            str: BLE advertisement name (e.g., "S3e4320fbef5e5519C")
        """
        # Calculate SHA1 hash of VIN
        h = hashlib.sha1(self.vin.encode('utf-8'))
        hash_bytes = h.digest()
        
        # Take first 8 bytes
        first_8_bytes = hash_bytes[:8]
        
        # Convert to hex string
        hex_str = binascii.hexlify(first_8_bytes).decode('ascii')
        
        # Format as "S{hex}C"
        ble_name = "S{}C".format(hex_str)
        
        return ble_name

    def _is_cache_valid(self):
        """Check if cached MAC address is still valid (within timeout).

        Returns:
            bool: True if cache is valid, False otherwise
        """
        if self._cached_mac is None or self._cache_timestamp is None:
            return False

        # Calculate time elapsed since cache
        current_time = time.ticks_ms()
        elapsed = time.ticks_diff(current_time, self._cache_timestamp)

        # Check if cache is still valid
        is_valid = elapsed < self._cache_timeout_ms

        if self.debug and not is_valid:
            print("[MinimalTeslaClient] Cache expired (age: {}ms, timeout: {}ms)".format(
                elapsed, self._cache_timeout_ms))

        return is_valid

    def _cache_device(self, device):
        """Cache device MAC address and timestamp for future connections.

        Args:
            device: aioble.Device object to extract MAC from
        """
        # Store MAC address instead of device object
        # Device objects can become stale after disconnect
        self._cached_mac = device.addr
        self._cache_timestamp = time.ticks_ms()

        if self.debug:
            print("[MinimalTeslaClient] MAC address cached for {}ms: {}".format(
                self._cache_timeout_ms, self._cached_mac))

    
    
    async def connect(self, force_scan=False, mac_address=None):
        """Connect to vehicle without authentication with smart caching.

        This method establishes a BLE connection to the vehicle and discovers
        the Tesla BLE service and characteristics. It does NOT perform the
        authentication handshake, making it suitable for unauthenticated commands
        like body-controller-state.

        Connection logic:
        - If mac_address provided: Create device from MAC (skip scan)
        - Else if cached device valid and not force_scan: Use cached device
        - Else: Scan for vehicle and cache result
        - On connection failure with cached device: Retry with fresh scan

        Args:
            force_scan: Force new BLE scan even if device is cached (default: False)
            mac_address: Optional MAC address for direct connection (skips scan)

        Returns:
            bool: True if connection successful

        Raises:
            ConnectionError: If connection fails or aioble is not available
            TimeoutError: If connection times out
        """
        if aioble is None:
            raise ConnectionError("aioble library not available - required for BLE connection")

        if self.debug:
            print("[MinimalTeslaClient] Connecting to vehicle...")
            print("[MinimalTeslaClient] Force scan: {}".format(force_scan))
            if mac_address:
                print("[MinimalTeslaClient] MAC address provided: {}".format(mac_address))

        try:
            device = None

            # Connection Decision Tree
            if mac_address:
                # Path 1: MAC address provided - create device directly (fastest)
                if self.debug:
                    print("[MinimalTeslaClient] Creating device from MAC address...")

                # Import Device from aioble
                from aioble import Device

                # Create device from MAC address
                # Note: MAC address format should be "XX:XX:XX:XX:XX:XX"
                device = Device(aioble.ADDR_PUBLIC, mac_address)

                if self.debug:
                    print("[MinimalTeslaClient] Device created from MAC")

            elif self._is_cache_valid() and not force_scan:
                # Path 2: Cached MAC valid and not forcing scan - create device from MAC (fast)
                if self.debug:
                    print("[MinimalTeslaClient] Using cached MAC address...")

                # Import Device from aioble
                from aioble import Device

                # Create fresh device object from cached MAC
                device = Device(aioble.ADDR_PUBLIC, self._cached_mac)

                if self.debug:
                    print("[MinimalTeslaClient] Device created from cached MAC: {}".format(self._cached_mac))

                # Try to connect with device from cached MAC
                try:
                    if self.debug:
                        print("[MinimalTeslaClient] Attempting connection with cached MAC...")

                    self._connection = await asyncio.wait_for(
                        device.connect(),
                        timeout=10
                    )

                    if self.debug:
                        print("[MinimalTeslaClient] Connected using cached MAC")

                except Exception as e:
                    # Cached MAC connection failed - retry with fresh scan
                    if self.debug:
                        print("[MinimalTeslaClient] Cached MAC connection failed: {}".format(e))
                        print("[MinimalTeslaClient] Retrying with fresh scan...")

                    # Clear failed connection
                    self._connection = None

                    # Perform fresh scan
                    device = await self.scan_for_vehicle(timeout_ms=20000)

                    if device is None:
                        raise ConnectionError("Vehicle not found: {}".format(self.ble_name))

                    # Cache the new device MAC
                    self._cache_device(device)

                    # Try connecting again with fresh device
                    self._connection = await asyncio.wait_for(
                        device.connect(),
                        timeout=10
                    )

                    if self.debug:
                        print("[MinimalTeslaClient] Connected after fresh scan")

            else:
                # Path 3: No cache or force_scan - scan for vehicle (reliable)
                if self.debug:
                    if force_scan:
                        print("[MinimalTeslaClient] Force scan requested, scanning...")
                    else:
                        print("[MinimalTeslaClient] No valid cache, scanning...")

                device = await self.scan_for_vehicle(timeout_ms=20000)

                if device is None:
                    raise ConnectionError("Vehicle not found: {}".format(self.ble_name))

                # Cache the device MAC for future connections
                self._cache_device(device)

                # Connect to device
                if self.debug:
                    print("[MinimalTeslaClient] Connecting to device...")

                self._connection = await asyncio.wait_for(
                    device.connect(),
                    timeout=10
                )

                if self.debug:
                    print("[MinimalTeslaClient] Connected after scan")

            # If we haven't connected yet (MAC address or successful cache path), connect now
            if self._connection is None and device is not None:
                if self.debug:
                    print("[MinimalTeslaClient] Connecting to device...")

                self._connection = await asyncio.wait_for(
                    device.connect(),
                    timeout=10
                )

            if self.debug:
                print("[MinimalTeslaClient] Connected to vehicle")

            # Step 3: Exchange MTU (517 bytes for large responses)
            if self.debug:
                print("[MinimalTeslaClient] Exchanging MTU...")

            # Try to exchange MTU if the method exists
            try:
                if hasattr(self._connection, 'exchange_mtu'):
                    await self._connection.exchange_mtu(517)
                    if self.debug:
                        print("[MinimalTeslaClient] MTU exchanged: 517 bytes")
                else:
                    if self.debug:
                        print("[MinimalTeslaClient] MTU exchange not available, using default")
            except Exception as e:
                if self.debug:
                    print("[MinimalTeslaClient] MTU exchange failed (non-fatal): {}".format(e))

            # Step 4: Discover Tesla BLE service
            if self.debug:
                print("[MinimalTeslaClient] Discovering Tesla BLE service...")
                print("[MinimalTeslaClient] Connection object: {}".format(self._connection))
                print("[MinimalTeslaClient] Connection type: {}".format(type(self._connection)))

            # Check if connection is valid
            if self._connection is None:
                raise ConnectionError("Connection is None before service discovery")

            # Check if UUID is available
            if UUID is None:
                raise ConnectionError("bluetooth.UUID not available")

            # Convert service UUID string to bluetooth UUID
            try:
                service_uuid = UUID(SERVICE_UUID)
                if self.debug:
                    print("[MinimalTeslaClient] Service UUID created: {}".format(service_uuid))
            except Exception as e:
                raise ConnectionError("Failed to create service UUID: {}".format(e))

            # Discover service
            try:
                if self.debug:
                    print("[MinimalTeslaClient] Calling connection.service()...")
                service = await self._connection.service(service_uuid)
                if self.debug:
                    print("[MinimalTeslaClient] Service call returned: {}".format(service))
            except Exception as e:
                if self.debug:
                    import sys
                    sys.print_exception(e)
                raise ConnectionError("Service discovery failed: {}".format(e))

            if service is None:
                raise ConnectionError("Tesla BLE service not found")

            if self.debug:
                print("[MinimalTeslaClient] Service discovered: {}".format(SERVICE_UUID))

            # Step 5: Discover characteristics
            if self.debug:
                print("[MinimalTeslaClient] Discovering characteristics...")

            # Convert characteristic UUIDs
            write_uuid = UUID(WRITE_UUID)
            read_uuid = UUID(READ_UUID)

            # Get characteristics
            self._write_char = await service.characteristic(write_uuid)
            self._read_char = await service.characteristic(read_uuid)

            if self._write_char is None:
                raise ConnectionError("Write characteristic not found")

            if self._read_char is None:
                raise ConnectionError("Read characteristic not found")

            if self.debug:
                print("[MinimalTeslaClient] Write characteristic: {}".format(WRITE_UUID))
                print("[MinimalTeslaClient] Read characteristic: {}".format(READ_UUID))

            # Step 6: Subscribe to read notifications
            if self.debug:
                print("[MinimalTeslaClient] Subscribing to read notifications...")

            await self._read_char.subscribe(notify=True)

            if self.debug:
                print("[MinimalTeslaClient] Subscribed to notifications")

            # Step 7: Do NOT perform handshake (this is the key difference)
            if self.debug:
                print("[MinimalTeslaClient] Skipping authentication handshake (not required)")

            # Step 8: Initialize fresh VehicleState for this connection
            from tesla_ble.vehicle_state import VehicleState
            self._vehicle_state = VehicleState()
            
            if self.debug:
                print("[MinimalTeslaClient] VehicleState initialized (all fields None)")

            if self.debug:
                print("[MinimalTeslaClient] Connection complete!")

            return True

        except asyncio.TimeoutError:
            if self.debug:
                print("[MinimalTeslaClient] Connection timeout")
            raise TimeoutError("Connection timeout after 10 seconds")

        except Exception as e:
            if self.debug:
                print("[MinimalTeslaClient] Connection error: {}".format(e))

            # Clean up on error
            await self.disconnect()

            raise ConnectionError("Failed to connect: {}".format(e))
    async def scan_for_vehicle(self, timeout_ms=10000):
        """Scan for vehicle and return device if found.

        Uses aioble.scan() with active scanning to discover the vehicle by BLE name.
        Reports RSSI signal strength when vehicle is found.

        Args:
            timeout_ms: Scan timeout in milliseconds (default: 10000)

        Returns:
            aioble.Device: Device object if found, None otherwise

        Raises:
            ConnectionError: If aioble is not available or scan fails
        """
        if aioble is None:
            raise ConnectionError("aioble library not available - required for BLE scanning")

        if self.debug:
            print("[MinimalTeslaClient] Scanning for vehicle: {}".format(self.ble_name))
            print("[MinimalTeslaClient] Scan timeout: {}ms".format(timeout_ms))

        device = None

        try:
            # Use aioble.scan() with active scanning
            # Note: On Pico W, do NOT combine active=True with interval_us/window_us
            # as it causes hanging. Use active=True alone.
            async with aioble.scan(duration_ms=timeout_ms, active=True) as scanner:
                async for result in scanner:
                    # Match on exact BLE name
                    if result.name() == self.ble_name:
                        device = result.device
                        rssi = result.rssi

                        if self.debug:
                            print("[MinimalTeslaClient] Found: {} (RSSI: {} dBm)".format(
                                result.name(), rssi))

                        # Store device for later use
                        self._device = device

                        # Return immediately when found
                        break

        except Exception as e:
            if self.debug:
                print("[MinimalTeslaClient] Scan error: {}".format(e))
            raise ConnectionError("BLE scan failed: {}".format(e))

        if device is None:
            if self.debug:
                print("[MinimalTeslaClient] Vehicle not found: {}".format(self.ble_name))

        return device

    def is_connected(self):
        """Check if client is connected to vehicle.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return (self._connection is not None and 
                self._write_char is not None and 
                self._read_char is not None)
    
    async def disconnect(self):
        """Disconnect from vehicle.
        
        Closes the BLE connection and clears all connection state.
        Handles errors gracefully and does not raise exceptions.
        Includes delay to allow BLE stack to fully clean up.
        """
        if self.debug:
            print("[MinimalTeslaClient] Disconnecting...")
        
        try:
            # Unsubscribe from notifications first
            if self._read_char is not None:
                try:
                    await self._read_char.subscribe(notify=False)
                    if self.debug:
                        print("[MinimalTeslaClient] Unsubscribed from notifications")
                except Exception as e:
                    if self.debug:
                        print("[MinimalTeslaClient] Error unsubscribing: {}".format(e))
            
            # Disconnect from device
            if self._connection is not None:
                try:
                    await self._connection.disconnect()
                    if self.debug:
                        print("[MinimalTeslaClient] Connection closed")
                except Exception as e:
                    if self.debug:
                        print("[MinimalTeslaClient] Error during disconnect: {}".format(e))
            
            # Give BLE stack time to clean up (critical for preventing EALREADY errors)
            await asyncio.sleep_ms(100)
            
        except Exception as e:
            if self.debug:
                print("[MinimalTeslaClient] Error during disconnect: {}".format(e))
        finally:
            # Clear all connection state
            self._connection = None
            self._write_char = None
            self._read_char = None
            self._device = None
            
            # Note: We keep _cached_mac and _cache_timestamp for future connections
            # The cache will be validated by _is_cache_valid() before reuse
            # We also keep _vehicle_state to preserve accumulated knowledge
            
            if self.debug:
                print("[MinimalTeslaClient] Disconnected (state preserved)")

    def _generate_random_bytes(self, n):
        """Generate n random bytes.

        Uses urandom if available (MicroPython), otherwise uses random module.

        Args:
            n: Number of bytes to generate

        Returns:
            bytes: Random bytes
        """
        try:
            import urandom
            result = bytearray()
            for _ in range(n // 4):
                rand_int = urandom.getrandbits(32)
                result.extend(rand_int.to_bytes(4, 'big'))
            # Handle remaining bytes
            remaining = n % 4
            if remaining > 0:
                rand_int = urandom.getrandbits(remaining * 8)
                result.extend(rand_int.to_bytes(remaining, 'big'))
            return bytes(result)
        except ImportError:
            import random
            return bytes(random.randint(0, 255) for _ in range(n))

    def _build_body_controller_state_request(self):
        """Build body-controller-state request matching tesla-control exactly.

        Based on detailed byte-by-byte analysis of tesla-control TX messages:

        Pattern (50 bytes payload):
        - 32 02 08 02                    : Field 6 (to_destination, domain=2)
        - 3a 12 12 10 [16 bytes]         : Field 7 (from_destination, routing_address)
        - 9a 03 10 [16 bytes]            : Field 19 (uuid, length=16)
        - a0 03 02                       : Field 20 (flags, value=2)
        - 52 02 0a 00                    : Field 10 (signature_data, empty)

        Key fix: Field 19 uuid is 16 bytes, not 2 bytes!
        - 9a 03 = field tag (field 19, wire type 2)
        - 10 = length (16 decimal = 0x10)
        - [16 bytes] = uuid data

        Total: 4 + 20 + 19 + 3 + 4 = 50 bytes (matches tesla-control)

        Returns:
            bytes: Complete message with 2-byte length header
        """
        # Field 6: to_destination (domain=VCSEC=2)
        field6 = bytes.fromhex('32020802')

        # Field 7: from_destination (with 16-byte routing address)
        routing_address = self._generate_random_bytes(16)
        field7 = bytes([0x3a, 0x12, 0x12, 0x10]) + routing_address

        # Field 19: uuid (16 bytes, not 2!)
        # 9a 03 = field 19 tag
        # 10 = length (16 bytes in decimal)
        # [16 bytes] = uuid data
        uuid_bytes = self._generate_random_bytes(16)
        field19 = b'\x9a\x03\x10' + uuid_bytes

        # Field 20: flags (value=2)
        field20 = b'\xa0\x03\x02'

        # Field 10: signature_data (empty for unauthenticated)
        field10 = b'\x52\x02\x0a\x00'

        # Combine all fields in order
        payload = field6 + field7 + field19 + field20 + field10

        # Add 2-byte big-endian length header
        length_header = struct.pack('>H', len(payload))
        complete_message = length_header + payload

        if self.debug:
            print("[MinimalTeslaClient] Built request message ({} bytes)".format(len(complete_message)))
            print("[MinimalTeslaClient] TX: {}".format(binascii.hexlify(complete_message).decode('ascii')))

        return complete_message


    async def _send_fragmented(self, data, chunk_size=20):
        """Send data in BLE-sized chunks.

        Fragments the data into chunks and sends each chunk with a delay to
        prevent overwhelming the BLE stack. Uses write with response=True for
        reliability.

        Args:
            data: bytes to send
            chunk_size: Size of each chunk in bytes (default: 20)

        Raises:
            ConnectionError: If not connected or write fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to vehicle")

        if self.debug:
            print("[MinimalTeslaClient] Sending {} bytes in {}-byte chunks...".format(
                len(data), chunk_size))

        # Fragment and send
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]

            if self.debug:
                print("[MinimalTeslaClient] Sending chunk {}/{} ({} bytes)".format(
                    i // chunk_size + 1,
                    (len(data) + chunk_size - 1) // chunk_size,
                    len(chunk)))

            try:
                # Write with response for reliability
                await self._write_char.write(chunk, response=True)
            except Exception as e:
                if self.debug:
                    print("[MinimalTeslaClient] Write failed: {}".format(e))
                raise ConnectionError("Failed to write chunk: {}".format(e))

            # Delay between chunks to prevent overwhelming BLE stack
            await asyncio.sleep_ms(50)

        if self.debug:
            print("[MinimalTeslaClient] All chunks sent")

    async def _receive_message(self, timeout_ms=5000):
        """Receive and reassemble BLE response packets.

        Collects BLE notification packets and reassembles them into a complete
        message. For body-controller-state responses, we only need the first
        ~40 bytes which contain the vehicle status.

        Protocol:
        - Packets arrive as BLE notifications
        - Skip error packets: 0x22 0x01 0x01
        - Collect until we have a complete protobuf message (field 10 with valid data)
        
        Note: Tesla BLE protocol quirk - The response data does not include the
        RoutableMessage field tag (0x32) in the BLE notification. We prepend it
        before returning to match the expected protobuf format.

        Args:
            timeout_ms: Timeout in milliseconds (default: 5000)

        Returns:
            bytes: Complete message with 0x32 prefix prepended (ready for protobuf parsing)

        Raises:
            TimeoutError: If no response received within timeout
            ConnectionError: If not connected
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to vehicle")

        if self.debug:
            print("[MinimalTeslaClient] Waiting for response (timeout: {}ms)...".format(timeout_ms))

        packets = []
        start_time = time.ticks_ms()
        first_packet = True

        try:
            while True:
                # Check timeout
                elapsed = time.ticks_diff(time.ticks_ms(), start_time)
                if elapsed >= timeout_ms:
                    if self.debug:
                        print("[MinimalTeslaClient] Response timeout after {}ms".format(elapsed))
                    raise TimeoutError("No response received within {}ms".format(timeout_ms))

                # Calculate remaining timeout
                remaining_timeout = timeout_ms - elapsed

                try:
                    # Wait for notification with remaining timeout
                    data = await asyncio.wait_for_ms(
                        self._read_char.notified(),
                        remaining_timeout
                    )

                    if data is None:
                        continue

                    # Skip error packets
                    if data == b'\x22\x01\x01':
                        if self.debug:
                            print("[MinimalTeslaClient] Skipping error packet")
                        continue

                    if self.debug:
                        print("[MinimalTeslaClient] Received packet: {} bytes".format(len(data)))

                    # Handle first packet
                    if first_packet:
                        # Check if it has a length header (0x00 + 2 bytes)
                        if len(data) >= 3 and data[0] == 0x00:
                            # Skip length header, store rest
                            packets.append(data[3:])
                        else:
                            # No length header, store as-is
                            packets.append(data)
                        first_packet = False
                    else:
                        # Subsequent packets
                        packets.append(data)

                    # For body-controller-state, we expect a small response (~40 bytes)
                    # Stop after we have enough data for a complete message
                    total_received = sum(len(p) for p in packets)
                    
                    # Check if we have a complete protobuf message
                    # A complete message should have at least field 10 with data
                    if total_received >= 30:  # Minimum size for a valid response
                        # Try to parse and see if we have field 10
                        try:
                            complete_message = b''.join(packets)
                            # Quick check: does it look like a complete message?
                            # Field 6 (0x32), Field 7 (0x3a), Field 10 (0x52)
                            if b'\x52' in complete_message[:50]:  # Field 10 marker
                                if self.debug:
                                    print("[MinimalTeslaClient] Complete message detected ({} bytes)".format(
                                        total_received))
                                break
                        except:
                            pass

                    # Safety: stop after collecting 100 bytes (way more than needed)
                    if total_received >= 100:
                        if self.debug:
                            print("[MinimalTeslaClient] Collected {} bytes, stopping".format(total_received))
                        break

                except asyncio.TimeoutError:
                    # If we have some packets, consider it complete
                    if len(packets) > 0:
                        total_received = sum(len(p) for p in packets)
                        if self.debug:
                            print("[MinimalTeslaClient] Timeout waiting for more packets, using {} bytes received".format(
                                total_received))
                        break
                    else:
                        # No packets received at all
                        continue

        except Exception as e:
            if self.debug:
                print("[MinimalTeslaClient] Error receiving message: {}".format(e))
            raise

        # Reassemble complete message
        complete_message = b''.join(packets)

        # Tesla BLE protocol quirk: The response does not include the RoutableMessage
        # field tag (0x32) in the BLE notification. We need to prepend it to match
        # the expected protobuf format for parsing.
        # 
        # Expected format: 0x32 [length] [data...]
        # BLE notification: [length] [data...] (missing 0x32)
        #
        # This matches the behavior observed in tesla-control where responses start
        # with 0x32 but BLE notifications start with the next byte.
        complete_message = b'\x32' + complete_message

        if self.debug:
            print("[MinimalTeslaClient] RX (with 0x32 prefix): {}".format(
                binascii.hexlify(complete_message).decode('ascii')))

        return complete_message

    async def send_body_controller_state_request(self):
        """Send unauthenticated body-controller-state command and return updated state.

        This command retrieves basic vehicle state (doors, locks, sleep status)
        without requiring authentication. It's faster than authenticated commands
        and works when the infotainment system is asleep.

        The command:
        1. Builds the request message
        2. Sends it in fragmented chunks
        3. Receives and reassembles the response
        4. Parses response into new_state
        5. Updates internal _vehicle_state with new values
        6. Logs changes if debug mode enabled
        7. Returns updated _vehicle_state

        Returns:
            VehicleState: Updated vehicle state with accumulated knowledge

        Raises:
            ConnectionError: If not connected or send/receive fails
            TimeoutError: If no response received within timeout
            ValueError: If response cannot be parsed
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to vehicle")

        if self.debug:
            print("[MinimalTeslaClient] Sending body-controller-state request...")

        # Build request message
        request = self._build_body_controller_state_request()

        # Send using fragmented helper
        await self._send_fragmented(request)

        # Receive response
        response_bytes = await self._receive_message(timeout_ms=5000)

        if self.debug:
            print("[MinimalTeslaClient] Received response: {} bytes".format(len(response_bytes)))

        # Parse response into new_state
        from tesla_ble.parser import parse_body_controller_state
        
        try:
            new_state = parse_body_controller_state(response_bytes)
        except Exception as e:
            if self.debug:
                print("[MinimalTeslaClient] Failed to parse response: {}".format(e))
            raise ValueError("Failed to parse response: {}".format(e))

        # Update internal state and get changes
        changes = self._vehicle_state.update_from_response(new_state)

        # Log changes if debug mode enabled
        if self.debug and changes:
            self._log_state_changes(changes)

        # Return updated state
        return self._vehicle_state

    def _log_state_changes(self, changes):
        """Log state changes for debug output.

        Formats the changes dictionary and logs each field change with old and new values.
        Also logs information about fields that retained values due to None in response.

        Args:
            changes: Dictionary mapping field_name to (old_value, new_value) tuples
        """
        if not changes:
            if self.debug:
                print("[MinimalTeslaClient] No state changes (all fields retained or None)")
            return

        print("[MinimalTeslaClient] State changes detected:")

        # Log each change
        for field, (old_value, new_value) in changes.items():
            # Format field name for display (MicroPython doesn't have .title())
            display_name = field.replace('_', ' ')

            print("[MinimalTeslaClient]   {}: {} -> {}".format(
                display_name,
                old_value if old_value is not None else "None",
                new_value
            ))






    async def get_vehicle_state(self):
        """Get vehicle state using body-controller-state command.

        This is the high-level method that:
        1. Sends body-controller-state request
        2. Receives raw response
        3. Validates response structure
        4. Parses response into VehicleState object

        Returns:
            VehicleState: Parsed vehicle state with all fields populated

        Raises:
            ConnectionError: If not connected or communication fails
            TimeoutError: If no response received
            ValueError: If response is invalid or cannot be parsed
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to vehicle")

        if self.debug:
            print("[MinimalTeslaClient] Getting vehicle state...")

        # Import validation and parsing modules
        from tesla_ble.response_validator import validate_response
        from tesla_ble.parser import parse_body_controller_state
        from tesla_ble.vehicle_state import VehicleState

        # Step 1: Send command and receive response
        response_bytes = await self.send_body_controller_state_request()

        # Step 2: Validate response
        if self.debug:
            print("[MinimalTeslaClient] Validating response...")

        validation_result = validate_response(response_bytes)

        if not validation_result['valid']:
            error_msg = "Invalid response: {}".format(', '.join(validation_result['errors']))
            if self.debug:
                print("[MinimalTeslaClient] {}".format(error_msg))
            raise ValueError(error_msg)

        if self.debug:
            print("[MinimalTeslaClient] Response validation passed")

        # Step 3: Parse response
        if self.debug:
            print("[MinimalTeslaClient] Parsing response...")

        try:
            parsed_state = parse_body_controller_state(response_bytes)
        except Exception as e:
            error_msg = "Failed to parse response: {}".format(e)
            if self.debug:
                print("[MinimalTeslaClient] {}".format(error_msg))
            raise ValueError(error_msg)

        if self.debug:
            print("[MinimalTeslaClient] Response parsed successfully")

        # Step 4: Create VehicleState object
        vehicle_state = VehicleState.from_parsed_state(parsed_state)

        if self.debug:
            print("[MinimalTeslaClient] Vehicle state created")
            print("[MinimalTeslaClient] Lock: {}, Sleep: {}, All doors closed: {}".format(
                vehicle_state.lock_state,
                vehicle_state.sleep_status,
                vehicle_state.all_doors_closed
            ))

        return vehicle_state
