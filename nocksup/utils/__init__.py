"""
Utility functions for the nocksup library.
"""
import re
import random
import string
import time
from typing import Optional

def generate_request_id() -> str:
    """Generate a unique request ID for WhatsApp requests."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

def validate_phone_number(phone: str) -> str:
    """
    Validate and normalize a phone number.
    
    Args:
        phone: Phone number with or without country code
        
    Returns:
        Normalized phone number with country code
        
    Raises:
        ValueError: If phone number is invalid
    """
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check if it starts with country code
    if not phone.startswith('1') and not phone.startswith('2') and not phone.startswith('3') and not phone.startswith('4'):
        raise ValueError("Phone number must include country code")
    
    # Basic length check
    if len(phone) < 8 or len(phone) > 15:
        raise ValueError("Phone number has invalid length")
    
    return phone

def jid_to_phone(jid: str) -> str:
    """Extract phone number from WhatsApp JID."""
    if '@' in jid:
        return jid.split('@')[0]
    return jid

def phone_to_jid(phone: str, domain: str = 's.whatsapp.net') -> str:
    """Convert phone number to WhatsApp JID."""
    phone = validate_phone_number(phone)
    return f"{phone}@{domain}"

def current_timestamp() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)

def split_jid(jid: str) -> tuple:
    """
    Split JID into user and domain parts.
    
    Args:
        jid: JID string (user@domain)
        
    Returns:
        Tuple of (user, domain)
    """
    if '@' in jid:
        user, domain = jid.split('@', 1)
        return user, domain
    return jid, None

def is_group_jid(jid: str) -> bool:
    """
    Check if a JID is a group.
    
    Args:
        jid: JID to check
        
    Returns:
        True if it's a group JID, False otherwise
    """
    return jid.endswith('@g.us')
