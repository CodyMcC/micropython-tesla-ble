"""
Simple working handshake implementation based on test_handshake_exact.py.
This uses the proven approach that successfully receives SessionInfo.
"""
import uasyncio as asyncio
import ustruct as struct
import utime as time
import ubinascii


def create_handshake_message(public_key_bytes, routing_address=None):
    """
    Create handshake message in the exact format that works.
    
    Args:
        public_key_bytes: 65-byte uncompressed public key (0x04 + X + Y)
        routing_address: Optional 16-byte routing address (generated if None)
    
    Returns:
        bytes: Complete handshake message with length header
    """
    # Generate routing address if not provided
    if routing_address is None:
        routing_address = _generate_routing_address()
    
    # Field 6: to_destination (domain=VEHICLE_SECURITY=2)
    field6 = bytes.fromhex('32020802')
    
    # Field 7: from_destination (with routing address)
    # Format: 0x3a (field 7, wire type 2) + length + 0x12 (field 2, wire type 2) + length + routing_address
    field7 = bytes([0x3a, 0x12, 0x12, 0x10]) + routing_address
    
    # Field 14: session_info_request (prefix + our public key)
    # Format: 0x72 (field 14, wire type 2) + length + 0x0a (field 1, wire type 2) + length + public_key
    field14_prefix = bytes([0x72, 0x43, 0x0a, 0x41])  # SessionInfoRequest with public_key field
    field14 = field14_prefix + public_key_bytes
    
    # Field 19: uuid (5 bytes for this example)
    field19 = bytes.fromhex('9a0310ae0d')
    
    # Field 23: flags
    field23 = bytes.fromhex('b8861c')
    
    # Field 10: signature_data (empty for handshake)
    field10 = bytes.fromhex('576840a0a76f22c38f24f8')
    
    # Combine all fields in exact order
    payload = field6 + field7 + field14 + field19 + field23 + field10
    
    # Add 2-byte big-endian length header
    length_header = struct.pack('>H', len(payload))
    complete_message = length_header + payload
    
    return complete_message


def _generate_routing_address():
    """Generate a random 16-byte routing address."""
    try:
        import urandom
        result = bytearray()
        for _ in range(4):
            rand_int = urandom.getrandbits(32)
            result.extend(rand_int.to_bytes(4, 'big'))
        return bytes(result)
    except:
        # Fallback: use a fixed address for testing
        return bytes.fromhex('e896e872cde518581d77c3d96897bb02')


async def receive_session_info(read_char, timeout_ms=30000, idle_timeout_ms=5000):
    """
    Receive SessionInfo response from vehicle.
    
    Key insight: The vehicle sends the response slowly over multiple packets
    that arrive over 10-15 seconds. We must be patient and keep collecting
    until we have a complete message.
    
    Args:
        read_char: BLE read characteristic (aioble characteristic)
        timeout_ms: Total timeout in milliseconds (default: 30 seconds)
        idle_timeout_ms: Timeout if no data received (default: 5 seconds)
    
    Returns:
        bytes: Complete SessionInfo message (without length header), or None on timeout
    """
    all_packets = []
    start_time = time.ticks_ms()
    last_receive_time = start_time
    
    # Collect all packets
    while True:
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)
        if elapsed > timeout_ms:
            break
        
        # Stop if no data for idle_timeout_ms
        if time.ticks_diff(time.ticks_ms(), last_receive_time) > idle_timeout_ms and len(all_packets) > 0:
            break
        
        try:
            data = await asyncio.wait_for_ms(read_char.notified(), 500)
            if data:
                last_receive_time = time.ticks_ms()
                
                # Skip error messages
                if data != b'\x22\x01\x01':
                    all_packets.append(data)
                    
        except asyncio.TimeoutError:
            continue
    
    if not all_packets:
        return None
    
    # Find the response message (starts with 0x00)
    for i, packet in enumerate(all_packets):
        if len(packet) >= 2 and packet[0] == 0x00:
            expected_length = struct.unpack('>H', packet[:2])[0]
            if 0 < expected_length <= 1024:
                # Reassemble from this packet onward
                buffer = bytearray()
                for j in range(i, len(all_packets)):
                    buffer.extend(all_packets[j])
                
                # Check if complete
                if len(buffer) >= expected_length + 2:
                    return bytes(buffer[2:expected_length+2])
    
    return None


