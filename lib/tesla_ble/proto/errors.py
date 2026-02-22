# Errors protobuf definitions for MicroPython
# Based on Tesla Fleet API errors.proto
from .base import ProtobufMessage

# Enums matching Tesla Fleet API
class NominalError_E:
    ERROR_NONE = 0
    ERROR_NOT_IMPLEMENTED = 1
    ERROR_INVALID_REQUEST = 2
    ERROR_INTERNAL = 3
    ERROR_TIMEOUT = 4
    ERROR_BUSY = 5
    ERROR_UNAUTHORIZED = 6
    ERROR_FORBIDDEN = 7
    ERROR_NOT_FOUND = 8
    ERROR_CONFLICT = 9
    ERROR_RATE_LIMITED = 10

# Message classes
class NominalError(ProtobufMessage):
    """Nominal error message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('error', 1, int)
        self._define_field('details', 2, 'string')