import yaml
import os
from pathlib import Path

class Config:
    """Thread-safe configuration manager with hot reload"""
    _instance = None
    _settings = {
        "network": {
            "interface": "en0",
            "timeout": 5,
            "max_threads": 20,
            "packet_size": 1500,
            "src_mac": "00:11:22:33:44:55",
            "spoof_ip": "192.168.1.100"
        },
        "attacks": {
            "arp_spoof": {
                "target_ip": "192.168.1.5",
                "gateway_ip": "192.168.1.1",
                "interval": 2
            },
            "syn_flood": {
                "target_ip": "192.168.1.10",
                "port": 80,
                "count": 1000,
                "threads": 10
            }
        },
        "gui": {
            "theme": "dark",
            "geometry": "1400x900",
            "refresh_rate": 100
        },
        "logging": {
            "level": "INFO",
            "file": "aegis.log"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Load from file if exists
            config_path = Path("config/default.yaml")
            if config_path.exists():
                with open(config_path) as f:
                    cls._settings.update(yaml.safe_load(f))
        return cls._instance

    def get(self, key, default=None):
        keys = key.split('.')
        val = self._settings
        for k in keys:
            val = val.get(k, default)
            if val is None:
                return default
        return val

    def set(self, key, value):
        keys = key.split('.')
        d = self._settings
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

# Singleton
config = Config()