def parse_session_info(message_bytes):
    """
    Parse SessionInfo from RoutableMessage bytes.
    
    Args:
        message_bytes: Complete RoutableMessage bytes (without length header)
    
    Returns:
        dict: Parsed session info with keys:
            - counter: int
            - clock_time: int (Unix timestamp)
            - vehicle_public_key: bytes (65 bytes)
            - epoch: bytes (16 bytes)
            - status: int (optional)
            - handle: int (optional)
    """
    result = {}
    i = 0
    
    # Parse RoutableMessage to find field 15 (session_info)
    while i < len(message_bytes):
        if i >= len(message_bytes):
            break
        tag = message_bytes[i]
        field_num = tag >> 3
        wire_type = tag & 0x07
        i += 1
        
        if wire_type == 2:  # Length-delimited
            if i >= len(message_bytes):
                break
            length = message_bytes[i]
            i += 1
            field_data = message_bytes[i:i+length]
            
            # Field 15 is session_info
            if field_num == 15:
                # Parse SessionInfo fields
                j = 0
                while j < len(field_data):
                    if j >= len(field_data):
                        break
                    tag2 = field_data[j]
                    field_num2 = tag2 >> 3
                    wire_type2 = tag2 & 0x07
                    j += 1
                    
                    if wire_type2 == 0:  # Varint
                        value = 0
                        shift = 0
                        while j < len(field_data):
                            byte = field_data[j]
                            value |= (byte & 0x7F) << shift
                            j += 1
                            if (byte & 0x80) == 0:
                                break
                            shift += 7
                        if field_num2 == 1:
                            result['counter'] = value
                        elif field_num2 == 5:
                            result['status'] = value
                        elif field_num2 == 6:
                            result['handle'] = value
                            
                    elif wire_type2 == 2:  # Bytes
                        if j >= len(field_data):
                            break
                        length2 = field_data[j]
                        j += 1
                        field_data2 = field_data[j:j+length2]
                        if field_num2 == 2:
                            result['vehicle_public_key'] = field_data2
                        elif field_num2 == 3:
                            result['epoch'] = field_data2
                        j += length2
                        
                    elif wire_type2 == 5:  # 32-bit fixed (clock_time is fixed32)
                        if j + 4 <= len(field_data):
                            # Little-endian 32-bit integer
                            value = struct.unpack('<I', field_data[j:j+4])[0]
                            if field_num2 == 4:
                                result['clock_time'] = value
                            j += 4
            
            i += length
        elif wire_type == 0:  # Varint
            value = 0
            shift = 0
            while i < len(message_bytes):
                byte = message_bytes[i]
                value |= (byte & 0x7F) << shift
                i += 1
                if (byte & 0x80) == 0:
                    break
                shift += 7
    
    return result


async def perform_handshake(connection, read_char, write_char, public_key_bytes, timeout_ms=30000):
    """
    Perform complete handshake with vehicle.
    
    CRITICAL: This function exchanges MTU before sending the handshake.
    Without MTU exchange, the vehicle can only send 20-byte fragments.
    
    Args:
        connection: aioble connection
        read_char: BLE read characteristic
        write_char: BLE write characteristic
        public_key_bytes: 65-byte uncompressed public key
        timeout_ms: Total timeout in milliseconds
    
    Returns:
        dict: Parsed SessionInfo or None on failure
    """
    # CRITICAL: Exchange MTU first!
    # Without this, vehicle is limited to 20-byte packets
    try:
        mtu = await connection.exchange_mtu(517)  # Request max MTU
        print(f"MTU negotiated: {mtu} bytes")
    except Exception as e:
        print(f"MTU exchange failed: {e}, continuing with default")
    
    # Create handshake message
    handshake_message = create_handshake_message(public_key_bytes)
    
    # Send handshake in chunks
    for i in range(0, len(handshake_message), 20):
        chunk = handshake_message[i:i+20]
        await write_char.write(chunk, response=True)
        await asyncio.sleep_ms(50)
    
    # Receive response
    message_bytes = await receive_session_info(read_char, timeout_ms=timeout_ms)
    
    if message_bytes:
        # Parse SessionInfo
        return parse_session_info(message_bytes)
    
    return None
