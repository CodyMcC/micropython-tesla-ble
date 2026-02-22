# Signatures protobuf definitions for MicroPython
# Based on Tesla Fleet API signatures.proto
from .base import ProtobufMessage

# Enums matching Tesla Fleet API
class SignatureType_E:
    SIGNATURE_TYPE_NONE = 0
    SIGNATURE_TYPE_ECDSA_SHA256 = 1
    SIGNATURE_TYPE_HMAC_SHA256 = 2

# Message classes
class SignatureData(ProtobufMessage):
    """Signature data message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('signer_identity', 1, 'bytes')
        self._define_field('ECDSA_signature_DER', 2, 'bytes')
        self._define_field('HMAC_signature', 3, 'bytes')

class SessionInfo(ProtobufMessage):
    """Session info message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('counter', 1, 'uint32')
        self._define_field('publicKey', 2, 'bytes')
        self._define_field('epoch', 3, 'bytes')
        self._define_field('clock_time', 4, 'uint32')
        self._define_field('status', 5, int)