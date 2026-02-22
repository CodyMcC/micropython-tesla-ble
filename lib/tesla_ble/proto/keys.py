# Keys protobuf definitions for MicroPython
# Based on Tesla Fleet API keys.proto
from .base import ProtobufMessage

# Enums matching Tesla Fleet API
class Role:
    ROLE_NONE = 0
    ROLE_SERVICE = 1
    ROLE_OWNER = 2
    ROLE_DRIVER = 3

class KeyType_E:
    KEY_TYPE_NONE = 0
    KEY_TYPE_NFC = 1
    KEY_TYPE_BLE = 2
    KEY_TYPE_CLOUD = 3

# Message classes
class PublicKey(ProtobufMessage):
    """Public key message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('PublicKeyRaw', 1, 'bytes')

class PrivateKey(ProtobufMessage):
    """Private key message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('PrivateKeyRaw', 1, 'bytes')

class KeyPair(ProtobufMessage):
    """Key pair message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('publicKey', 1, PublicKey)
        self._define_field('privateKey', 2, PrivateKey)