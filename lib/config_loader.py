"""
Configuration loader for the Tesla BLE library.

Reads the vehicle VIN from the Pico W filesystem (/config/config.json).

This library performs unauthenticated reads of the body-controller-state
command only, so no keys are required -- the VIN is the sole configuration.
"""

try:
    import ujson as json
except ImportError:
    import json


class Config:
    """Configuration for a Tesla BLE connection (VIN only)."""

    def __init__(self, config_path="/config/config.json"):
        self.vin = None
        self.config_path = config_path

    def load(self):
        """Load the VIN from config.json."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
        except OSError:
            raise RuntimeError("Config not found at {}".format(self.config_path))
        except ValueError:
            raise RuntimeError("Config at {} is not valid JSON".format(self.config_path))

        self.vin = config_data.get('vin')
        if not self.vin:
            raise ValueError("VIN not found in {}".format(self.config_path))

        return self

    def get_ble_name(self):
        """
        Calculate the BLE advertisement name from the VIN.

        Tesla vehicles advertise as "S" + hex(SHA1(VIN)[:8]) + "C".
        """
        if not self.vin:
            raise ValueError("VIN not loaded")

        try:
            import uhashlib as hashlib
            import ubinascii as binascii
        except ImportError:
            import hashlib
            import binascii

        h = hashlib.sha1()
        h.update(self.vin.encode('utf-8'))
        hash_hex = binascii.hexlify(h.digest()[:8]).decode('utf-8')
        return "S{}C".format(hash_hex)

    def __repr__(self):
        return "Config(vin={})".format(self.vin)


# Global config instance
_config = None


def get_config():
    """Get the global config instance, loading if necessary."""
    global _config
    if _config is None:
        _config = Config().load()
    return _config


def reload_config():
    """Force a reload of the configuration."""
    global _config
    _config = Config().load()
    return _config
