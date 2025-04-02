"""
Registration and verification for WhatsApp.

This module handles phone number registration and verification
with WhatsApp servers.
"""
import base64
import hashlib
import hmac
import json
import os
import random
import time
from typing import Dict, Any, Optional, Tuple

from nocksup.utils.http_utils import HttpClient
from nocksup.utils.logger import logger
from nocksup.utils import validate_phone_number
from nocksup.exceptions import RegistrationError, VerificationError
from nocksup.config import (
    WHATSAPP_REGISTER_URL,
    WHATSAPP_VERIFY_URL,
    WHATSAPP_VERSION,
    USER_AGENT
)

class Registration:
    """
    WhatsApp registration manager.
    
    Handles phone number registration and verification with WhatsApp servers.
    """
    
    def __init__(self, http_client: HttpClient = None):
        """
        Initialize registration manager.
        
        Args:
            http_client: Optional HTTP client to use
        """
        self.http_client = http_client or HttpClient()
        
    def request_code(self, phone_number: str, method: str = 'sms', 
                    language: str = 'en', country_code: str = None) -> Dict[str, Any]:
        """
        Request verification code from WhatsApp.
        
        Args:
            phone_number: Phone number with country code
            method: Verification method ('sms' or 'voice')
            language: Language code for the message
            country_code: Two-letter country code (optional)
            
        Returns:
            Response from WhatsApp servers
            
        Raises:
            RegistrationError: If code request fails
        """
        # Validate phone number
        phone = validate_phone_number(phone_number)
        
        # Extract country code if not provided
        if not country_code and phone.startswith('1'):
            country_code = 'US'  # Default to US for country code 1
        
        # Generate registration parameters
        params = self._generate_registration_params(phone)
        
        # Add method-specific parameters
        params.update({
            'method': method,
            'lg': language,
            'lc': country_code or 'US',
            'sim_mcc': '000',  # Mobile Country Code (default)
            'sim_mnc': '000',  # Mobile Network Code (default)
        })
        
        try:
            # Make registration request
            response = self.http_client.post(
                WHATSAPP_REGISTER_URL,
                json_data=params
            )
            
            if response.get('status') == 'sent':
                logger.info(f"Verification code sent via {method}")
                return response
            else:
                error = response.get('reason', 'Unknown error')
                logger.error(f"Failed to request code: {error}")
                raise RegistrationError(f"Failed to request verification code: {error}")
                
        except Exception as e:
            logger.error(f"Registration request failed: {e}")
            raise RegistrationError(f"Failed to request verification code: {str(e)}")
    
    def verify_code(self, phone_number: str, code: str) -> Dict[str, Any]:
        """
        Verify WhatsApp code.
        
        Args:
            phone_number: Phone number with country code
            code: Verification code received
            
        Returns:
            Response from WhatsApp servers with account info
            
        Raises:
            VerificationError: If verification fails
        """
        # Validate phone number
        phone = validate_phone_number(phone_number)
        
        # Generate verification parameters
        params = self._generate_registration_params(phone)
        
        # Add verification-specific parameters
        params.update({
            'code': code,
        })
        
        try:
            # Make verification request
            response = self.http_client.post(
                WHATSAPP_VERIFY_URL,
                json_data=params
            )
            
            if response.get('status') == 'ok':
                logger.info("Phone number verified successfully")
                return response
            else:
                error = response.get('reason', 'Unknown error')
                logger.error(f"Verification failed: {error}")
                raise VerificationError(f"Failed to verify code: {error}")
                
        except Exception as e:
            logger.error(f"Verification request failed: {e}")
            raise VerificationError(f"Failed to verify code: {str(e)}")
    
    def _generate_registration_params(self, phone: str) -> Dict[str, Any]:
        """
        Generate parameters for registration request.
        
        Args:
            phone: Phone number
            
        Returns:
            Dictionary of parameters
        """
        # Generate device ID
        device_id = self._generate_device_id()
        
        # Current timestamp
        timestamp = int(time.time())
        
        # Generate a random client_static_keypair
        client_static_keypair = base64.b64encode(os.urandom(32)).decode('utf-8')
        
        # Base parameters
        params = {
            'cc': phone[:3],  # Country code
            'in': phone[3:],  # Phone number without country code
            'rc': 0,  # Retry count
            'id': device_id,
            'lg': 'en',  # Language
            'lc': 'US',  # Locale
            'token': self._generate_token(phone),
            'mistyped': '6',  # Mistyped count (default)
            'network_radio_type': '1',  # Network radio type (default)
            'simnum': '1',  # SIM number (default)
            'hasinrc': '1',  # Has in recent calls (default)
            'tos': '2',  # Terms of service version
            'fdid': device_id,  # Facebook device ID
            'refkey': self._generate_ref_key(phone),
            'e_regid': client_static_keypair,
            'e_keytype': '1',  # Key type (default)
            'e_ident': client_static_keypair,
            'e_skey_id': client_static_keypair,
            'e_skey_val': client_static_keypair,
            'e_skey_pkey': client_static_keypair,
            'cpm': '0',  # Contacts permission (default)
            'nbh': '0',  # Nearby share (default)
            'authkey': self._generate_auth_key(phone),
            'expid': self._generate_exp_id(),
            'fdid': device_id,
            'v': WHATSAPP_VERSION,
        }
        
        return params
    
    def _generate_device_id(self) -> str:
        """
        Generate a device ID.
        
        Returns:
            Device ID string
        """
        # Generate a random device ID
        device_id = ''.join(
            random.choice('0123456789abcdef') for _ in range(16)
        )
        return device_id
    
    def _generate_token(self, phone: str) -> str:
        """
        Generate a token for the registration request.
        
        Args:
            phone: Phone number
            
        Returns:
            Token string
        """
        # Generate a token based on the phone number
        data = phone.encode('utf-8')
        key = "WhatsApp Token Generation".encode('utf-8')
        
        # Create HMAC using SHA256
        token_hmac = hmac.new(key, data, hashlib.sha256)
        return base64.b64encode(token_hmac.digest()).decode('utf-8')
    
    def _generate_ref_key(self, phone: str) -> str:
        """
        Generate a reference key.
        
        Args:
            phone: Phone number
            
        Returns:
            Reference key string
        """
        # Generate a random reference key
        key_data = phone.encode('utf-8') + os.urandom(10)
        key_hash = hashlib.sha256(key_data).digest()
        return base64.b64encode(key_hash).decode('utf-8')
    
    def _generate_auth_key(self, phone: str) -> str:
        """
        Generate an auth key.
        
        Args:
            phone: Phone number
            
        Returns:
            Auth key string
        """
        # Generate a random auth key
        key_data = phone.encode('utf-8') + os.urandom(10)
        key_hash = hashlib.sha256(key_data).digest()
        return base64.b64encode(key_hash).decode('utf-8')
    
    def _generate_exp_id(self) -> str:
        """
        Generate an experiment ID.
        
        Returns:
            Experiment ID string
        """
        # Generate a random experiment ID
        exp_id = ''.join(
            random.choice('0123456789abcdef') for _ in range(8)
        )
        return exp_id
