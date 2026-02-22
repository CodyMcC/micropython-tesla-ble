# Universal Message protobuf definitions for MicroPython
# Based on Tesla Fleet API universal_message.proto
from .base import ProtobufMessage

# Enums matching Tesla Fleet API
class Domain:
    DOMAIN_BROADCAST = 0
    DOMAIN_VEHICLE_SECURITY = 2
    DOMAIN_INFOTAINMENT = 3

class OperationStatus_E:
    OPERATIONSTATUS_OK = 0
    OPERATIONSTATUS_WAIT = 1
    OPERATIONSTATUS_ERROR = 2

class MessageFault_E:
    MESSAGEFAULT_ERROR_NONE = 0
    MESSAGEFAULT_ERROR_BUSY = 1
    MESSAGEFAULT_ERROR_TIMEOUT = 2
    MESSAGEFAULT_ERROR_UNKNOWN_KEY_ID = 3
    MESSAGEFAULT_ERROR_INACTIVE_KEY = 4
    MESSAGEFAULT_ERROR_INVALID_SIGNATURE = 5
    MESSAGEFAULT_ERROR_INVALID_TOKEN_OR_COUNTER = 6
    MESSAGEFAULT_ERROR_INSUFFICIENT_PRIVILEGES = 7
    MESSAGEFAULT_ERROR_INVALID_DOMAINS = 8
    MESSAGEFAULT_ERROR_INVALID_COMMAND = 9
    MESSAGEFAULT_ERROR_DECODING = 10
    MESSAGEFAULT_ERROR_INTERNAL = 11
    MESSAGEFAULT_ERROR_WRONG_PERSONALIZATION = 12
    MESSAGEFAULT_ERROR_BAD_PARAMETER = 13
    MESSAGEFAULT_ERROR_KEYCHAIN_IS_FULL = 14
    MESSAGEFAULT_ERROR_INCORRECT_EPOCH = 15
    MESSAGEFAULT_ERROR_IV_INCORRECT_LENGTH = 16
    MESSAGEFAULT_ERROR_TIME_EXPIRED = 17
    MESSAGEFAULT_ERROR_NOT_PROVISIONED_WITH_IDENTITY = 18
    MESSAGEFAULT_ERROR_COULD_NOT_HASH_METADATA = 19
    MESSAGEFAULT_ERROR_TIME_TO_LIVE_TOO_LONG = 20
    MESSAGEFAULT_ERROR_REMOTE_ACCESS_DISABLED = 21
    MESSAGEFAULT_ERROR_REMOTE_SERVICE_ACCESS_DISABLED = 22
    MESSAGEFAULT_ERROR_COMMAND_REQUIRES_ACCOUNT_CREDENTIALS = 23
    MESSAGEFAULT_ERROR_REQUEST_MTU_EXCEEDED = 24
    MESSAGEFAULT_ERROR_RESPONSE_MTU_EXCEEDED = 25
    MESSAGEFAULT_ERROR_REPEATED_COUNTER = 26
    MESSAGEFAULT_ERROR_INVALID_KEY_HANDLE = 27
    MESSAGEFAULT_ERROR_REQUIRES_RESPONSE_ENCRYPTION = 28

class Flags:
    FLAG_USER_COMMAND = 0
    FLAG_ENCRYPT_RESPONSE = 1

class Destination(ProtobufMessage):
    """Destination message for routing"""
    
    def __init__(self):
        super().__init__()
        self._define_field('domain', 1, int, oneof_group='sub_destination')
        self._define_field('routing_address', 2, 'bytes', oneof_group='sub_destination')

class MessageStatus(ProtobufMessage):
    """Message status information"""
    
    def __init__(self):
        super().__init__()
        self._define_field('operation_status', 1, int)
        self._define_field('signed_message_fault', 2, int)

class SessionInfoRequest(ProtobufMessage):
    """Session info request message"""
    
    def __init__(self):
        super().__init__()
        self._define_field('public_key', 1, 'bytes')
        self._define_field('challenge', 2, 'bytes')

class RoutableMessage(ProtobufMessage):
    """Main routable message container - matches Tesla Fleet API RoutableMessage"""
    
    def __init__(self):
        super().__init__()
        # Field numbers match the Tesla Fleet API proto definition
        self._define_field('to_destination', 6, Destination)
        self._define_field('from_destination', 7, Destination)
        
        # Oneof payload fields
        self._define_field('protobuf_message_as_bytes', 10, 'bytes', oneof_group='payload')
        self._define_field('session_info_request', 14, SessionInfoRequest, oneof_group='payload')
        self._define_field('session_info', 15, 'bytes', oneof_group='payload')
        
        # Signature data (oneof sub_sigData) - simplified for now
        # self._define_field('signature_data', 13, SignatureData, oneof_group='sub_sigData')
        
        # Other fields
        self._define_field('signedMessageStatus', 12, MessageStatus)
        self._define_field('request_uuid', 50, 'bytes')
        self._define_field('uuid', 51, 'bytes')
        self._define_field('flags', 52, 'uint32')