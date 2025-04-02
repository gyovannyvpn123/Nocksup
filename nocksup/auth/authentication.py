"""
Authentication implementation for WhatsApp.

This module handles WhatsApp authentication, session management,
and login functionality.
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional, Tuple

# Make sure websocket-client is installed
try:
    import websocket
except ImportError:
    raise ImportError("websocket-client package is required. Install it using 'pip install websocket-client'.")

from nocksup.utils.encryption import EncryptionManager, generate_random_bytes
from nocksup.utils.http_utils import HttpClient
from nocksup.utils.logger import logger
from nocksup.exceptions import AuthenticationError
from nocksup.storage.session_store import SessionStore
from nocksup.protocols.constants import WHATSAPP_WEB_VERSION

class Authenticator:
    """
    WhatsApp authentication manager.
    
    Handles authentication with WhatsApp servers, including
    QR authentication and reconnection with existing sessions.
    """
    
    def __init__(self, phone_number: str, session_store: SessionStore, 
                 encryption_manager: EncryptionManager = None):
        """
        Initialize authenticator.
        
        Args:
            phone_number: User's phone number with country code
            session_store: Storage for session data
            encryption_manager: Optional encryption manager
        """
        self.phone_number = phone_number
        self.session_store = session_store
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.http_client = HttpClient()
        self.ws = None
        self.connected = False
        self.credentials = None
        
    def connect(self, restore_session: bool = True, auth_method: str = 'qr', pairing_code: str = None) -> bool:
        """
        Connect to WhatsApp servers.
        
        Args:
            restore_session: Try to restore previous session
            auth_method: Authentication method if restore fails ('qr' or 'pairing_code')
            pairing_code: Pairing code for authentication (required if auth_method is 'pairing_code')
            
        Returns:
            True if connected successfully
        
        Raises:
            AuthenticationError: If authentication fails
        """
        # Try to restore session if requested
        if restore_session:
            self.credentials = self.session_store.load_session(self.phone_number)
            if self.credentials:
                logger.info("Attempting to restore previous session")
                try:
                    return self._restore_session()
                except AuthenticationError as e:
                    logger.warning(f"Session restore failed: {e}")
                    # Continue with fresh login if restore fails
        
        # Fresh login with specified authentication method
        return self._login(auth_method=auth_method, pairing_code=pairing_code)
    
    def _login(self, auth_method: str = 'qr', pairing_code: str = None) -> bool:
        """
        Perform fresh login process.
        
        Args:
            auth_method: Authentication method ('qr' or 'pairing_code')
            pairing_code: Pairing code for authentication (required if auth_method is 'pairing_code')
        
        Returns:
            True if login successful
        
        Raises:
            AuthenticationError: If login fails
        """
        # Initialize WebSocket connection
        try:
            self._init_websocket()
            
            # Generate client keys
            client_id = base64.b64encode(generate_random_bytes(16)).decode('utf-8')
            client_token = generate_random_bytes(32)
            
            if auth_method == 'qr':
                # Generate QR code and wait for scan
                qr_info = self._generate_qr(client_id, client_token)
                logger.info("QR code generated, waiting for scan")
                
                # At this point, the user would scan the QR code
                # We would wait for authentication messages on the WebSocket
                success = self._wait_for_auth()
                
            elif auth_method == 'pairing_code':
                if not pairing_code:
                    raise AuthenticationError("Pairing code is required for pairing_code auth method")
                
                # Generate pairing with code
                pairing_info = self._generate_pairing(client_id, client_token, pairing_code)
                logger.info("Pairing code sent, waiting for authentication")
                
                # Wait for authentication after pairing code submission
                success = self._wait_for_auth()
                
            else:
                raise AuthenticationError(f"Unknown authentication method: {auth_method}")
            
            if success:
                # Save the session for future use
                self.session_store.save_session(self.phone_number, self.credentials)
                self.connected = True
                return True
            else:
                raise AuthenticationError("Authentication timeout or rejected")
                
        except (websocket.WebSocketException, OSError) as e:
            logger.error(f"WebSocket connection error: {e}")
            raise AuthenticationError(f"Failed to connect: {str(e)}")
    
    def _restore_session(self) -> bool:
        """
        Restore an existing session.
        
        Returns:
            True if session restored successfully
        
        Raises:
            AuthenticationError: If session restore fails
        """
        if not self.credentials:
            raise AuthenticationError("No credentials to restore")
        
        try:
            self._init_websocket()
            
            # Send session restore message
            restore_message = {
                "clientId": self.credentials.get("client_id"),
                "clientToken": self.credentials.get("client_token"),
                "serverToken": self.credentials.get("server_token"),
                "browserToken": self.credentials.get("browser_token"),
                "phoneId": self.credentials.get("phone_id"),
                "loginTime": int(time.time() * 1000)
            }
            
            self.ws.send(json.dumps(restore_message))
            
            # Wait for restore response
            success = self._wait_for_restore()
            
            if success:
                self.connected = True
                return True
            else:
                raise AuthenticationError("Session restore failed or rejected")
                
        except (websocket.WebSocketException, OSError) as e:
            logger.error(f"WebSocket connection error during restore: {e}")
            raise AuthenticationError(f"Failed to restore session: {str(e)}")
    
    def _init_websocket(self) -> None:
        """
        Initialize WebSocket connection to WhatsApp servers.
        
        Raises:
            AuthenticationError: If connection fails
        """
        try:
            # Connect to WhatsApp WebSocket server using updated URL for current protocol
            # Use /ws/chat endpoint for current WhatsApp Web
            ws_url = "wss://web.whatsapp.com/ws/chat"
            
            # Connection headers with updated browser info
            headers = {
                "Origin": "https://web.whatsapp.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
                "Sec-WebSocket-Version": "13",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
            
            # Create WebSocket connection with updated parameters
            self.ws = websocket.create_connection(
                ws_url, 
                header=headers,
                enable_multithread=True,
                timeout=30
            )
            logger.info("WebSocket connection established")
            
        except (websocket.WebSocketException, OSError) as e:
            logger.error(f"WebSocket connection error: {e}")
            raise AuthenticationError(f"Failed to connect to WhatsApp: {str(e)}")
    
    def _generate_qr(self, client_id: str, client_token: bytes) -> Dict[str, Any]:
        """
        Generate authentication QR code data.
        
        Args:
            client_id: Client ID
            client_token: Client token
            
        Returns:
            QR code data
        """
        # Generate keys for authentication
        keys = self.encryption_manager.generate_keys()
        
        # Create a QR string with the essential components
        qr_components = [
            self.phone_number,
            base64.b64encode(client_token).decode('utf-8'),
            client_id,
            base64.b64encode(keys['identity_public']).decode('utf-8')
        ]
        
        qr_string = ",".join(qr_components)
        
        # This QR string would be encoded as a QR code for the user to scan
        qr_data = {
            "qr_string": qr_string,
            "client_id": client_id,
            "client_token": client_token,
            "keys": keys
        }
        
        logger.info("Generated QR code data")
        
        return qr_data
        
    def _generate_pairing(self, client_id: str, client_token: bytes, pairing_code: str) -> Dict[str, Any]:
        """
        Generate pairing request using a pairing code.
        
        Args:
            client_id: Client ID
            client_token: Client token
            pairing_code: The 8-digit pairing code from WhatsApp mobile app
            
        Returns:
            Pairing info data
        """
        # Generate keys for authentication
        keys = self.encryption_manager.generate_keys()
        
        # Format the pairing code (remove any hyphens or spaces)
        formatted_code = pairing_code.replace('-', '').replace(' ', '')
        
        # Validate the pairing code format (should be 8 digits)
        if not formatted_code.isdigit() or len(formatted_code) != 8:
            raise AuthenticationError("Invalid pairing code format. Should be 8 digits.")
            
        # Create a pairing request for the WhatsApp server
        pairing_request = {
            "clientId": client_id,
            "clientToken": base64.b64encode(client_token).decode('utf-8'),
            "phoneNumber": self.phone_number,
            "pairingCode": formatted_code,
            "publicKey": base64.b64encode(keys['identity_public']).decode('utf-8'),
            "deviceName": "NocksupClient",  # Device name shown in WhatsApp linked devices
            "authMethod": "pairing_code"
        }
        
        # In a real implementation, this would be sent to the WebSocket
        # Here we just prepare it and simulate sending
        if self.ws:
            self.ws.send(json.dumps(pairing_request))
            logger.info(f"Pairing code request sent for number {self.phone_number}")
        else:
            raise AuthenticationError("WebSocket connection not established")
        
        # Return pairing info for reference
        pairing_info = {
            "client_id": client_id,
            "client_token": client_token,
            "pairing_code": formatted_code,
            "keys": keys
        }
        
        return pairing_info
    
    def _wait_for_auth(self) -> bool:
        """
        Wait for authentication confirmation.
        
        Returns:
            True if authenticated successfully
        """
        # In a real implementation, this would listen for WebSocket messages
        # and process them according to WhatsApp's protocol
        
        # For this sample implementation, we'll simulate a success response
        # after a timeout to represent a user scanning the QR code
        
        # Timeout after 60 seconds
        timeout = time.time() + 60
        
        try:
            while time.time() < timeout:
                # Check for messages with a short timeout
                self.ws.settimeout(1)
                try:
                    message = self.ws.recv()
                    
                    # Parse the message
                    data = json.loads(message)
                    
                    # Check if it's an authentication confirmation
                    if data.get("status") == "connected":
                        # Store credentials from response
                        self.credentials = {
                            "client_id": data.get("clientId"),
                            "client_token": data.get("clientToken"),
                            "server_token": data.get("serverToken"),
                            "browser_token": data.get("browserToken"),
                            "phone_id": data.get("phoneId"),
                            "secret": data.get("secret"),
                            "public_key": data.get("publicKey"),
                            "private_key": data.get("privateKey"),
                        }
                        
                        logger.info("Authentication successful")
                        return True
                        
                except websocket.WebSocketTimeoutException:
                    # No message received within timeout, continue waiting
                    pass
                    
            # Timeout elapsed without successful authentication
            logger.warning("Authentication timeout")
            return False
            
        except websocket.WebSocketException as e:
            logger.error(f"WebSocket error during authentication: {e}")
            return False
    
    def _wait_for_restore(self) -> bool:
        """
        Wait for session restore confirmation.
        
        Returns:
            True if session restored successfully
        """
        # Similar to _wait_for_auth, but for session restore
        
        # Timeout after 30 seconds
        timeout = time.time() + 30
        
        try:
            while time.time() < timeout:
                # Check for messages with a short timeout
                self.ws.settimeout(1)
                try:
                    message = self.ws.recv()
                    
                    # Parse the message
                    data = json.loads(message)
                    
                    # Check if it's a restore confirmation
                    if data.get("status") == "connected":
                        logger.info("Session restored successfully")
                        return True
                        
                except websocket.WebSocketTimeoutException:
                    # No message received within timeout, continue waiting
                    pass
                    
            # Timeout elapsed without successful restore
            logger.warning("Session restore timeout")
            return False
            
        except websocket.WebSocketException as e:
            logger.error(f"WebSocket error during session restore: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from WhatsApp servers."""
        if self.ws:
            self.ws.close()
            self.connected = False
            logger.info("Disconnected from WhatsApp")
            
    def is_connected(self) -> bool:
        """Check if connected to WhatsApp servers."""
        return self.connected
