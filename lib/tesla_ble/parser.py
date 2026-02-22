"""Minimal protobuf parser for body-controller-state responses.

This module parses body-controller-state responses from Tesla vehicles
without requiring authentication. It extracts closure statuses, lock state,
sleep status, and user presence.

Based on the official Tesla vehicle-command implementation.
"""

try:
    import ubinascii as binascii
    import ustruct as struct
except ImportError:
    import binascii
    import struct

from .vehicle_state import VehicleState


# Enum to string mappings (from VCSEC proto)
# NOTE: The actual values sent by the vehicle differ from the protobuf definition!
# Vehicle sends: 1=OPEN, 2=CLOSED (verified against tesla-control output)
CLOSURE_STATE_NAMES = {
    0: "UNKNOWN",
    1: "OPEN",      # Vehicle sends 1 for OPEN (not CLOSED as in proto)
    2: "CLOSED",    # Vehicle sends 2 for CLOSED (not OPEN as in proto)
    3: "AJAR",
    4: "FAILED_UNLATCH",
    5: "OPENING",
    6: "CLOSING",
}

LOCK_STATE_NAMES = {
    0: "UNLOCKED",
    1: "LOCKED",
    2: "INTERNAL_LOCKED",
    3: "SELECTIVE_UNLOCKED",
}

SLEEP_STATUS_NAMES = {
    0: "UNKNOWN",
    1: "AWAKE",
    2: "ASLEEP",
}

USER_PRESENCE_NAMES = {
    0: "UNKNOWN",
    1: "NOT_PRESENT",
    2: "PRESENT",
}


def _read_varint(data, offset):
    """Read a protobuf varint from data at offset.
    
    Returns:
        tuple: (value, new_offset)
    """
    result = 0
    shift = 0
    pos = offset
    
    while pos < len(data):
        byte = data[pos]
        result |= (byte & 0x7F) << shift
        pos += 1
        
        if (byte & 0x80) == 0:
            return result, pos
        
        shift += 7
    
    raise ValueError("Incomplete varint at offset {}".format(offset))


def _parse_field(data, offset):
    """Parse a single protobuf field.
    
    Returns:
        tuple: (field_num, wire_type, field_data, new_offset)
    """
    if offset >= len(data):
        raise ValueError("Offset {} beyond data length {}".format(offset, len(data)))
    
    # Read tag
    tag, offset = _read_varint(data, offset)
    field_num = tag >> 3
    wire_type = tag & 0x07
    
    # Read field data based on wire type
    if wire_type == 0:  # Varint
        value, offset = _read_varint(data, offset)
        return field_num, wire_type, value, offset
    
    elif wire_type == 2:  # Length-delimited
        length, offset = _read_varint(data, offset)
        field_data = data[offset:offset + length]
        offset += length
        return field_num, wire_type, field_data, offset
    
    else:
        raise ValueError("Unsupported wire type: {}".format(wire_type))


def _parse_message_fields(data):
    """Parse all fields in a protobuf message.
    
    Returns:
        dict: {field_num: (wire_type, field_data)}
    """
    fields = {}
    offset = 0
    
    while offset < len(data):
        try:
            field_num, wire_type, field_data, offset = _parse_field(data, offset)
            fields[field_num] = (wire_type, field_data)
        except Exception:
            break
    
    return fields


