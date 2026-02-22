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

# Tesla BLE vehicle data endpoints (from reference implementation)
class BluetoothVehicleData:
    CHARGE_STATE = "GetChargeState"
    CLIMATE_STATE = "GetClimateState"
    DRIVE_STATE = "GetDriveState"
    LOCATION_STATE = "GetLocationState"
    CLOSURES_STATE = "GetClosuresState"
    CHARGE_SCHEDULE_STATE = "GetChargeScheduleState"
    PRECONDITIONING_SCHEDULE_STATE = "GetPreconditioningScheduleState"
    TIRE_PRESSURE_STATE = "GetTirePressureState"
    MEDIA_STATE = "GetMediaState"
    MEDIA_DETAIL_STATE = "GetMediaDetailState"
    SOFTWARE_UPDATE_STATE = "GetSoftwareUpdateState"
    PARENTAL_CONTROLS_STATE = "GetParentalControlsState"

# RKE (Remote Keyless Entry) Actions
class RKEAction:
    WAKE_VEHICLE = 1
    UNLOCK = 2
    LOCK = 3
    OPEN_TRUNK = 4
    OPEN_FRUNK = 5
    CLOSE_TRUNK = 6
    CLOSE_FRUNK = 7
    OPEN_CHARGE_PORT = 8
    CLOSE_CHARGE_PORT = 9

# Protobuf domains (from reference implementation)
class Domain:
    DOMAIN_VEHICLE_SECURITY = 1
    DOMAIN_INFOTAINMENT = 2

# Key roles for pairing
class KeyRole:
    ROLE_NONE = 0
    ROLE_SERVICE = 1
    ROLE_OWNER = 2
    ROLE_DRIVER = 3

class KeyFormFactor:
    KEY_FORM_FACTOR_UNKNOWN = 0
    KEY_FORM_FACTOR_NFC_CARD = 1
    KEY_FORM_FACTOR_CLOUD_KEY = 2
    KEY_FORM_FACTOR_PHONE_KEY = 3

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

class CryptoError(TeslaBLEError):
    """Cryptographic operation errors"""
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

# Import comprehensive logger (defined in logger.py to avoid circular imports)
# This is a placeholder that will be replaced at runtime
LOGGER = None

def _init_logger():
    """Initialize the global logger instance."""
    global LOGGER
    if LOGGER is None:
        try:
            from lib.logger import get_logger
            LOGGER = get_logger("tesla_ble")
        except ImportError:
            # Fallback to simple logger if logger module not available
            class SimpleLogger:
                def debug(self, msg): print("[DEBUG] tesla_ble:", msg)
                def info(self, msg): print("[INFO] tesla_ble:", msg)
                def warning(self, msg): print("[WARNING] tesla_ble:", msg)
                def error(self, msg): print("[ERROR] tesla_ble:", msg)
                def set_level(self, level): pass
                def enable_uart(self, enabled): pass
                def enable_file(self, enabled, path=None): pass
            LOGGER = SimpleLogger()
    return LOGGER

# Initialize logger on module import
_init_logger()