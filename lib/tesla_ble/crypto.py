"""
Minimal cryptography implementations for MicroPython.
Provides HMAC since it's not built-in.
"""
import uhashlib


def hmac_sha256(key, message):
    """
    Implement HMAC-SHA256 since MicroPython doesn't have hmac module.
    
    Args:
        key: bytes
        message: bytes
    
    Returns:
        bytes: 32-byte HMAC digest
    
    Reference: RFC 2104
    """
    block_size = 64  # SHA256 block size
    
    # If key is longer than block size, hash it
    if len(key) > block_size:
        h = uhashlib.sha256(key)
        key = h.digest()
    
    # Pad key to block size
    if len(key) < block_size:
        key = key + bytes(block_size - len(key))
    
    # Create inner and outer padding
    o_key_pad = bytes(b ^ 0x5C for b in key)
    i_key_pad = bytes(b ^ 0x36 for b in key)
    
    # HMAC = H(o_key_pad || H(i_key_pad || message))
    inner_hash = uhashlib.sha256(i_key_pad + message)
    outer_hash = uhashlib.sha256(o_key_pad + inner_hash.digest())
    
    return outer_hash.digest()


# Note: ECDH is NOT implemented here
# MicroPython on Pico W doesn't have elliptic curve support
# Options:
# 1. Add pure Python implementation (micropython-lib/ecdsa)
# 2. Use pre-computed shared key
# 3. Add C extension module

def ecdh_p256_placeholder(private_key, public_key):
    """
    Placeholder for ECDH P-256.
    This needs to be implemented with a proper EC library.
    
    For now, returns None to indicate not implemented.
    """
    print("ERROR: ECDH not implemented")
    print("Need to add elliptic curve library")
    return None