def parse_body_controller_state(response_bytes):
    """Parse body-controller-state response into VehicleState.
    
    This function manually parses the protobuf response from a body-controller-state
    command and extracts all vehicle status information.
    
    Args:
        response_bytes: Raw response bytes from vehicle (with 0x32 prefix)
    
    Returns:
        VehicleState: Parsed vehicle state object
    
    Raises:
        ValueError: If response cannot be decoded
    """
    if not isinstance(response_bytes, (bytes, bytearray)):
        raise ValueError("Response must be bytes, got {}".format(type(response_bytes)))
    
    if len(response_bytes) == 0:
        raise ValueError("Response is empty")
    
    # Parse RoutableMessage (outer message)
    routable_fields = _parse_message_fields(response_bytes)
    
    # Extract field 10 (protobuf_message_as_bytes)
    if 10 not in routable_fields:
        raise ValueError("RoutableMessage missing field 10 (protobuf_message_as_bytes)")
    
    wire_type, inner_bytes = routable_fields[10]
    
    # Parse FromVCSECMessage (inner message)
    from_vcsec_fields = _parse_message_fields(inner_bytes)
    
    # The vehicleStatus can be in different fields:
    # - Field 1: Simple format with individual closure fields (tesla-control format)
    # - Field 3: Alternate format with encrypted blob (what we're getting)
    vehicle_status_bytes = None
    use_field_1_format = False
    
    if 1 in from_vcsec_fields:
        # Field 1 format (tesla-control style)
        wire_type, vehicle_status_bytes = from_vcsec_fields[1]
        use_field_1_format = True
    elif 3 in from_vcsec_fields:
        # Field 3 format (encrypted blob style)
        wire_type, vehicle_status_bytes = from_vcsec_fields[3]
        use_field_1_format = False
    else:
        available_fields = list(from_vcsec_fields.keys())
        raise ValueError("FromVCSECMessage missing vehicleStatus. Available fields: {}".format(available_fields))
    
    # Parse VehicleStatus - this is where the nested structure is
    vehicle_status_fields = _parse_message_fields(vehicle_status_bytes)
    
    # Create VehicleState object
    state = VehicleState()
    
    # Handle field 1 format (tesla-control style - proper closure data)
    if use_field_1_format:
        # Initialize all doors as CLOSED (default value in protobuf)
        # Protobuf omits fields with default values, so missing = CLOSED
        state.front_driver_door = "CLOSED"
        state.front_passenger_door = "CLOSED"
        state.rear_driver_door = "CLOSED"
        state.rear_passenger_door = "CLOSED"
        state.front_trunk = "CLOSED"
        state.rear_trunk = "CLOSED"
        state.charge_port = "CLOSED"
        state.tonneau = "CLOSED"  # Default for Cybertruck
        
        # Field 1 in VehicleStatus contains the closure data directly
        if 1 in vehicle_status_fields:
            wire_type, closure_data = vehicle_status_fields[1]
            
            # Parse the closure data as a protobuf message
            # Each field represents a door/closure:
            # Field 1: frontDriverDoor
            # Field 2: frontPassengerDoor
            # Field 3: rearDriverDoor
            # Field 4: rearPassengerDoor
            # Field 5: rearTrunk
            # Field 6: frontTrunk
            # Field 7: chargePort
            # Field 8: tonneau
            closure_fields = _parse_message_fields(closure_data)
            
            # Update only the fields that are present (non-default values)
            if 1 in closure_fields:
                wire_type, value = closure_fields[1]
                state.front_driver_door = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 2 in closure_fields:
                wire_type, value = closure_fields[2]
                state.front_passenger_door = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 3 in closure_fields:
                wire_type, value = closure_fields[3]
                state.rear_driver_door = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 4 in closure_fields:
                wire_type, value = closure_fields[4]
                state.rear_passenger_door = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 5 in closure_fields:
                wire_type, value = closure_fields[5]
                state.rear_trunk = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 6 in closure_fields:
                wire_type, value = closure_fields[6]
                state.front_trunk = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 7 in closure_fields:
                wire_type, value = closure_fields[7]
                state.charge_port = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
            
            if 8 in closure_fields:
                wire_type, value = closure_fields[8]
                state.tonneau = CLOSURE_STATE_NAMES.get(value, "UNKNOWN")
        
        # Lock state can be in Field 2 or Field 7 (varint)
        # Field 2: Uses VehicleLockState_E enum (0=UNLOCKED, 1=LOCKED, 2=INTERNAL_LOCKED, 3=SELECTIVE_UNLOCKED)
        # Field 7: Undocumented field, appears to use inverted boolean (0=LOCKED, 1=UNLOCKED)
        if 2 in vehicle_status_fields:
            wire_type, lock_value = vehicle_status_fields[2]
            if wire_type == 0:  # Varint
                state.lock_state = LOCK_STATE_NAMES.get(lock_value, "UNKNOWN")
        elif 7 in vehicle_status_fields:
            wire_type, lock_value = vehicle_status_fields[7]
            if wire_type == 0:  # Varint
                # Field 7 uses inverted logic: 0=LOCKED, 1=UNLOCKED
                if lock_value == 0:
                    state.lock_state = "LOCKED"
                elif lock_value == 1:
                    state.lock_state = "UNLOCKED"
                else:
                    state.lock_state = "UNKNOWN"
        
        # Field 3 is sleep status (varint)
        if 3 in vehicle_status_fields:
            wire_type, sleep_value = vehicle_status_fields[3]
            if wire_type == 0:  # Varint
                state.sleep_status = SLEEP_STATUS_NAMES.get(sleep_value, "UNKNOWN")
        
        # Field 4 is user presence (varint)
        if 4 in vehicle_status_fields:
            wire_type, presence_value = vehicle_status_fields[4]
            if wire_type == 0:  # Varint
                state.user_presence = USER_PRESENCE_NAMES.get(presence_value, "UNKNOWN")
    
    else:
        # Field 3 format (encrypted blob style - what we're currently getting)
        # Field 2 in VehicleStatus can be:
        # - A varint (wire_type=0) for vehicleLockState
        # - A nested message (wire_type=2) containing closure data
        if 2 in vehicle_status_fields:
            wire_type, field_2_data = vehicle_status_fields[2]
            
            if wire_type == 0:  # Varint - this is vehicleLockState
                state.lock_state = LOCK_STATE_NAMES.get(field_2_data, "UNKNOWN")
            
            elif wire_type == 2:  # Length-delimited - nested message with closure data
                # Parse the nested message
                nested_fields = _parse_message_fields(field_2_data)
                
                # Field 1 in the nested message contains the closure blob (20 bytes)
                # This blob is encrypted/obfuscated and cannot be decoded without
                # additional information. Mark all closure fields as UNKNOWN.
                if 1 in nested_fields:
                    # Blob present but cannot be decoded
                    pass
                
                # Field 3 in the nested message might be lock state
                if 3 in nested_fields:
                    lock_wire_type, lock_value = nested_fields[3]
                    if lock_wire_type == 0:  # Varint
                        state.lock_state = LOCK_STATE_NAMES.get(lock_value, "UNKNOWN")
        
        # Field 3 in VehicleStatus is vehicleSleepStatus
        if 3 in vehicle_status_fields:
            wire_type, raw_value = vehicle_status_fields[3]
            if wire_type == 0:  # Varint
                state.sleep_status = SLEEP_STATUS_NAMES.get(raw_value, "UNKNOWN")
        
        # Field 4 in VehicleStatus can be userPresence
        if 4 in vehicle_status_fields:
            wire_type, field_4_data = vehicle_status_fields[4]
            
            if wire_type == 0:  # Varint
                state.user_presence = USER_PRESENCE_NAMES.get(field_4_data, "UNKNOWN")
            elif wire_type == 2:  # Length-delimited - might contain a single byte
                if len(field_4_data) == 1:
                    state.user_presence = USER_PRESENCE_NAMES.get(field_4_data[0], "UNKNOWN")
    
    return state
