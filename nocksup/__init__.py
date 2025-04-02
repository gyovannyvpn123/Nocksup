"""
Nocksup - Python Library for WhatsApp.

Nocksup este o bibliotecă Python pentru comunicarea WhatsApp, dezvoltată
ca înlocuitor pentru Yowsup, menținând compatibilitatea cu protocoalele actuale.
"""

__version__ = '0.3.0'
__author__ = 'gyovannyvpn123'
__email__ = 'mdanut159@gmail.com'

# Import the main client class
from nocksup.client.client import NocksupClient

# Import exceptions
from nocksup.exceptions import (
    NocksupError, ValidationError, ConnectionError, AuthenticationError,
    RegistrationError, VerificationError, MessageError, GroupError, ContactError,
    ProtocolError, EncryptionError, StorageError
)

# Import CLI
from nocksup.cli import NocksupCLI

__all__ = [
    'NocksupClient',
    'NocksupCLI',
    'NocksupError',
    'ValidationError',
    'ConnectionError',
    'AuthenticationError',
    'RegistrationError',
    'VerificationError',
    'MessageError',
    'GroupError',
    'ContactError',
    'ProtocolError',
    'EncryptionError',
    'StorageError'
]