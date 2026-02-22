# VCSEC protobuf definitions for MicroPython
# Based on Tesla Fleet API vcsec.proto
from .base import ProtobufMessage

# Enums
class SignatureType:
    SIGNATURE_TYPE_NONE = 0
    SIGNATURE_TYPE_PRESENT_KEY = 2

class KeyFormFactor:
    KEY_FORM_FACTOR_UNKNOWN = 0
    KEY_FORM_FACTOR_NFC_CARD = 1
    KEY_FORM_FACTOR_3_BUTTON_BLE_CAR_KEYFOB = 2
    KEY_FORM_FACTOR_BLE_DEVICE = 3
    KEY_FORM_FACTOR_NFC_DEVICE = 4
    KEY_FORM_FACTOR_BLE_AND_NFC_DEVICE = 5
    KEY_FORM_FACTOR_IOS_DEVICE = 6
    KEY_FORM_FACTOR_ANDROID_DEVICE = 7
    KEY_FORM_FACTOR_3_BUTTON_BLE_CAR_KEYFOB_P60 = 8
    KEY_FORM_FACTOR_CLOUD_KEY = 9
    KEY_FORM_FACTOR_3_BUTTON_GEN2_CAR_KEYFOB_P60 = 10
    KEY_FORM_FACTOR_5_BUTTON_GEN2_CAR_KEYFOB_P60 = 11
    KEY_FORM_FACTOR_3_BUTTON_GEN2_CAR_KEYFOB_P60_V2 = 12
    KEY_FORM_FACTOR_3_BUTTON_GEN2_CAR_KEYFOB_P60_V3 = 13
    KEY_FORM_FACTOR_NFC_CARD_P71 = 14
    KEY_FORM_FACTOR_NFC_CARD_METAL_CARD = 15
    KEY_FORM_FACTOR_NFC_CARD_PLASTIC_CARD = 16
    KEY_FORM_FACTOR_APPLE_WATCH = 17

class InformationRequestType:
    INFORMATION_REQUEST_TYPE_GET_STATUS = 0
    INFORMATION_REQUEST_TYPE_GET_WHITELIST_INFO = 5
    INFORMATION_REQUEST_TYPE_GET_WHITELIST_ENTRY_INFO = 6

class RKEAction_E:
    RKE_ACTION_UNLOCK = 0
    RKE_ACTION_LOCK = 1
    RKE_ACTION_OPEN_TRUNK = 2
    RKE_ACTION_OPEN_FRUNK = 3
    RKE_ACTION_OPEN_CHARGE_PORT = 4
    RKE_ACTION_CLOSE_CHARGE_PORT = 5
    RKE_ACTION_CANCEL_EXTERNAL_AUTHENTICATE = 6
    RKE_ACTION_UNKNOWN = 19
    RKE_ACTION_REMOTE_DRIVE = 20
    RKE_ACTION_AUTO_SECURE_VEHICLE = 29
    RKE_ACTION_WAKE_VEHICLE = 30

class ClosureMoveType_E:
    CLOSURE_MOVE_TYPE_NONE = 0
    CLOSURE_MOVE_TYPE_MOVE = 1
    CLOSURE_MOVE_TYPE_STOP = 2
    CLOSURE_MOVE_TYPE_OPEN = 3
    CLOSURE_MOVE_TYPE_CLOSE = 4

class OperationStatus_E:
    OPERATIONSTATUS_OK = 0
    OPERATIONSTATUS_WAIT = 1
    OPERATIONSTATUS_ERROR = 2

class ClosureState_E:
    CLOSURESTATE_CLOSED = 0
    CLOSURESTATE_OPEN = 1
    CLOSURESTATE_AJAR = 2
    CLOSURESTATE_UNKNOWN = 3
    CLOSURESTATE_FAILED_UNLATCH = 4
    CLOSURESTATE_OPENING = 5
    CLOSURESTATE_CLOSING = 6

class VehicleLockState_E:
    VEHICLELOCKSTATE_UNLOCKED = 0
    VEHICLELOCKSTATE_LOCKED = 1
    VEHICLELOCKSTATE_INTERNAL_LOCKED = 2
    VEHICLELOCKSTATE_SELECTIVE_UNLOCKED = 3

