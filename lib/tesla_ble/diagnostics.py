"""
Diagnostic tools for protocol analysis.

Provides utilities for analyzing protobuf messages, hex dumps, and message comparison.
Designed to work on Raspberry Pi Pico W with limited memory.
"""


class ProtobufAnalyzer:
    """
    Analyzes and displays protobuf message structure.
    
    Useful for understanding unknown message formats and comparing
    messages from different sources. Optimized for low memory usage.
    """
    
    @staticmethod
    def analyze(data, indent=0):
        """
        Recursively analyze protobuf structure.
        
        Args:
            data: Raw protobuf bytes
            indent: Indentation level for nested messages
            
        Returns:
            str: Human-readable structure description
        """
        if not data:
            return "  " * indent + "(empty)\n"
        
        result = []
        i = 0
        
        try:
            while i < len(data):
                # Read tag
                if i >= len(data):
                    break
                    
                tag = data[i]
                field_num = tag >> 3
                wire_type = tag & 0x07
                i += 1
                
                indent_str = "  " * indent
                
                # Wire type names
                wire_type_names = {
                    0: "varint",
                    1: "64-bit",
                    2: "length-delimited",
                    3: "start-group",
                    4: "end-group",
                    5: "32-bit"
                }
                wire_name = wire_type_names.get(wire_type, "unknown")
                
                if wire_type == 0:  # Varint
                    value, bytes_read = ProtobufAnalyzer._read_varint(data, i)
                    i += bytes_read
                    result.append("{}Field {}, {} = {}\n".format(
                        indent_str, field_num, wire_name, value
                    ))
                    
                elif wire_type == 1:  # 64-bit
                    if i + 8 <= len(data):
                        value_bytes = data[i:i+8]
                        result.append("{}Field {}, {} = {}\n".format(
                            indent_str, field_num, wire_name,
                            ProtobufAnalyzer._bytes_to_hex(value_bytes)
                        ))
                        i += 8
                    else:
                        result.append("{}Field {}, {} (incomplete)\n".format(
                            indent_str, field_num, wire_name
                        ))
                        break
                        
                elif wire_type == 2:  # Length-delimited
                    if i >= len(data):
                        result.append("{}Field {}, {} (no length)\n".format(
                            indent_str, field_num, wire_name
                        ))
                        break
                        
                    length, bytes_read = ProtobufAnalyzer._read_varint(data, i)
                    i += bytes_read
                    
                    if i + length > len(data):
                        result.append("{}Field {}, {} length={} (incomplete)\n".format(
                            indent_str, field_num, wire_name, length
                        ))
                        break
                    
                    field_data = data[i:i+length]
                    i += length
                    
                    # Try to parse as nested message
                    is_nested = ProtobufAnalyzer._looks_like_protobuf(field_data)
                    
                    if is_nested and length > 0:
                        result.append("{}Field {}, {} length={} (nested):\n".format(
                            indent_str, field_num, wire_name, length
                        ))
                        result.append(ProtobufAnalyzer.analyze(field_data, indent + 1))
                    else:
                        # Show as hex
                        hex_str = ProtobufAnalyzer._bytes_to_hex(field_data)
                        if len(hex_str) > 40:
                            hex_str = hex_str[:40] + "..."
                        result.append("{}Field {}, {} length={} = {}\n".format(
                            indent_str, field_num, wire_name, length, hex_str
                        ))
                        
                elif wire_type == 5:  # 32-bit
                    if i + 4 <= len(data):
                        value_bytes = data[i:i+4]
                        result.append("{}Field {}, {} = {}\n".format(
                            indent_str, field_num, wire_name,
                            ProtobufAnalyzer._bytes_to_hex(value_bytes)
                        ))
                        i += 4
                    else:
                        result.append("{}Field {}, {} (incomplete)\n".format(
                            indent_str, field_num, wire_name
                        ))
                        break
                else:
                    result.append("{}Field {}, {} (unsupported)\n".format(
                        indent_str, field_num, wire_name
                    ))
                    break
                    
        except Exception as e:
            result.append("{}(parse error: {})\n".format("  " * indent, str(e)))
        
        return "".join(result)
    
    @staticmethod
    def hex_dump(data, bytes_per_line=16):
        """
        Create hex dump with ASCII representation.
        
        Args:
            data: Bytes to dump
            bytes_per_line: Number of bytes per line
            
        Returns:
            str: Formatted hex dump
        """
        if not data:
            return "(empty)\n"
        
        result = []
        
        for offset in range(0, len(data), bytes_per_line):
            chunk = data[offset:offset + bytes_per_line]
            
            # Offset
            line = "{:04x}  ".format(offset)
            
            # Hex bytes
            hex_parts = []
            for i in range(bytes_per_line):
                if i < len(chunk):
                    hex_parts.append("{:02x}".format(chunk[i]))
                else:
                    hex_parts.append("  ")
                    
                # Add extra space in the middle
                if i == 7:
                    hex_parts.append(" ")
            
            line += " ".join(hex_parts)
            line += "  "
            
            # ASCII representation
            ascii_part = ""
            for byte in chunk:
                if 32 <= byte <= 126:
                    ascii_part += chr(byte)
                else:
                    ascii_part += "."
            
            line += ascii_part
            result.append(line + "\n")
        
        return "".join(result)
    
    @staticmethod
    def compare_messages(msg1, msg2):
        """
        Compare two messages byte-by-byte.
        
        Args:
            msg1: First message
            msg2: Second message
            
        Returns:
            str: Comparison showing differences
        """
        result = []
        
        result.append("Message 1: {} bytes\n".format(len(msg1)))
        result.append("Message 2: {} bytes\n".format(len(msg2)))
        result.append("\n")
        
        max_len = max(len(msg1), len(msg2))
        
        if len(msg1) != len(msg2):
            result.append("Length difference: {} bytes\n\n".format(abs(len(msg1) - len(msg2))))
        
        # Compare byte by byte
        differences = 0
        bytes_per_line = 16
        
        for offset in range(0, max_len, bytes_per_line):
            chunk1 = msg1[offset:offset + bytes_per_line] if offset < len(msg1) else b''
            chunk2 = msg2[offset:offset + bytes_per_line] if offset < len(msg2) else b''
            
            # Check if this line has differences
            has_diff = False
            for i in range(max(len(chunk1), len(chunk2))):
                b1 = chunk1[i] if i < len(chunk1) else None
                b2 = chunk2[i] if i < len(chunk2) else None
                if b1 != b2:
                    has_diff = True
                    differences += 1
            
            if has_diff:
                # Show offset
                result.append("{:04x}:\n".format(offset))
                
                # Show message 1
                line1 = "  1: "
                for i in range(bytes_per_line):
                    if i < len(chunk1):
                        line1 += "{:02x} ".format(chunk1[i])
                    else:
                        line1 += "   "
                result.append(line1 + "\n")
                
                # Show message 2
                line2 = "  2: "
                for i in range(bytes_per_line):
                    if i < len(chunk2):
                        line2 += "{:02x} ".format(chunk2[i])
                    else:
                        line2 += "   "
                result.append(line2 + "\n")
                
                # Show difference markers
                diff_line = "     "
                for i in range(min(bytes_per_line, max(len(chunk1), len(chunk2)))):
                    b1 = chunk1[i] if i < len(chunk1) else None
                    b2 = chunk2[i] if i < len(chunk2) else None
                    if b1 != b2:
                        diff_line += "^^ "
                    else:
                        diff_line += "   "
                result.append(diff_line + "\n\n")
        
        if differences == 0:
            result.append("Messages are identical\n")
        else:
            result.append("Total differences: {} bytes\n".format(differences))
        
        return "".join(result)
    
    # Helper methods
    
    @staticmethod
    def _read_varint(data, offset):
        """
        Read a varint from data at offset.
        
        Returns:
            tuple: (value, bytes_read)
        """
        value = 0
        shift = 0
        bytes_read = 0
        
        while offset + bytes_read < len(data):
            byte = data[offset + bytes_read]
            bytes_read += 1
            
            value |= (byte & 0x7f) << shift
            
            if not (byte & 0x80):
                break
                
            shift += 7
            
            if bytes_read > 10:  # Varint too long
                break
        
        return value, bytes_read
    
    @staticmethod
    def _bytes_to_hex(data):
        """Convert bytes to hex string."""
        return " ".join("{:02x}".format(b) for b in data)
    
    @staticmethod
    def _looks_like_protobuf(data):
        """
        Check if data looks like a protobuf message.
        
        Returns:
            bool: True if data appears to be protobuf
        """
        if not data or len(data) == 0:
            return False
        
        # Check first byte - should be a valid tag
        tag = data[0]
        wire_type = tag & 0x07
        field_num = tag >> 3
        
        # Field number should be reasonable (1-536870911)
        # Wire type should be valid (0-5, excluding 3 and 4)
        if field_num == 0:
            return False
        
        if wire_type in (3, 4, 6, 7):
            return False
        
        # If it's length-delimited, check if length is reasonable
        if wire_type == 2 and len(data) >= 2:
            length = data[1]
            # Simple check: length should not exceed remaining data
            if length > len(data) - 2:
                return False
        
        return True
