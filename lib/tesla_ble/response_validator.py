"""Response validation for Tesla BLE body-controller-state responses.

This module validates raw response bytes against expected patterns from
the official Tesla vehicle-command implementation.

Based on tesla-control debug logs, valid responses have:
- Prefix: 0x32 0x12 0x12 0x10
- Variable section: 16 bytes (routing address matching TX)
- Suffix: 0x3a 0x02 0x08 0x02 0x52 0x0c 0x0a 0x0a 0x0a 0x02 0x40 0x03 0x10 0x01 0x18 0x02 0x20 0x01
- Length: 40-60 bytes typical
"""

try:
    import ubinascii as binascii
except ImportError:
    import binascii


# Expected patterns from tesla-control logs
EXPECTED_PREFIX = bytes([0x32, 0x12, 0x12, 0x10])
EXPECTED_SUFFIX = bytes([0x3a, 0x02, 0x08, 0x02, 0x52, 0x0c, 0x0a, 0x0a, 
                         0x0a, 0x02, 0x40, 0x03, 0x10, 0x01, 0x18, 0x02, 0x20, 0x01])

# Reasonable length bounds
MIN_RESPONSE_LENGTH = 35  # Minimum expected
MAX_RESPONSE_LENGTH = 100  # Maximum expected


def validate_response(response_bytes):
    """Validate response structure and extract patterns.
    
    Args:
        response_bytes: Raw response from vehicle (bytes)
    
    Returns:
        dict: {
            'valid': bool - Overall validation result,
            'prefix_match': bool - Prefix matches expected,
            'suffix_match': bool - Suffix matches expected,
            'length_valid': bool - Length is reasonable,
            'routing_address': bytes - Extracted routing address (16 bytes),
            'errors': list - List of validation errors
        }
    """
    result = {
        'valid': True,
        'prefix_match': False,
        'suffix_match': False,
        'length_valid': False,
        'routing_address': None,
        'errors': []
    }
    
    # Check if response is bytes
    if not isinstance(response_bytes, (bytes, bytearray)):
        result['valid'] = False
        result['errors'].append("Response is not bytes type")
        return result
    
    # Check length
    response_len = len(response_bytes)
    if response_len < MIN_RESPONSE_LENGTH:
        result['valid'] = False
        result['errors'].append("Response too short: {} bytes (min: {})".format(
            response_len, MIN_RESPONSE_LENGTH))
    elif response_len > MAX_RESPONSE_LENGTH:
        result['valid'] = False
        result['errors'].append("Response too long: {} bytes (max: {})".format(
            response_len, MAX_RESPONSE_LENGTH))
    else:
        result['length_valid'] = True
    
    # Check prefix (first 4 bytes)
    if response_len >= len(EXPECTED_PREFIX):
        prefix = response_bytes[:len(EXPECTED_PREFIX)]
        if prefix == EXPECTED_PREFIX:
            result['prefix_match'] = True
        else:
            result['valid'] = False
            result['errors'].append("Prefix mismatch: expected {}, got {}".format(
                binascii.hexlify(EXPECTED_PREFIX).decode(),
                binascii.hexlify(prefix).decode()))
    else:
        result['valid'] = False
        result['errors'].append("Response too short to check prefix")
    
    # Extract routing address (16 bytes after prefix)
    if response_len >= len(EXPECTED_PREFIX) + 16:
        result['routing_address'] = response_bytes[len(EXPECTED_PREFIX):len(EXPECTED_PREFIX) + 16]
    
    # Check suffix (last 18 bytes)
    if response_len >= len(EXPECTED_SUFFIX):
        suffix = response_bytes[-len(EXPECTED_SUFFIX):]
        if suffix == EXPECTED_SUFFIX:
            result['suffix_match'] = True
        else:
            result['valid'] = False
            result['errors'].append("Suffix mismatch: expected {}, got {}".format(
                binascii.hexlify(EXPECTED_SUFFIX).decode(),
                binascii.hexlify(suffix).decode()))
    else:
        result['valid'] = False
        result['errors'].append("Response too short to check suffix")
    
    return result


def format_validation_result(result):
    """Format validation result for display.
    
    Args:
        result: Validation result dict from validate_response()
    
    Returns:
        str: Formatted validation result
    """
    lines = []
    lines.append("Validation Result: {}".format("PASS" if result['valid'] else "FAIL"))
    lines.append("  Prefix Match: {}".format("YES" if result['prefix_match'] else "NO"))
    lines.append("  Suffix Match: {}".format("YES" if result['suffix_match'] else "NO"))
    lines.append("  Length Valid: {}".format("YES" if result['length_valid'] else "NO"))
    
    if result['routing_address']:
        lines.append("  Routing Address: {}".format(
            binascii.hexlify(result['routing_address']).decode()))
    
    if result['errors']:
        lines.append("  Errors:")
        for error in result['errors']:
            lines.append("    - {}".format(error))
    
    return "\n".join(lines)



def compare_responses(response1, response2):
    """Compare two responses and identify differences.
    
    Args:
        response1: First response bytes
        response2: Second response bytes
    
    Returns:
        dict: {
            'identical': bool - Whether responses are identical,
            'length_match': bool - Whether lengths match,
            'differences': list - List of (position, byte1, byte2) tuples,
            'difference_count': int - Number of differing bytes
        }
    """
    result = {
        'identical': False,
        'length_match': False,
        'differences': [],
        'difference_count': 0
    }
    
    # Check if both are bytes
    if not isinstance(response1, (bytes, bytearray)):
        result['differences'].append("Response 1 is not bytes type")
        return result
    
    if not isinstance(response2, (bytes, bytearray)):
        result['differences'].append("Response 2 is not bytes type")
        return result
    
    # Check lengths
    len1 = len(response1)
    len2 = len(response2)
    result['length_match'] = (len1 == len2)
    
    if not result['length_match']:
        result['differences'].append("Length mismatch: {} vs {} bytes".format(len1, len2))
        return result
    
    # Compare byte by byte
    differences = []
    for i in range(len1):
        if response1[i] != response2[i]:
            differences.append((i, response1[i], response2[i]))
    
    result['differences'] = differences
    result['difference_count'] = len(differences)
    result['identical'] = (len(differences) == 0)
    
    return result


def format_comparison_result(result):
    """Format comparison result for display.
    
    Args:
        result: Comparison result dict from compare_responses()
    
    Returns:
        str: Formatted comparison result
    """
    lines = []
    
    if result['identical']:
        lines.append("Responses are IDENTICAL")
        return "\n".join(lines)
    
    lines.append("Responses DIFFER")
    
    if not result['length_match']:
        lines.append("  Length mismatch")
        if isinstance(result['differences'][0], str):
            lines.append("  {}".format(result['differences'][0]))
        return "\n".join(lines)
    
    lines.append("  Difference count: {}".format(result['difference_count']))
    lines.append("  Differing positions:")
    
    for pos, byte1, byte2 in result['differences']:
        lines.append("    Position {}: 0x{:02x} vs 0x{:02x}".format(pos, byte1, byte2))
    
    return "\n".join(lines)
