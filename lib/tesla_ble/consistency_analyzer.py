"""Consistency analysis for multiple Tesla BLE responses.

This module analyzes multiple body-controller-state responses to identify
consistent and variable byte positions.
"""

try:
    import ubinascii as binascii
except ImportError:
    import binascii


def analyze_consistency(responses):
    """Analyze consistency across multiple responses.
    
    Args:
        responses: List of response bytes
    
    Returns:
        dict: {
            'response_count': int - Number of responses analyzed,
            'length_consistent': bool - All responses same length,
            'common_length': int - Most common length (or None),
            'consistent_positions': list - Byte positions that never vary,
            'variable_positions': list - Byte positions that vary,
            'consistency_percentage': float - Percentage of consistent bytes
        }
    """
    result = {
        'response_count': len(responses),
        'length_consistent': False,
        'common_length': None,
        'consistent_positions': [],
        'variable_positions': [],
        'consistency_percentage': 0.0
    }
    
    if len(responses) == 0:
        return result
    
    if len(responses) == 1:
        result['length_consistent'] = True
        result['common_length'] = len(responses[0])
        result['consistent_positions'] = list(range(len(responses[0])))
        result['consistency_percentage'] = 100.0
        return result
    
    # Check if all responses are bytes
    for i, resp in enumerate(responses):
        if not isinstance(resp, (bytes, bytearray)):
            result['error'] = "Response {} is not bytes type".format(i)
            return result
    
    # Check length consistency
    lengths = [len(r) for r in responses]
    result['common_length'] = lengths[0]
    result['length_consistent'] = all(l == result['common_length'] for l in lengths)
    
    if not result['length_consistent']:
        result['error'] = "Responses have different lengths: {}".format(set(lengths))
        return result
    
    # Analyze each byte position
    length = result['common_length']
    consistent_positions = []
    variable_positions = []
    
    for pos in range(length):
        # Get all bytes at this position
        bytes_at_pos = [resp[pos] for resp in responses]
        
        # Check if all bytes are the same
        if all(b == bytes_at_pos[0] for b in bytes_at_pos):
            consistent_positions.append(pos)
        else:
            variable_positions.append(pos)
    
    result['consistent_positions'] = consistent_positions
    result['variable_positions'] = variable_positions
    
    # Calculate consistency percentage
    if length > 0:
        result['consistency_percentage'] = (len(consistent_positions) / length) * 100.0
    
    return result


def format_consistency_result(result, show_positions=False):
    """Format consistency analysis result for display.
    
    Args:
        result: Consistency result dict from analyze_consistency()
        show_positions: If True, show detailed position lists
    
    Returns:
        str: Formatted consistency result
    """
    lines = []
    
    lines.append("Consistency Analysis")
    lines.append("  Response count: {}".format(result['response_count']))
    
    if 'error' in result:
        lines.append("  Error: {}".format(result['error']))
        return "\n".join(lines)
    
    lines.append("  Length consistent: {}".format("YES" if result['length_consistent'] else "NO"))
    
    if result['common_length'] is not None:
        lines.append("  Common length: {} bytes".format(result['common_length']))
    
    lines.append("  Consistent positions: {}".format(len(result['consistent_positions'])))
    lines.append("  Variable positions: {}".format(len(result['variable_positions'])))
    lines.append("  Consistency: {:.1f}%".format(result['consistency_percentage']))
    
    if show_positions and result['variable_positions']:
        lines.append("\n  Variable positions:")
        for pos in result['variable_positions']:
            lines.append("    Position {}".format(pos))
    
    return "\n".join(lines)


def identify_variable_regions(result):
    """Identify contiguous regions of variable bytes.
    
    Args:
        result: Consistency result dict from analyze_consistency()
    
    Returns:
        list: List of (start, end) tuples for variable regions
    """
    if not result['variable_positions']:
        return []
    
    regions = []
    positions = sorted(result['variable_positions'])
    
    start = positions[0]
    prev = positions[0]
    
    for pos in positions[1:]:
        if pos != prev + 1:
            # Gap found, close current region
            regions.append((start, prev))
            start = pos
        prev = pos
    
    # Close final region
    regions.append((start, prev))
    
    return regions


def format_variable_regions(regions):
    """Format variable regions for display.
    
    Args:
        regions: List of (start, end) tuples from identify_variable_regions()
    
    Returns:
        str: Formatted variable regions
    """
    if not regions:
        return "No variable regions"
    
    lines = []
    lines.append("Variable regions:")
    
    for start, end in regions:
        if start == end:
            lines.append("  Position {}: 1 byte".format(start))
        else:
            lines.append("  Positions {}-{}: {} bytes".format(start, end, end - start + 1))
    
    return "\n".join(lines)
