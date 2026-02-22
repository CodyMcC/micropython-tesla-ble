"""
Configuration loader for Tesla BLE library.

Loads VIN and private key from Pico W filesystem.
"""

try:
    import ujson as json
except ImportError:
    import json

try:
    import uos as os
except ImportError:
    import os


class Config:
    """Configuration for Tesla BLE connection."""
    
    def __init__(self):
        self.vin = None
        self.private_key_path = "/config/private_key.pem"
        self.public_key_path = "/config/public_key.bin"
        self.config_path = "/config/config.json"
        self._private_key = None
        self._public_key = None
        self.shared_key = None
        self.hmac_key = None
        
    def load(self):
        """Load configuration from filesystem."""
        # Load VIN from config.json
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                self.vin = config_data.get('vin')
                if not self.vin:
                    raise ValueError("VIN not found in config.json")
                
                # Load pre-computed keys (hex strings)
                shared_key_hex = config_data.get('shared_key')
                hmac_key_hex = config_data.get('hmac_key')
                
                if not shared_key_hex or not hmac_key_hex:
                    raise ValueError("shared_key and hmac_key must be in config.json")
                
                self.shared_key = bytes.fromhex(shared_key_hex)
                self.hmac_key = bytes.fromhex(hmac_key_hex)
                
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")
        
        # Verify private key exists
        try:
            stat = os.stat(self.private_key_path)
            if stat[6] == 0:  # File size is 0
                raise ValueError("Private key file is empty")
        except OSError:
            raise RuntimeError(f"Private key not found at {self.private_key_path}")
        
        return self
    
    def load_private_key(self):
        """Load private key from filesystem."""
        if self._private_key is not None:
            return self._private_key
            
        try:
            with open(self.private_key_path, 'r') as f:
                self._private_key = f.read()
                if not self._private_key:
                    raise ValueError("Private key file is empty")
                return self._private_key
        except Exception as e:
            raise RuntimeError(f"Failed to load private key: {e}")
    
    def load_public_key(self):
        """Load public key from filesystem (pre-computed binary format)."""
        if self._public_key is not None:
            return self._public_key
            
        try:
            with open(self.public_key_path, 'rb') as f:
                self._public_key = f.read()
                if len(self._public_key) != 65:
                    raise ValueError(f"Invalid public key length: {len(self._public_key)}")
                if self._public_key[0] != 0x04:
                    raise ValueError("Invalid public key format (must start with 0x04)")
                return self._public_key
        except OSError:
            # Public key file doesn't exist, return None
            # (will need to extract from private key)
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to load public key: {e}")
    
    def get_ble_name(self):
        """
        Calculate BLE advertisement name from VIN.
        
        Tesla vehicles advertise with name: "S" + SHA1(VIN)[:16] + "C"
        """
        if not self.vin:
            raise ValueError("VIN not loaded")
        
        try:
            import uhashlib
            import ubinascii
        except ImportError:
            import hashlib as uhashlib
            import binascii as ubinascii
        
        # Calculate SHA1 of VIN
        h = uhashlib.sha1()
        h.update(self.vin.encode('utf-8'))
        hash_bytes = h.digest()
        
        # Take first 8 bytes and convert to hex
        hash_hex = ubinascii.hexlify(hash_bytes[:8]).decode('utf-8')
        
        # Format: S + hash + C
        ble_name = f"S{hash_hex}C"
        return ble_name
    
    def __repr__(self):
        return f"Config(vin={self.vin}, key_path={self.private_key_path})"


# Global config instance
_config = None


def get_config():
    """Get global config instance, loading if necessary."""
    global _config
    if _config is None:
        _config = Config().load()
    return _config


def reload_config():
    """Force reload of configuration."""
    global _config
    _config = Config().load()
    return _config
