"""
Configuration settings for the nocksup library.
"""
import os
import logging
from typing import Dict, Any

# WhatsApp connection settings
WHATSAPP_SERVER = 'e{0}.whatsapp.net'
WHATSAPP_DOMAIN = 's.whatsapp.net'
WHATSAPP_REGISTER_URL = 'https://v.whatsapp.net/v2/register'
WHATSAPP_VERIFY_URL = 'https://v.whatsapp.net/v2/code'
WHATSAPP_WS_URL = 'wss://web.whatsapp.com/ws'
WHATSAPP_VERSION = '2.23.10.76'  # This should be updated as WhatsApp updates

# User agent for HTTP requests
USER_AGENT = f"WhatsApp/{WHATSAPP_VERSION} Android/11 Device/nocksup"

# Key constants for crypto
CURVE_TYPE = 'curve25519'
AES_KEY_SIZE = 32
HASH_ITERATION_COUNT = 16

# Connection settings
SOCKET_TIMEOUT = 30
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

# Default paths
DEFAULT_CONFIG_PATH = os.path.expanduser('~/.nocksup')
DEFAULT_LOG_LEVEL = logging.INFO

class ConfigManager:
    """Manages configuration settings for nocksup."""
    
    def __init__(self, config_path: str = None, log_level: int = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to store configuration files
            log_level: Logging level to use
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.log_level = log_level or DEFAULT_LOG_LEVEL
        
        # Ensure config directory exists
        os.makedirs(self.config_path, exist_ok=True)
        
        # Default config values
        self._config = {
            'server': WHATSAPP_SERVER,
            'domain': WHATSAPP_DOMAIN,
            'register_url': WHATSAPP_REGISTER_URL,
            'verify_url': WHATSAPP_VERIFY_URL,
            'ws_url': WHATSAPP_WS_URL,
            'version': WHATSAPP_VERSION,
            'user_agent': USER_AGENT,
            'socket_timeout': SOCKET_TIMEOUT,
            'max_retries': MAX_RETRIES,
            'retry_delay': RETRY_DELAY
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update multiple configuration values at once."""
        self._config.update(config_dict)
        
    @property
    def config_dict(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self._config.copy()
