"""
Main client interface for Nocksup.

This module provides the main client interface for the Nocksup library,
including message sending, receiving, and connection management.
"""
import os
import logging
import json
import time
from typing import Dict, Any, List, Optional, Callable, Union

from nocksup.utils.logger import logger
from nocksup.exceptions import (
    ConnectionError, AuthenticationError, ValidationError, 
    MessageError, ContactError, GroupError, RegistrationError, VerificationError
)
from nocksup.protocols.connection import ConnectionManager
from nocksup.protocols.message_protocol import MessageProtocol
from nocksup.auth.registration import Registration

class NocksupClient:
    """
    Main client interface for Nocksup.
    
    This class provides a high-level interface for interacting with WhatsApp,
    including sending and receiving messages, managing contacts and groups,
    and handling media.
    """
    
    def __init__(self, phone_number: str = None, session_path: str = None, 
                log_level: int = None):
        """
        Initialize the client.
        
        Args:
            phone_number: User's phone number with country code
            session_path: Path to store session data
            log_level: Logging level to use
        """
        self.phone_number = phone_number
        self.session_path = session_path or os.path.expanduser('~/.nocksup')
        
        # Initialize protocol
        self.protocol = MessageProtocol()
        
        # Initialize connection manager
        self.connection = None
        
        # Initialize registration
        self.registration = Registration()
        
        # Callbacks
        self.message_callback = None
        self.qr_code_callback = None
        self.pairing_code_callback = None
        self.error_callback = None
        self.code_request_callback = None
        self.verification_callback = None
        
        # State
        self._is_connected = False
        
        logger.info("NocksupClient initialized")
    
    def connect(self, restore_session: bool = True, auth_method: str = 'qr',
               pairing_code: str = None, timeout: int = 60) -> bool:
        """
        Connect to WhatsApp servers.
        
        Args:
            restore_session: Try to restore previous session
            auth_method: Authentication method if restore fails ('qr' or 'pairing_code')
            pairing_code: Pairing code for authentication (required if auth_method is 'pairing_code')
            timeout: Timeout in seconds for authentication
            
        Returns:
            True if connected successfully
            
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
            ValidationError: If phone number is not set
        """
        if not self.phone_number:
            raise ValidationError("Phone number not set")
        
        # Initialize connection manager
        self.connection = ConnectionManager(
            on_message=self._on_message_received,
            on_error=self._on_error,
            on_close=self._on_connection_closed
        )
        
        # Connect to WhatsApp servers
        try:
            self.connection.connect()
            
            # Start authentication
            if auth_method == 'qr':
                # Generate QR code
                qr_data = self._generate_qr_code()
                if self.qr_code_callback:
                    self.qr_code_callback(qr_data)
                    
                # TODO: Wait for authentication
                # This would be implemented in real code
                # For now, we'll simulate waiting
                logger.info("Waiting for QR code scan...")
                
            elif auth_method == 'pairing_code':
                # Use pairing code
                if not pairing_code:
                    # Generate pairing code
                    pairing_code = self.generate_pairing_code()
                
                # TODO: Use pairing code for authentication
                # This would be implemented in real code
                # For now, we'll simulate waiting
                logger.info(f"Using pairing code: {pairing_code}")
                logger.info("Waiting for pairing...")
                
            else:
                raise ValidationError(f"Invalid authentication method: {auth_method}")
                
            # Authentication successful
            self._is_connected = True
            logger.info("Connected to WhatsApp")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._is_connected = False
            if isinstance(e, (ConnectionError, AuthenticationError)):
                raise
            else:
                raise ConnectionError(f"Failed to connect: {str(e)}")
    
    def disconnect(self) -> None:
        """
        Disconnect from WhatsApp servers.
        """
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
            finally:
                self.connection = None
        
        self._is_connected = False
        logger.info("Disconnected from WhatsApp")
    
    def is_connected(self) -> bool:
        """
        Check if connected to WhatsApp servers.
        
        Returns:
            True if connected
        """
        return self._is_connected and self.connection is not None
    
    def on_message(self, callback: Callable) -> None:
        """
        Register callback for received messages.
        
        Args:
            callback: Function to call when a message is received
        """
        self.message_callback = callback
    
    def on_error(self, callback: Callable) -> None:
        """
        Register callback for errors.
        
        Args:
            callback: Function to call when an error occurs
        """
        self.error_callback = callback
    
    def on_qr_code(self, callback: Callable) -> None:
        """
        Register callback for QR code generation.
        
        Args:
            callback: Function to call when a QR code is generated
        """
        self.qr_code_callback = callback
    
    def on_pairing_code(self, callback: Callable) -> None:
        """
        Register callback for pairing code generation.
        
        Args:
            callback: Function to call when a pairing code is generated
        """
        self.pairing_code_callback = callback
        
    def on_code_request(self, callback: Callable) -> None:
        """
        Register callback for code request results.
        
        Args:
            callback: Function to call when a code request completes
        """
        self.code_request_callback = callback
        
    def on_verification(self, callback: Callable) -> None:
        """
        Register callback for verification results.
        
        Args:
            callback: Function to call when verification completes
        """
        self.verification_callback = callback
    
    def generate_pairing_code(self) -> str:
        """
        Generate a pairing code for WhatsApp authentication.
        
        Returns:
            Pairing code
            
        Raises:
            ConnectionError: If not connected
        """
        # In a real implementation, this would generate a real pairing code
        # For now, we'll simulate it
        pairing_code = "12345678"
        
        if self.pairing_code_callback:
            self.pairing_code_callback(pairing_code)
            
        return pairing_code
        
    def request_code(self, method: str = 'sms', language: str = 'en', 
                    country_code: str = None) -> Dict[str, Any]:
        """
        Request a verification code via SMS or voice call.
        
        Args:
            method: Verification method ('sms' or 'voice')
            language: Language code for the message
            country_code: Two-letter country code (optional)
            
        Returns:
            Response from WhatsApp servers
            
        Raises:
            ValidationError: If phone number is not set
            RegistrationError: If code request fails
        """
        if not self.phone_number:
            raise ValidationError("Phone number not set")
            
        try:
            logger.info(f"Requesting verification code via {method}")
            
            result = self.registration.request_code(
                phone_number=self.phone_number,
                method=method,
                language=language,
                country_code=country_code
            )
            
            # Call the callback if registered
            if self.code_request_callback:
                self.code_request_callback(result)
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to request verification code: {e}")
            if isinstance(e, RegistrationError):
                raise
            else:
                raise RegistrationError(f"Failed to request verification code: {str(e)}")
    
    def verify_code(self, code: str) -> Dict[str, Any]:
        """
        Verify the received code to complete registration.
        
        Args:
            code: Verification code received
            
        Returns:
            Response from WhatsApp servers with account info
            
        Raises:
            ValidationError: If phone number is not set
            VerificationError: If verification fails
        """
        if not self.phone_number:
            raise ValidationError("Phone number not set")
            
        if not code:
            raise ValidationError("Verification code is required")
            
        try:
            logger.info("Verifying code")
            
            result = self.registration.verify_code(
                phone_number=self.phone_number,
                code=code
            )
            
            # Call the callback if registered
            if self.verification_callback:
                self.verification_callback(result)
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify code: {e}")
            if isinstance(e, VerificationError):
                raise
            else:
                raise VerificationError(f"Failed to verify code: {str(e)}")
    
    def send_text_message(self, recipient: str, text: str) -> str:
        """
        Send a text message.
        
        Args:
            recipient: Recipient's phone number with country code
            text: Message text
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If recipient or text is invalid
            MessageError: If message sending fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not recipient:
            raise ValidationError("Recipient is required")
            
        if not text:
            raise ValidationError("Message text is required")
        
        try:
            # Prepare message
            message = {
                'type': 'text',
                'recipient': recipient,
                'text': text
            }
            
            # Send message
            message_id = "msg_" + self.protocol.generate_message_id()
            
            logger.info(f"Sending text message to {recipient}: {text[:30]}...")
            
            # In a real implementation, this would send the message
            # For now, we'll simulate it
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            raise MessageError(f"Failed to send text message: {str(e)}")
            
    def send_image(self, recipient: str, image_path: str, caption: str = None) -> str:
        """
        Send an image message.
        
        Args:
            recipient: Recipient's phone number with country code
            image_path: Path to the image file
            caption: Optional caption for the image
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If recipient or image_path is invalid
            MessageError: If message sending fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not recipient:
            raise ValidationError("Recipient is required")
            
        if not image_path:
            raise ValidationError("Image path is required")
            
        if not os.path.exists(image_path):
            raise ValidationError(f"Image not found: {image_path}")
        
        try:
            # Prepare message
            message = {
                'type': 'image',
                'recipient': recipient,
                'image_path': image_path,
                'caption': caption
            }
            
            # Send message
            message_id = "msg_" + self.protocol.generate_message_id()
            
            logger.info(f"Sending image to {recipient}: {image_path}")
            
            # In a real implementation, this would upload and send the image
            # For now, we'll simulate it
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to send image: {e}")
            raise MessageError(f"Failed to send image: {str(e)}")
    
    def send_document(self, recipient: str, document_path: str, caption: str = None) -> str:
        """
        Send a document message.
        
        Args:
            recipient: Recipient's phone number with country code
            document_path: Path to the document file
            caption: Optional caption for the document
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If recipient or document_path is invalid
            MessageError: If message sending fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not recipient:
            raise ValidationError("Recipient is required")
            
        if not document_path:
            raise ValidationError("Document path is required")
            
        if not os.path.exists(document_path):
            raise ValidationError(f"Document not found: {document_path}")
        
        try:
            # Prepare message
            message = {
                'type': 'document',
                'recipient': recipient,
                'document_path': document_path,
                'caption': caption
            }
            
            # Send message
            message_id = "msg_" + self.protocol.generate_message_id()
            
            logger.info(f"Sending document to {recipient}: {document_path}")
            
            # In a real implementation, this would upload and send the document
            # For now, we'll simulate it
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            raise MessageError(f"Failed to send document: {str(e)}")
    
    def send_location(self, recipient: str, latitude: float, longitude: float, 
                     name: str = None, address: str = None) -> str:
        """
        Send a location message.
        
        Args:
            recipient: Recipient's phone number with country code
            latitude: Location latitude
            longitude: Location longitude
            name: Optional location name
            address: Optional location address
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If recipient, latitude, or longitude is invalid
            MessageError: If message sending fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not recipient:
            raise ValidationError("Recipient is required")
        
        try:
            # Prepare message
            message = {
                'type': 'location',
                'recipient': recipient,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'name': name,
                'address': address
            }
            
            # Send message
            message_id = "msg_" + self.protocol.generate_message_id()
            
            logger.info(f"Sending location to {recipient}: {latitude}, {longitude}")
            
            # In a real implementation, this would send the location
            # For now, we'll simulate it
            
            return message_id
        except ValueError:
            raise ValidationError("Latitude and longitude must be valid numbers")
        except Exception as e:
            logger.error(f"Failed to send location: {e}")
            raise MessageError(f"Failed to send location: {str(e)}")
    
    def create_group(self, subject: str, participants: List[str]) -> str:
        """
        Create a WhatsApp group.
        
        Args:
            subject: Group subject (name)
            participants: List of participant phone numbers
            
        Returns:
            Group ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If subject or participants are invalid
            GroupError: If group creation fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not subject:
            raise ValidationError("Group subject is required")
            
        if not participants or not isinstance(participants, list) or len(participants) < 1:
            raise ValidationError("At least one participant is required")
        
        try:
            # Prepare group creation request
            group_id = "group_" + self.protocol.generate_message_id()
            
            logger.info(f"Creating group '{subject}' with {len(participants)} participants")
            
            # In a real implementation, this would create the group
            # For now, we'll simulate it
            
            return group_id
        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            raise GroupError(f"Failed to create group: {str(e)}")
    
    def add_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Add participants to a WhatsApp group.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to add
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If group_id or participants are invalid
            GroupError: If adding participants fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not group_id:
            raise ValidationError("Group ID is required")
            
        if not participants or not isinstance(participants, list) or len(participants) < 1:
            raise ValidationError("At least one participant is required")
        
        try:
            logger.info(f"Adding {len(participants)} participants to group {group_id}")
            
            # In a real implementation, this would add participants to the group
            # For now, we'll simulate it
            
            return True
        except Exception as e:
            logger.error(f"Failed to add participants: {e}")
            raise GroupError(f"Failed to add participants: {str(e)}")
    
    def remove_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Remove participants from a WhatsApp group.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to remove
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If group_id or participants are invalid
            GroupError: If removing participants fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not group_id:
            raise ValidationError("Group ID is required")
            
        if not participants or not isinstance(participants, list) or len(participants) < 1:
            raise ValidationError("At least one participant is required")
        
        try:
            logger.info(f"Removing {len(participants)} participants from group {group_id}")
            
            # In a real implementation, this would remove participants from the group
            # For now, we'll simulate it
            
            return True
        except Exception as e:
            logger.error(f"Failed to remove participants: {e}")
            raise GroupError(f"Failed to remove participants: {str(e)}")
    
    def update_group_subject(self, group_id: str, subject: str) -> bool:
        """
        Update a WhatsApp group subject.
        
        Args:
            group_id: Group ID
            subject: New group subject
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If group_id or subject are invalid
            GroupError: If updating subject fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not group_id:
            raise ValidationError("Group ID is required")
            
        if not subject:
            raise ValidationError("Group subject is required")
        
        try:
            logger.info(f"Updating group {group_id} subject to '{subject}'")
            
            # In a real implementation, this would update the group subject
            # For now, we'll simulate it
            
            return True
        except Exception as e:
            logger.error(f"Failed to update group subject: {e}")
            raise GroupError(f"Failed to update group subject: {str(e)}")
    
    def get_contact(self, phone_number: str) -> Dict[str, Any]:
        """
        Get contact information.
        
        Args:
            phone_number: Phone number with country code
            
        Returns:
            Contact information
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If phone_number is invalid
            ContactError: If getting contact information fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
        
        if not phone_number:
            raise ValidationError("Phone number is required")
        
        try:
            logger.info(f"Getting contact information for {phone_number}")
            
            # In a real implementation, this would get contact information
            # For now, we'll simulate it
            contact_info = {
                'phone_number': phone_number,
                'name': f"Contact {phone_number}",
                'status': "Hey there! I am using WhatsApp.",
                'profile_picture': None,
                'last_seen': time.time()
            }
            
            return contact_info
        except Exception as e:
            logger.error(f"Failed to get contact: {e}")
            raise ContactError(f"Failed to get contact: {str(e)}")
    
    def get_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts.
        
        Returns:
            List of contact information
            
        Raises:
            ConnectionError: If not connected
            ContactError: If getting contacts fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
            
        try:
            logger.info("Getting all contacts")
            
            # In a real implementation, this would get all contacts
            # For now, we'll simulate it with empty contacts list
            contacts = []
            
            return contacts
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            raise ContactError(f"Failed to get contacts: {str(e)}")
    
    def download_media(self, message_id: str, output_path: str = None) -> str:
        """
        Download media from a message.
        
        Args:
            message_id: ID of the message containing media
            output_path: Path to save the media (optional)
            
        Returns:
            Path to the downloaded media
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If message_id is invalid
            MessageError: If downloading media fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
            
        if not message_id:
            raise ValidationError("Message ID is required")
            
        try:
            # If no output path is provided, use a default location
            if not output_path:
                output_dir = os.path.join(self.session_path, 'media')
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{message_id}_media")
                
            logger.info(f"Downloading media from message {message_id} to {output_path}")
            
            # In a real implementation, this would download the media
            # For now, we'll simulate it
            
            return output_path
        except Exception as e:
            logger.error(f"Failed to download media: {e}")
            raise MessageError(f"Failed to download media: {str(e)}")
    
    def check_phone_exists(self, phone_number: str) -> bool:
        """
        Check if a phone number exists on WhatsApp.
        
        Args:
            phone_number: Phone number with country code
            
        Returns:
            True if the phone number exists on WhatsApp
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If phone_number is invalid
            ContactError: If checking phone number fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
            
        if not phone_number:
            raise ValidationError("Phone number is required")
            
        try:
            logger.info(f"Checking if phone number {phone_number} exists on WhatsApp")
            
            # In a real implementation, this would check if the phone number exists
            # For now, we'll simulate it and assume it exists
            
            return True
        except Exception as e:
            logger.error(f"Failed to check phone number: {e}")
            raise ContactError(f"Failed to check phone number: {str(e)}")
    
    def send_audio(self, recipient: str, audio_path: str) -> str:
        """
        Send an audio message.
        
        Args:
            recipient: Recipient's phone number with country code
            audio_path: Path to the audio file
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If recipient or audio_path is invalid
            MessageError: If message sending fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
            
        if not recipient:
            raise ValidationError("Recipient is required")
            
        if not audio_path:
            raise ValidationError("Audio path is required")
            
        if not os.path.exists(audio_path):
            raise ValidationError(f"Audio not found: {audio_path}")
            
        try:
            # Prepare message
            message = {
                'type': 'audio',
                'recipient': recipient,
                'audio_path': audio_path
            }
            
            # Send message
            message_id = "msg_" + self.protocol.generate_message_id()
            
            logger.info(f"Sending audio to {recipient}: {audio_path}")
            
            # In a real implementation, this would upload and send the audio
            # For now, we'll simulate it
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            raise MessageError(f"Failed to send audio: {str(e)}")
    
    def send_video(self, recipient: str, video_path: str, caption: str = None) -> str:
        """
        Send a video message.
        
        Args:
            recipient: Recipient's phone number with country code
            video_path: Path to the video file
            caption: Optional caption for the video
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ValidationError: If recipient or video_path is invalid
            MessageError: If message sending fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp")
            
        if not recipient:
            raise ValidationError("Recipient is required")
            
        if not video_path:
            raise ValidationError("Video path is required")
            
        if not os.path.exists(video_path):
            raise ValidationError(f"Video not found: {video_path}")
            
        try:
            # Prepare message
            message = {
                'type': 'video',
                'recipient': recipient,
                'video_path': video_path,
                'caption': caption
            }
            
            # Send message
            message_id = "msg_" + self.protocol.generate_message_id()
            
            logger.info(f"Sending video to {recipient}: {video_path}")
            
            # In a real implementation, this would upload and send the video
            # For now, we'll simulate it
            
            return message_id
        except Exception as e:
            logger.error(f"Failed to send video: {e}")
            raise MessageError(f"Failed to send video: {str(e)}")
    
    def _on_message_received(self, message: Dict[str, Any]) -> None:
        """
        Handle received message.
        
        Args:
            message: Received message
        """
        logger.debug(f"Message received: {message}")
        
        if self.message_callback:
            try:
                self.message_callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
    
    def _on_error(self, error: Dict[str, Any]) -> None:
        """
        Handle error.
        
        Args:
            error: Error information
        """
        logger.error(f"Error received: {error}")
        
        if self.error_callback:
            try:
                self.error_callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def _on_connection_closed(self, reason: Dict[str, Any]) -> None:
        """
        Handle connection closure.
        
        Args:
            reason: Closure reason
        """
        logger.warning(f"Connection closed: {reason}")
        self._is_connected = False
    
    def _generate_qr_code(self) -> str:
        """
        Generate QR code for authentication.
        
        Returns:
            QR code data
        """
        # In a real implementation, this would generate a real QR code
        # For now, we'll simulate it
        qr_data = "simulated_qr_code_data"
        
        if self.qr_code_callback:
            self.qr_code_callback(qr_data)
            
        return qr_data