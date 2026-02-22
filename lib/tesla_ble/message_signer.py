"""
HMAC message signing for Tesla BLE authenticated commands.
"""
import ustruct as struct
import utime
from .crypto import hmac_sha256


class MessageSigner:
    """
    Signs authenticated commands with HMAC.
    """
    
    def __init__(self, vin, epoch, counter, clock_delta, hmac_key):
        """
        Initialize message signer.
        
        Args:
            vin: Vehicle VIN (17 characters)
            epoch: 16-byte epoch from SessionInfo
            counter: Initial counter from SessionInfo
            clock_delta: Time delta (local_time - vehicle_time)
            hmac_key: Pre-computed HMAC key (32 bytes)
        """
        self.vin = vin.encode() if isinstance(vin, str) else vin
        self.epoch = epoch
        self.counter = counter
        self.clock_delta = clock_delta
        self.hmac_key = hmac_key
    
    def get_adjusted_time(self):
        """Get current time adjusted for vehicle clock."""
        return utime.time() - self.clock_delta
    
    def increment_counter(self):
        """Increment and return counter."""
        self.counter += 1
        return self.counter
    
    def create_signature_data(self, expires_at):
        """
        Create HMAC signature data for a command.
        
        Args:
            expires_at: Expiration timestamp (vehicle time)
        
        Returns:
            bytes: Serialized SignatureData protobuf
        
        Reference: signatures.proto - HMAC_Personalized_Signature_Data
        """
        # Field 1: epoch (bytes)
        field1 = b'\x0a' + bytes([len(self.epoch)]) + self.epoch
        
        # Field 2: counter (varint)
        counter_bytes = self._encode_varint(self.counter)
        field2 = b'\x10' + counter_bytes
        
        # Field 3: expires_at (fixed32)
        field3 = b'\x1d' + struct.pack('<I', expires_at)
        
        # Field 4: tag (bytes) - will be filled after HMAC
        # Placeholder for now
        field4 = b''
        
        signature_data = field1 + field2 + field3 + field4
        return signature_data
    
    def sign_message(self, command_bytes, domain):
        """
        Sign a command message with HMAC.
        
        Args:
            command_bytes: Serialized command protobuf
            domain: Domain (2 for VEHICLE_SECURITY, 3 for INFOTAINMENT)
        
        Returns:
            bytes: Complete signed RoutableMessage
        
        Reference:
            - Python: _commandHmac in commands.py
            - Protobuf: universal_message.proto, signatures.proto
        """
        # Increment counter
        counter = self.increment_counter()
        
        # Calculate expiration (30 seconds from now, vehicle time)
        expires_at = self.get_adjusted_time() + 30
        
        # Create metadata for HMAC
        # Format: signature_type (1 byte) + domain (varint) + VIN + command + metadata
        signature_type = 0x01  # SIGNATURE_TYPE_HMAC_PERSONALIZED
        
        metadata = bytearray()
        metadata.append(signature_type)
        metadata.extend(self._encode_varint(domain))
        metadata.extend(self.vin)
        metadata.extend(command_bytes)
        
        # Add personalized data to metadata
        metadata.extend(self.epoch)
        metadata.extend(self._encode_varint(counter))
        metadata.extend(struct.pack('<I', expires_at))
        
        # Compute HMAC tag
        tag = hmac_sha256(self.hmac_key, bytes(metadata))
        
        # For VEHICLE_SECURITY domain, truncate tag to 16 bytes
        if domain == 2:
            tag = tag[:16]
        
        # Create SignatureData protobuf
        # Field 1: HMAC_Personalized_data
        hmac_data = bytearray()
        # epoch
        hmac_data.extend(b'\x0a' + bytes([len(self.epoch)]) + self.epoch)
        # counter
        hmac_data.extend(b'\x10' + self._encode_varint(counter))
        # expires_at
        hmac_data.extend(b'\x1d' + struct.pack('<I', expires_at))
        # tag
        hmac_data.extend(b'\x22' + bytes([len(tag)]) + tag)
        
        signature_data = b'\x6a' + bytes([len(hmac_data)]) + bytes(hmac_data)
        
        # Create RoutableMessage
        # Field 6: to_destination
        to_dest = b'\x32\x02\x08' + bytes([domain])
        
        # Field 10: protobuf_message_as_bytes (the command)
        field10 = b'\x52' + self._encode_length_delimited(command_bytes)
        
        # Field 13: signature_data
        field13 = signature_data
        
        # Combine
        routable_message = to_dest + field10 + field13
        
        # Add length header
        length_header = struct.pack('>H', len(routable_message))
        
        return length_header + routable_message
    
    def _encode_varint(self, value):
        """Encode integer as protobuf varint."""
        result = bytearray()
        while value > 0x7f:
            result.append((value & 0x7f) | 0x80)
            value >>= 7
        result.append(value & 0x7f)
        return bytes(result)
    
    def _encode_length_delimited(self, data):
        """Encode length-delimited field."""
        length = len(data)
        if length < 128:
            return bytes([length]) + data
        else:
            # Multi-byte length
            return self._encode_varint(length) + data
