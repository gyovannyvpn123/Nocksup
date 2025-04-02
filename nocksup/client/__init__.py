"""
Client module for WhatsApp interaction.

This module provides the main client interface for WhatsApp
communication, allowing users to interact with the library.
"""

from nocksup.client.client import NocksupClient
from nocksup.client.contact_manager import ContactManager

__all__ = ['NocksupClient', 'ContactManager']
