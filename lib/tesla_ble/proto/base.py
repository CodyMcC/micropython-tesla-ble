"""Base protobuf classes for MicroPython compatibility."""

try:
    import ustruct as struct
    import ujson as json
except ImportError:
    import struct
    import json

# Note: LOGGER removed - base.py is now self-contained

class ProtobufError(Exception):
    """Base exception for protobuf operations."""
    pass

class DecodeError(ProtobufError):
    """Error during protobuf decoding."""
    pass

class EncodeError(ProtobufError):
    """Error during protobuf encoding."""
    pass

class ProtobufMessage:
    """Base class for MicroPython-compatible protobuf messages."""
    
    def __init__(self, **kwargs):
        """Initialize message with field values."""
        self._fields = {}
        self._field_types = {}
        self._field_numbers = {}
        self._oneof_groups = {}
        
        # Set provided field values
        for key, value in kwargs.items():
            self.set_field(key, value)
    
    def _define_field(self, name, field_number, field_type, oneof_group=None, repeated=False):
        """Define a field in the message schema.
        
        Args:
            name: Field name
            field_number: Protobuf field number
            field_type: Field type (int, str, bytes, or message class)
            oneof_group: Optional oneof group name
            repeated: Whether field is repeated (list)
        """
        self._field_types[name] = field_type
        self._field_numbers[name] = field_number
        
        if oneof_group:
            if oneof_group not in self._oneof_groups:
                self._oneof_groups[oneof_group] = []
            self._oneof_groups[oneof_group].append(name)
        
        # Initialize repeated fields as empty lists
        if repeated and name not in self._fields:
            self._fields[name] = []
    
    def set_field(self, name, value):
        """Set a field value."""
        self._fields[name] = value
    
    def get_field(self, name, default=None):
        """Get a field value."""
        return self._fields.get(name, default)
    
    def has_field(self, name):
        """Check if field exists and has a value."""
        return name in self._fields and self._fields[name] is not None
    
    def clear_field(self, name):
        """Clear a field value."""
        if name in self._fields:
            del self._fields[name]
    
    def serialize_to_string(self):
        """Serialize message to bytes (simplified implementation)."""
        try:
            # Convert to JSON and encode as bytes for simplicity
            # In a full implementation, this would use proper protobuf encoding
            json_str = json.dumps(self._fields)
            return json_str.encode('utf-8')
        except Exception as e:
            raise EncodeError("Failed to serialize message: {}".format(e))
    
    def parse_from_string(self, data):
        """Parse message from bytes (simplified implementation)."""
        try:
            # Decode from JSON for simplicity
            # In a full implementation, this would use proper protobuf decoding
            if isinstance(data, bytes):
                json_str = data.decode('utf-8')
            else:
                json_str = data
            
            self._fields = json.loads(json_str)
        except Exception as e:
            raise DecodeError("Failed to parse message: {}".format(e))
    
    def __getattr__(self, name):
        """Allow field access as attributes."""
        if name.startswith('_'):
            raise AttributeError("'{}' object has no attribute '{}'".format(
                self.__class__.__name__, name))
        return self.get_field(name)
    
    def __setattr__(self, name, value):
        """Allow field setting as attributes."""
        if name.startswith('_') or name in ['serialize_to_string', 'parse_from_string']:
            super().__setattr__(name, value)
        else:
            self.set_field(name, value)
    
    def __str__(self):
        """String representation of message."""
        return "{}({})".format(
            self.__class__.__name__, 
            ', '.join("{}={}".format(k, repr(v)) for k, v in self._fields.items())
        )

class RoutableMessage(ProtobufMessage):
    """Tesla BLE routable message."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize common fields
        if 'to_destination' not in self._fields:
            self._fields['to_destination'] = {}
        if 'from_destination' not in self._fields:
            self._fields['from_destination'] = {}

class Destination(ProtobufMessage):
    """Message destination."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SessionInfoRequest(ProtobufMessage):
    """Session info request message."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class UnsignedMessage(ProtobufMessage):
    """Unsigned message for vehicle security."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Action(ProtobufMessage):
    """Action message for infotainment."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Utility functions for message handling
def create_message_from_dict(message_class, data_dict):
    """Create a protobuf message from a dictionary."""
    try:
        message = message_class()
        for key, value in data_dict.items():
            message.set_field(key, value)
        return message
    except Exception as e:
        raise ProtobufError("Failed to create message: {}".format(e))

def message_to_dict(message):
    """Convert a protobuf message to a dictionary."""
    try:
        return dict(message._fields)
    except Exception as e:
        raise ProtobufError("Failed to convert message: {}".format(e))