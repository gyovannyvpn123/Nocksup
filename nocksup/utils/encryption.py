"""
Encryption utilities for secure WhatsApp communication.

This module handles the encryption/decryption functionality required
for secure communication with WhatsApp, including key generation and
message encryption using the required cryptographic protocols.
"""
import os
import hashlib
import hmac
import base64
from typing import Tuple, Dict, Any, Union, List

# Import cryptography libraries
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend

from nocksup.exceptions import EncryptionError
from nocksup.utils.logger import logger

class EncryptionManager:
    """Manages encryption operations for WhatsApp communication."""
    
    def __init__(self, identity_key: bytes = None):
        """
        Initialize the encryption manager with optional identity key.
        
        Args:
            identity_key: Optional identity key, will generate new one if not provided
        """
        # Generate or use provided identity key
        self._identity_key_pair = self._load_or_generate_identity_key(identity_key)
        self._sessions = {}  # Map of JID -> encryption session
        
    def _load_or_generate_identity_key(self, identity_key: bytes = None) -> Tuple[bytes, bytes]:
        """
        Load existing or generate new identity key pair.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        if identity_key:
            # TODO: Implement loading from existing key
            # This would require appropriate key format validation
            pass
        
        # Generate new key pair
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Get raw bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return (private_bytes, public_bytes)
    
    def generate_keys(self) -> Dict[str, bytes]:
        """
        Generate encryption keys required for WhatsApp registration.
        
        Returns:
            Dictionary with the required keys
        """
        # Generate ephemeral key pair
        ephemeral_private = x25519.X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()
        
        # Get raw bytes
        ephemeral_private_bytes = ephemeral_private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        ephemeral_public_bytes = ephemeral_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return {
            'identity_private': self._identity_key_pair[0],
            'identity_public': self._identity_key_pair[1],
            'ephemeral_private': ephemeral_private_bytes,
            'ephemeral_public': ephemeral_public_bytes
        }
    
    def establish_session(self, jid: str, their_public_key: bytes) -> None:
        """
        Establish an encryption session with a contact.
        
        Args:
            jid: WhatsApp ID of the contact
            their_public_key: Public key of the contact
        """
        # Create a new session for the contact
        self._sessions[jid] = {
            'their_public_key': their_public_key,
            'shared_secret': None,
            'chain_key': None
        }
        
        # Calculate shared secret (ECDH)
        their_key = x25519.X25519PublicKey.from_public_bytes(their_public_key)
        private_key = x25519.X25519PrivateKey.from_private_bytes(self._identity_key_pair[0])
        shared_secret = private_key.exchange(their_key)
        
        # Derive initial chain key using HKDF
        chain_key = self._hkdf(
            shared_secret, 
            b"WhatsApp Chain Key", 
            b"\x01", 
            32
        )
        
        # Store in session
        self._sessions[jid]['shared_secret'] = shared_secret
        self._sessions[jid]['chain_key'] = chain_key
    
    def encrypt_message(self, jid: str, plaintext: Union[str, bytes]) -> bytes:
        """
        Encrypt a message for a contact.
        
        Args:
            jid: WhatsApp ID of the recipient
            plaintext: Message to encrypt
            
        Returns:
            Encrypted message bytes
        """
        if jid not in self._sessions:
            raise EncryptionError(f"No encryption session established with {jid}")
        
        # Ensure plaintext is bytes
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Get session
        session = self._sessions[jid]
        
        # Derive message key and next chain key
        message_key = self._hmac_sha256(session['chain_key'], b"\x01")
        next_chain_key = self._hmac_sha256(session['chain_key'], b"\x02")
        
        # Update chain key
        session['chain_key'] = next_chain_key
        
        # Derive encryption key and IV using HKDF
        key_material = self._hkdf(
            message_key,
            b"WhatsApp Message Keys",
            b"",
            80
        )
        
        enc_key = key_material[:32]
        iv = key_material[32:48]
        
        # Pad the plaintext
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        
        # Encrypt the message
        cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Create HMAC
        mac_key = key_material[48:80]
        mac = hmac.new(mac_key, ciphertext, hashlib.sha256).digest()
        
        # Combine IV, ciphertext, and MAC
        result = iv + ciphertext + mac
        
        return result
    
    def decrypt_message(self, jid: str, ciphertext: bytes) -> bytes:
        """
        Decrypt a message from a contact.
        
        Args:
            jid: WhatsApp ID of the sender
            ciphertext: Encrypted message
            
        Returns:
            Decrypted message bytes
        """
        if jid not in self._sessions:
            raise EncryptionError(f"No encryption session established with {jid}")
        
        # Get session
        session = self._sessions[jid]
        
        # Check if message is at least as long as IV + MAC
        if len(ciphertext) < 16 + 32:
            raise EncryptionError("Message too short")
        
        # Extract IV, ciphertext, and MAC
        iv = ciphertext[:16]
        actual_ciphertext = ciphertext[16:-32]
        mac = ciphertext[-32:]
        
        # Derive message key and next chain key
        message_key = self._hmac_sha256(session['chain_key'], b"\x01")
        next_chain_key = self._hmac_sha256(session['chain_key'], b"\x02")
        
        # Update chain key
        session['chain_key'] = next_chain_key
        
        # Derive keys from message key
        key_material = self._hkdf(
            message_key,
            b"WhatsApp Message Keys",
            b"",
            80
        )
        
        enc_key = key_material[:32]
        mac_key = key_material[48:80]
        
        # Verify MAC
        expected_mac = hmac.new(mac_key, iv + actual_ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise EncryptionError("MAC verification failed")
        
        # Decrypt message
        cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext
    
    def _hmac_sha256(self, key: bytes, message: bytes) -> bytes:
        """Compute HMAC-SHA256."""
        return hmac.new(key, message, hashlib.sha256).digest()
    
    def _hkdf(self, input_key_material: bytes, info: bytes, salt: bytes, length: int) -> bytes:
        """
        HKDF (HMAC-based Key Derivation Function) implementation.
        
        Args:
            input_key_material: Input key material
            info: Context and application specific information
            salt: Salt value (optional)
            length: Length of output keying material
            
        Returns:
            Output keying material
        """
        if not salt:
            salt = b"\x00" * 32
            
        # Extract
        prk = hmac.new(salt, input_key_material, hashlib.sha256).digest()
        
        # Expand
        t = b""
        okm = b""
        for i in range(1, (length // 32) + 2):
            t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
            okm += t
        
        return okm[:length]

def generate_random_bytes(length: int) -> bytes:
    """Generate cryptographically secure random bytes."""
    return os.urandom(length)

# Missing import added here to resolve reference before assignment
from cryptography.hazmat.primitives import serialization