class VehicleSleepStatus_E:
    VEHICLE_SLEEP_STATUS_UNKNOWN = 0
    VEHICLE_SLEEP_STATUS_AWAKE = 1
    VEHICLE_SLEEP_STATUS_ASLEEP = 2

class UserPresence_E:
    VEHICLE_USER_PRESENCE_UNKNOWN = 0
    VEHICLE_USER_PRESENCE_NOT_PRESENT = 1
    VEHICLE_USER_PRESENCE_PRESENT = 2

# Message classes
class SignedMessage(ProtobufMessage):
    """Signed message container"""
    
    def __init__(self):
        super().__init__()
        self._define_field('protobufMessageAsBytes', 2, 'bytes')
        self._define_field('signatureType', 3, int)

class ToVCSECMessage(ProtobufMessage):
    """Message to VCSEC"""
    
    def __init__(self):
        super().__init__()
        self._define_field('signedMessage', 1, SignedMessage)

class KeyIdentifier(ProtobufMessage):
    """Key identifier"""
    
    def __init__(self):
        super().__init__()
        self._define_field('publicKeySHA1', 1, 'bytes')

class KeyMetadata(ProtobufMessage):
    """Key metadata"""
    
    def __init__(self):
        super().__init__()
        self._define_field('keyFormFactor', 1, int)

class PublicKey(ProtobufMessage):
    """Public key"""
    
    def __init__(self):
        super().__init__()
        self._define_field('PublicKeyRaw', 1, 'bytes')

class WhitelistInfo(ProtobufMessage):
    """Whitelist information"""
    
    def __init__(self):
        super().__init__()
        self._define_field('numberOfEntries', 1, 'uint32')
        self._define_field('whitelistEntries', 2, KeyIdentifier, repeated=True)
        self._define_field('slotMask', 3, 'uint32')

class WhitelistEntryInfo(ProtobufMessage):
    """Whitelist entry information"""
    
    def __init__(self):
        super().__init__()
        self._define_field('keyId', 1, KeyIdentifier)
        self._define_field('publicKey', 2, PublicKey)
        self._define_field('metadataForKey', 4, KeyMetadata)
        self._define_field('slot', 6, 'uint32')
        self._define_field('keyRole', 7, int)  # Keys.Role enum

class InformationRequest(ProtobufMessage):
    """Information request"""
    
    def __init__(self):
        super().__init__()
        self._define_field('informationRequestType', 1, int)
        self._define_field('keyId', 2, KeyIdentifier, oneof_group='key')
        self._define_field('publicKey', 3, 'bytes', oneof_group='key')
        self._define_field('slot', 4, 'uint32', oneof_group='key')

class ClosureMoveRequest(ProtobufMessage):
    """Closure move request"""
    
    def __init__(self):
        super().__init__()
        self._define_field('frontDriverDoor', 1, int)
        self._define_field('frontPassengerDoor', 2, int)
        self._define_field('rearDriverDoor', 3, int)
        self._define_field('rearPassengerDoor', 4, int)
        self._define_field('rearTrunk', 5, int)
        self._define_field('frontTrunk', 6, int)
        self._define_field('chargePort', 7, int)
        self._define_field('tonneau', 8, int)

class PermissionChange(ProtobufMessage):
    """Permission change"""
    
    def __init__(self):
        super().__init__()
        self._define_field('key', 1, PublicKey)
        self._define_field('secondsToBeActive', 3, 'uint32')
        self._define_field('keyRole', 4, int)  # Keys.Role enum

class ReplaceKey(ProtobufMessage):
    """Replace key operation"""
    
    def __init__(self):
        super().__init__()
        self._define_field('publicKeyToReplace', 1, PublicKey, oneof_group='keyToReplace')
        self._define_field('slotToReplace', 2, 'uint32', oneof_group='keyToReplace')
        self._define_field('keyToAdd', 3, PublicKey)
        self._define_field('keyRole', 4, int)  # Keys.Role enum
        self._define_field('impermanent', 5, 'bool')

