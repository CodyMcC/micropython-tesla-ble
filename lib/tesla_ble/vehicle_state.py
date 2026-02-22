"""Minimal vehicle state data structure for body-controller-state responses.

This module defines a simple VehicleState class that holds the parsed
vehicle status information from body-controller-state commands.
"""


class VehicleState:
    """Vehicle state from body-controller-state command.
    
    This class holds all the information returned by the body-controller-state
    command, including closure statuses for all doors/trunks/charge port,
    vehicle lock state, sleep status, and user presence.
    
    Attributes:
        front_driver_door: Front driver door state ("OPEN", "CLOSED", "AJAR", etc.)
        front_passenger_door: Front passenger door state
        rear_driver_door: Rear driver door state
        rear_passenger_door: Rear passenger door state
        front_trunk: Front trunk (frunk) state
        rear_trunk: Rear trunk state
        charge_port: Charge port state
        tonneau: Tonneau cover state (Cybertruck only)
        lock_state: Vehicle lock state ("LOCKED", "UNLOCKED", etc.)
        sleep_status: Vehicle sleep status ("AWAKE", "ASLEEP", etc.)
        user_presence: User presence status ("PRESENT", "NOT_PRESENT", etc.)
    """
    
    def __init__(self):
        """Initialize empty vehicle state."""
        # Closure statuses
        self.front_driver_door = None
        self.front_passenger_door = None
        self.rear_driver_door = None
        self.rear_passenger_door = None
        self.front_trunk = None
        self.rear_trunk = None
        self.charge_port = None
        self.tonneau = None
        
        # Vehicle status
        self.lock_state = None
        self.sleep_status = None
        self.user_presence = None
    
    @property
    def all_doors_closed(self):
        """Check if all doors are closed.
        
        Returns:
            bool: True if all doors are closed, False otherwise.
                  Returns None if any door status is unknown.
        """
        doors = [
            self.front_driver_door,
            self.front_passenger_door,
            self.rear_driver_door,
            self.rear_passenger_door
        ]
        
        # If any door is None, we can't determine
        if any(d is None for d in doors):
            return None
        
        # All doors must be "CLOSED"
        return all(d == "CLOSED" for d in doors)
    def any_doors_open(self):
        """Check if any door is open.

        Returns:
            bool: True if any door is open, False if all doors are closed.
                  Returns None if any door status is unknown.
        """
        doors = [
            self.front_driver_door,
            self.front_passenger_door,
            self.rear_driver_door,
            self.rear_passenger_door
        ]

        # If any door is None, we can't determine
        if any(d is None for d in doors):
            return None

        # Check if any door is "OPEN"
        return any(d == "OPEN" for d in doors)
    def update_from_response(self, new_state):
        """Update state with new values, retaining last known values for None fields.

        This method implements stateful update logic: only non-None fields from
        new_state are used to update the current state. Fields that are None in
        new_state retain their previous values.

        Args:
            new_state: VehicleState instance from parsed response

        Returns:
            dict: Dictionary of fields that changed, mapping field_name to (old_value, new_value)

        Raises:
            TypeError: If new_state is not a VehicleState instance
        """
        if not isinstance(new_state, VehicleState):
            raise TypeError("new_state must be VehicleState instance")

        changes = {}

        # List of all fields to update
        fields = [
            'front_driver_door',
            'front_passenger_door',
            'rear_driver_door',
            'rear_passenger_door',
            'front_trunk',
            'rear_trunk',
            'charge_port',
            'tonneau',
            'lock_state',
            'sleep_status',
            'user_presence'
        ]

        # Update each field if new value is not None
        for field in fields:
            new_value = getattr(new_state, field)

            # Only update if new value is not None
            if new_value is not None:
                old_value = getattr(self, field)

                # Track change if value actually changed
                if old_value != new_value:
                    changes[field] = (old_value, new_value)
                    setattr(self, field, new_value)

        return changes

    
    @property
    def is_locked(self):
        """Check if vehicle is locked.
        
        Returns:
            bool: True if vehicle is locked (LOCKED or INTERNAL_LOCKED), False otherwise.
                  Returns None if lock state is unknown.
        """
        if self.lock_state is None:
            return None
        
        return self.lock_state in ("LOCKED", "INTERNAL_LOCKED")
    
    def __str__(self):
        """Format vehicle state for display.
        
        Returns:
            str: Formatted vehicle state information
        """
        lines = []
        
        # Closure statuses
        lines.append("Closure Statuses:")
        
        closure_fields = [
            ('front_driver_door', 'Front Driver Door'),
            ('front_passenger_door', 'Front Passenger Door'),
            ('rear_driver_door', 'Rear Driver Door'),
            ('rear_passenger_door', 'Rear Passenger Door'),
            ('front_trunk', 'Front Trunk'),
            ('rear_trunk', 'Rear Trunk'),
            ('charge_port', 'Charge Port'),
            ('tonneau', 'Tonneau'),
        ]
        
        for field, label in closure_fields:
            value = getattr(self, field)
            if value is not None:
                lines.append("  {}: {}".format(label, value))
        
        # Vehicle status
        lines.append("")
        lines.append("Vehicle Status:")
        
        if self.lock_state is not None:
            lines.append("  Lock State: {}".format(self.lock_state))
        
        if self.sleep_status is not None:
            lines.append("  Sleep Status: {}".format(self.sleep_status))
        
        if self.user_presence is not None:
            lines.append("  User Presence: {}".format(self.user_presence))
        
        # Quick check properties
        lines.append("")
        lines.append("Quick Check:")
        
        any_open = self.any_doors_open()
        if any_open is not None:
            lines.append("  Any Doors Open: {}".format("YES" if any_open else "NO"))
        
        all_closed = self.all_doors_closed
        if all_closed is not None:
            lines.append("  All Doors Closed: {}".format("YES" if all_closed else "NO"))
        
        locked = self.is_locked
        if locked is not None:
            lines.append("  Vehicle Locked: {}".format("YES" if locked else "NO"))
        
        return "\n".join(lines)
    
    def __repr__(self):
        """Return representation of vehicle state.
        
        Returns:
            str: String representation
        """
        return "VehicleState(lock={}, sleep={}, all_doors_closed={})".format(
            self.lock_state,
            self.sleep_status,
            self.all_doors_closed
        )
    
    @classmethod
    def from_parsed_state(cls, parsed_state):
        """Create VehicleState from parsed state dictionary.
        
        Args:
            parsed_state: Dictionary from minimal_parser.parse_body_controller_state()
        
        Returns:
            VehicleState: New VehicleState instance with populated fields
        """
        state = cls()
        
        # Copy closure statuses
        closure_statuses = parsed_state.get('closure_statuses', {})
        state.front_driver_door = closure_statuses.get('front_driver_door')
        state.front_passenger_door = closure_statuses.get('front_passenger_door')
        state.rear_driver_door = closure_statuses.get('rear_driver_door')
        state.rear_passenger_door = closure_statuses.get('rear_passenger_door')
        state.front_trunk = closure_statuses.get('front_trunk')
        state.rear_trunk = closure_statuses.get('rear_trunk')
        state.charge_port = closure_statuses.get('charge_port')
        state.tonneau = closure_statuses.get('tonneau')
        
        # Copy vehicle status
        state.lock_state = parsed_state.get('lock_state')
        state.sleep_status = parsed_state.get('sleep_status')
        state.user_presence = parsed_state.get('user_presence')
        
        return state
