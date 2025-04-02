"""
nocksup - A Python library for WhatsApp communication

This library implements current WhatsApp protocols with authentication and
messaging capabilities, allowing Python applications to interact with WhatsApp.

Main components:
- Authentication and registration
- Messaging (text, media)
- Contact and group management
- Connection management
"""

__version__ = '0.2.0'

# For more convenient imports
from nocksup.client.client import NocksupClient

__all__ = ['NocksupClient']