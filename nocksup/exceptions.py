"""
Exceptions for the nocksup library.
"""

class NocksupException(Exception):
    """Base exception for the nocksup library."""
    pass

class ConnectionError(NocksupException):
    """Error when connecting to WhatsApp servers."""
    pass

class AuthenticationError(NocksupException):
    """Error during authentication."""
    pass

class RegistrationError(NocksupException):
    """Error during registration."""
    pass

class VerificationError(NocksupException):
    """Error during verification."""
    pass

class MessageError(NocksupException):
    """Error when sending or receiving messages."""
    pass

class ProtocolError(NocksupException):
    """Error in the WhatsApp protocol."""
    pass

class MediaError(NocksupException):
    """Error when handling media."""
    pass

class GroupError(NocksupException):
    """Error when handling groups."""
    pass

class ConfigError(NocksupException):
    """Error in configuration."""
    pass

class ValidationError(NocksupException):
    """Error when validating data."""
    pass

class EncryptionError(NocksupException):
    """Error in encryption/decryption."""
    pass

class StorageError(NocksupException):
    """Error when storing or retrieving data."""
    pass

class ContactError(NocksupException):
    """Error when handling contacts."""
    pass

class TimeoutError(NocksupException):
    """Operation timed out."""
    pass
