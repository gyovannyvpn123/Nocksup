"""
Storage module for WhatsApp data.

This module provides storage functionality for WhatsApp data,
including session information, contacts, and messages.
"""

from nocksup.storage.session_store import SessionStore
from nocksup.storage.contact_store import ContactStore

__all__ = ['SessionStore', 'ContactStore']
