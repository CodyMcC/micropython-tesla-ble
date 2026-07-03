"""Tesla BLE MicroPython constants and enums."""

try:
    import usys as sys
except ImportError:
    import sys

# BLE Service and Characteristic UUIDs (from reference implementation)
SERVICE_UUID = "00000211-b2d1-43f0-9b88-960cebf8b91e"
WRITE_UUID = "00000212-b2d1-43f0-9b88-960cebf8b91e"
READ_UUID = "00000213-b2d1-43f0-9b88-960cebf8b91e"
VERSION_UUID = "00000214-b2d1-43f0-9b88-960cebf8b91e"
NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"
APPEARANCE_UUID = "00002a01-0000-1000-8000-00805f9b34fb"

# Memory constraints for Pico W
MAX_RAM_USAGE = 211 * 1024  # 80% of 264KB available RAM
MAX_FLASH_USAGE = int(1.6 * 1024 * 1024)  # 80% of 2MB available flash

# Connection and timing constants
DEFAULT_CONNECTION_TIMEOUT = 10  # seconds
DEFAULT_MESSAGE_TIMEOUT = 5  # seconds
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_POLL_INTERVAL = 2  # seconds for status monitoring
MAX_MESSAGE_SIZE = 1024  # bytes (protocol limit from Go implementation)
DEFAULT_BLE_MTU = 23  # Default BLE MTU (20 usable bytes after 3-byte ATT header)
TARGET_BLE_MTU = 512  # Target MTU for Pico W
MESSAGE_CHUNK_TIMEOUT_MS = 1000  # 1 second timeout between message chunks
MAX_BLE_LATENCY_MS = 4000  # 4 seconds max latency for BLE session info

# Debug levels (compatible with MicroPython)
class LogLevel:
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

# Vehicle state enums (from reference implementation)
class ClosureState:
    UNKNOWN = 0
    OPEN = 1
    CLOSED = 2

class VehicleLockState:
    UNKNOWN = 0
    UNLOCKED = 1
    LOCKED = 2
    INTERNAL_LOCKED = 3
    SELECTIVE_UNLOCKED = 4

class VehicleSleepStatus:
    UNKNOWN = 0
    AWAKE = 1
    ASLEEP = 2

class UserPresence:
    UNKNOWN = 0
    NOT_PRESENT = 1
    PRESENT = 2

class ConnectionStatus:
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    RECONNECTING = 3
    FAILED = 4

# NOTE: This library is unauthenticated-read-only. The removed classes
# (BluetoothVehicleData, RKEAction, Domain, KeyRole, KeyFormFactor) and the
# CryptoError exception were remnants of an earlier authenticated command
# client and have been archived under archive/legacy_tesla_ble_auth/.

# Error codes
class TeslaBLEError(Exception):
    """Base exception for Tesla BLE operations"""
    pass

class ConnectionError(TeslaBLEError):
    """Connection-related errors"""
    pass

class ProtocolError(TeslaBLEError):
    """Protocol and message errors"""
    pass

class SystemError(TeslaBLEError):
    """System and hardware errors"""
    pass

class TimeoutError(TeslaBLEError):
    """Timeout errors"""
    pass

class CommandError(TeslaBLEError):
    """Vehicle command execution errors"""
    pass

class AdapterError(TeslaBLEError):
    """BLE adapter/hardware errors - should not retry"""
    pass

class MaxConnectionsError(TeslaBLEError):
    """Vehicle at maximum BLE connections - should not retry"""
    pass