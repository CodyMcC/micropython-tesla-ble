# Car Server protobuf definitions for MicroPython
# Based on Tesla Fleet API car_server.proto
from .base import ProtobufMessage

# Enums matching Tesla Fleet API
class OperationStatus_E:
    OPERATIONSTATUS_OK = 0
    OPERATIONSTATUS_ERROR = 1

# Message classes matching Tesla Fleet API structure
class GetVehicleData(ProtobufMessage):
    """Get vehicle data request - matches Tesla Fleet API GetVehicleData"""
    
    def __init__(self):
        super().__init__()
        # Field numbers match Tesla Fleet API proto definition
        self._define_field('getChargeState', 2, 'GetChargeState')
        self._define_field('getClimateState', 3, 'GetClimateState')
        self._define_field('getDriveState', 4, 'GetDriveState')
        self._define_field('getLocationState', 7, 'GetLocationState')
        self._define_field('getClosuresState', 8, 'GetClosuresState')
        self._define_field('getChargeScheduleState', 10, 'GetChargeScheduleState')
        self._define_field('getPreconditioningScheduleState', 11, 'GetPreconditioningScheduleState')
        self._define_field('getTirePressureState', 14, 'GetTirePressureState')
        self._define_field('getMediaState', 15, 'GetMediaState')
        self._define_field('getMediaDetailState', 16, 'GetMediaDetailState')
        self._define_field('getSoftwareUpdateState', 17, 'GetSoftwareUpdateState')
        self._define_field('getParentalControlsState', 19, 'GetParentalControlsState')

class GetChargeState(ProtobufMessage):
    """Get charge state request"""
    
    def __init__(self):
        super().__init__()

class GetClimateState(ProtobufMessage):
    """Get climate state request"""
    
    def __init__(self):
        super().__init__()

class GetDriveState(ProtobufMessage):
    """Get drive state request"""
    
    def __init__(self):
        super().__init__()

class GetLocationState(ProtobufMessage):
    """Get location state request"""
    
    def __init__(self):
        super().__init__()

class GetClosuresState(ProtobufMessage):
    """Get closures state request"""
    
    def __init__(self):
        super().__init__()

class GetChargeScheduleState(ProtobufMessage):
    """Get charge schedule state request"""
    
    def __init__(self):
        super().__init__()

class GetPreconditioningScheduleState(ProtobufMessage):
    """Get preconditioning schedule state request"""
    
    def __init__(self):
        super().__init__()

class GetTirePressureState(ProtobufMessage):
    """Get tire pressure state request"""
    
    def __init__(self):
        super().__init__()

class GetMediaState(ProtobufMessage):
    """Get media state request"""
    
    def __init__(self):
        super().__init__()

class GetMediaDetailState(ProtobufMessage):
    """Get media detail state request"""
    
    def __init__(self):
        super().__init__()

class GetSoftwareUpdateState(ProtobufMessage):
    """Get software update state request"""
    
    def __init__(self):
        super().__init__()

class GetParentalControlsState(ProtobufMessage):
    """Get parental controls state request"""
    
    def __init__(self):
        super().__init__()

class VehicleAction(ProtobufMessage):
    """Vehicle action container - matches Tesla Fleet API VehicleAction"""
    
    def __init__(self):
        super().__init__()
        # Field numbers match Tesla Fleet API proto definition
        self._define_field('getVehicleData', 1, GetVehicleData, oneof_group='vehicle_action_msg')
        # Additional actions can be added as needed
        self._define_field('remoteStartDrive', 2, 'RemoteStartDrive', oneof_group='vehicle_action_msg')
        self._define_field('chargingSetLimitAction', 5, 'ChargingSetLimitAction', oneof_group='vehicle_action_msg')
        self._define_field('chargingStartStopAction', 6, 'ChargingStartStopAction', oneof_group='vehicle_action_msg')
        self._define_field('hvacAutoAction', 10, 'HvacAutoAction', oneof_group='vehicle_action_msg')
        self._define_field('vehicleControlFlashLightsAction', 26, 'VehicleControlFlashLightsAction', oneof_group='vehicle_action_msg')
        self._define_field('vehicleControlHonkHornAction', 27, 'VehicleControlHonkHornAction', oneof_group='vehicle_action_msg')
        self._define_field('chargePortDoorClose', 61, 'ChargePortDoorClose', oneof_group='vehicle_action_msg')
        self._define_field('chargePortDoorOpen', 62, 'ChargePortDoorOpen', oneof_group='vehicle_action_msg')

class Action(ProtobufMessage):
    """Action container - matches Tesla Fleet API Action"""
    
    def __init__(self):
        super().__init__()
        self._define_field('vehicleAction', 2, VehicleAction, oneof_group='action_msg')

class ResultReason(ProtobufMessage):
    """Result reason - matches Tesla Fleet API ResultReason"""
    
    def __init__(self):
        super().__init__()
        self._define_field('plain_text', 1, 'string', oneof_group='reason')

class ActionStatus(ProtobufMessage):
    """Action status - matches Tesla Fleet API ActionStatus"""
    
    def __init__(self):
        super().__init__()
        self._define_field('result', 1, int)
        self._define_field('result_reason', 2, ResultReason)

class Response(ProtobufMessage):
    """Response container - matches Tesla Fleet API Response"""
    
    def __init__(self):
        super().__init__()
        self._define_field('actionStatus', 1, ActionStatus)
        # Additional response fields can be added as needed
        # self._define_field('vehicleData', 2, VehicleData)

# Simple action message classes
class RemoteStartDrive(ProtobufMessage):
    """Remote start drive action"""
    
    def __init__(self):
        super().__init__()

class ChargingSetLimitAction(ProtobufMessage):
    """Charging set limit action"""
    
    def __init__(self):
        super().__init__()
        self._define_field('percent', 1, 'int32')

class ChargingStartStopAction(ProtobufMessage):
    """Charging start/stop action"""
    
    def __init__(self):
        super().__init__()
        # Oneof charging_action fields would be defined here

class HvacAutoAction(ProtobufMessage):
    """HVAC auto action"""
    
    def __init__(self):
        super().__init__()
        self._define_field('power_on', 1, 'bool')
        self._define_field('manual_override', 2, 'bool')

class VehicleControlFlashLightsAction(ProtobufMessage):
    """Vehicle control flash lights action"""
    
    def __init__(self):
        super().__init__()

class VehicleControlHonkHornAction(ProtobufMessage):
    """Vehicle control honk horn action"""
    
    def __init__(self):
        super().__init__()

class ChargePortDoorClose(ProtobufMessage):
    """Charge port door close action"""
    
    def __init__(self):
        super().__init__()

class ChargePortDoorOpen(ProtobufMessage):
    """Charge port door open action"""
    
    def __init__(self):
        super().__init__()