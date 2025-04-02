"""
Exceptions for Nocksup.

This module provides exceptions used in the Nocksup library.
"""


class NocksupError(Exception):
    """Base exception for Nocksup errors."""
    pass


class ValidationError(NocksupError):
    """Raised when validation fails."""
    pass


class ConnectionError(NocksupError):
    """Raised when connection to WhatsApp servers fails."""
    pass


class AuthenticationError(NocksupError):
    """Raised when authentication fails."""
    pass


class RegistrationError(NocksupError):
    """Raised when registration fails."""
    pass


class VerificationError(NocksupError):
    """Raised when verification fails."""
    pass


class MessageError(NocksupError):
    """Raised when message sending or receiving fails."""
    pass


class GroupError(NocksupError):
    """Raised when group operations fail."""
    pass


class ContactError(NocksupError):
    """Raised when contact operations fail."""
    pass


class ProtocolError(NocksupError):
    """Raised when protocol errors occur."""
    pass


class EncryptionError(NocksupError):
    """Raised when encryption operations fail."""
    pass


class StorageError(NocksupError):
    """Raised when storage operations fail."""
    pass