class WhitelistOperation(ProtobufMessage):
    """Whitelist operation"""
    
    def __init__(self):
        super().__init__()
        self._define_field('addPublicKeyToWhitelist', 1, PublicKey, oneof_group='sub_message')
        self._define_field('removePublicKeyFromWhitelist', 2, PublicKey, oneof_group='sub_message')
        self._define_field('addPermissionsToPublicKey', 3, PermissionChange, oneof_group='sub_message')
        self._define_field('removePermissionsFromPublicKey', 4, PermissionChange, oneof_group='sub_message')
        self._define_field('addKeyToWhitelistAndAddPermissions', 5, PermissionChange, oneof_group='sub_message')
        self._define_field('updateKeyAndPermissions', 7, PermissionChange, oneof_group='sub_message')
        self._define_field('addImpermanentKey', 8, PermissionChange, oneof_group='sub_message')
        self._define_field('addImpermanentKeyAndRemoveExisting', 9, PermissionChange, oneof_group='sub_message')
        self._define_field('removeAllImpermanentKeys', 16, 'bool', oneof_group='sub_message')
        self._define_field('replaceKey', 17, ReplaceKey, oneof_group='sub_message')
        self._define_field('metadataForKey', 6, KeyMetadata)

class WhitelistOperation_status(ProtobufMessage):
    """Whitelist operation status"""
    
    def __init__(self):
        super().__init__()
        self._define_field('whitelistOperationInformation', 1, int)  # WhitelistOperation_information_E
        self._define_field('signerOfOperation', 2, KeyIdentifier)
        self._define_field('operationStatus', 3, int)  # OperationStatus_E

class SignedMessage_status(ProtobufMessage):
    """Signed message status"""
    
    def __init__(self):
        super().__init__()
        self._define_field('counter', 1, 'uint32')
        self._define_field('signedMessageInformation', 2, int)  # SignedMessage_information_E

class CommandStatus(ProtobufMessage):
    """Command status"""
    
    def __init__(self):
        super().__init__()
        self._define_field('operationStatus', 1, int)
        self._define_field('signedMessageStatus', 2, SignedMessage_status, oneof_group='sub_message')
        self._define_field('whitelistOperationStatus', 3, WhitelistOperation_status, oneof_group='sub_message')

class UnsignedMessage(ProtobufMessage):
    """Unsigned message container"""
    
    def __init__(self):
        super().__init__()
        self._define_field('InformationRequest', 1, InformationRequest, oneof_group='sub_message')
        self._define_field('RKEAction', 2, int, oneof_group='sub_message')
        self._define_field('closureMoveRequest', 4, ClosureMoveRequest, oneof_group='sub_message')
        self._define_field('WhitelistOperation', 16, WhitelistOperation, oneof_group='sub_message')

class ClosureStatuses(ProtobufMessage):
    """Closure statuses"""
    
    def __init__(self):
        super().__init__()
        self._define_field('frontDriverDoor', 1, int)
        self._define_field('frontPassengerDoor', 2, int)
        self._define_field('rearDriverDoor', 3, int)
        self._define_field('rearPassengerDoor', 4, int)
        self._define_field('rearTrunk', 5, int)
        self._define_field('frontTrunk', 6, int)
        self._define_field('chargePort', 7, int)
        self._define_field('tonneau', 8, int)

class DetailedClosureStatus(ProtobufMessage):
    """Detailed closure status"""
    
    def __init__(self):
        super().__init__()
        self._define_field('tonneauPercentOpen', 1, 'uint32')

class VehicleStatus(ProtobufMessage):
    """Vehicle status"""
    
    def __init__(self):
        super().__init__()
        self._define_field('closureStatuses', 1, ClosureStatuses)
        self._define_field('vehicleLockState', 2, int)
        self._define_field('vehicleSleepStatus', 3, int)
        self._define_field('userPresence', 4, int)
        self._define_field('detailedClosureStatus', 5, DetailedClosureStatus)

class FromVCSECMessage(ProtobufMessage):
    """Message from VCSEC"""
    
    def __init__(self):
        super().__init__()
        self._define_field('vehicleStatus', 1, VehicleStatus, oneof_group='sub_message')
        self._define_field('commandStatus', 4, CommandStatus, oneof_group='sub_message')
        self._define_field('whitelistInfo', 16, WhitelistInfo, oneof_group='sub_message')
        self._define_field('whitelistEntryInfo', 17, WhitelistEntryInfo, oneof_group='sub_message')
        # Field 46 for nominalError - would need errors module
        # self._define_field('nominalError', 46, NominalError, oneof_group='sub_message')