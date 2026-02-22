# Tesla BLE Protobuf Definitions
# This package contains all protobuf message definitions for Tesla BLE protocol

# Import all proto modules for convenient access
try:
    # MicroPython
    from . import base
    from . import car_server
    from . import universal_message
    from . import vcsec
    from . import errors
    from . import keys
    from . import signatures
except ImportError:
    # CPython fallback
    pass

__all__ = [
    'base',
    'car_server',
    'universal_message',
    'vcsec',
    'errors',
    'keys',
    'signatures',
]
