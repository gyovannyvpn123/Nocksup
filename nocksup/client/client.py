"""
Main client interface for nocksup.

This module provides the main client class for interacting with
WhatsApp, serving as the primary interface for users of the library.
"""
import os
import time
from typing import Dict, Any, List, Optional, Callable, Union

from nocksup.utils.logger import logger, setup_logger
from nocksup.utils import validate_phone_number
from nocksup.exceptions import (
    ConnectionError, 
    AuthenticationError, 
    MessageError,
    ValidationError
)
from nocksup.auth.authentication import Authenticator
from nocksup.auth.registration import Registration
from nocksup.protocols.connection import ConnectionManager
from nocksup.messaging.message import Message, MessageType
from nocksup.messaging.media import MediaUploader, MediaDownloader
from nocksup.messaging.group import GroupManager
from nocksup.client.contact_manager import ContactManager
from nocksup.storage.session_store import SessionStore
from nocksup.storage.contact_store import ContactStore
from nocksup.config import ConfigManager

class NocksupClient:
    """
    Main client for WhatsApp interaction.
    
    This class provides a high-level interface to the WhatsApp protocol,
    allowing users to easily connect, send messages, and manage contacts
    and groups.
    """
    
    def __init__(self, phone_number: str = None, config_path: str = None, 
                 log_level: int = None, log_file: str = None):
        """
        Initialize the WhatsApp client.
        
        Args:
            phone_number: User's phone number with country code
            config_path: Path for configuration and data files
            log_level: Logging level
            log_file: Path to log file (if None, logs to console only)
        """
        # Set up logging
        self.logger = setup_logger('nocksup.client', log_level, log_file)
        
        # Configuration manager
        self.config = ConfigManager(config_path, log_level)
        
        # Initialize storage
        self.session_store = SessionStore(self.config.get('config_path'))
        self.contact_store = ContactStore(self.config.get('config_path'))
        
        # Set phone number if provided
        self.phone_number = None
        if phone_number:
            self.set_phone_number(phone_number)
        
        # Initialize managers (will be fully initialized on connect)
        self.connection = None
        self.authenticator = None
        self.registration = Registration()
        self.contact_manager = None
        self.group_manager = None
        self.media_uploader = MediaUploader()
        self.media_downloader = MediaDownloader()
        
        # Message callback registry
        self.message_callbacks = {}
        
        # Connection state
        self.connected = False
        
        logger.info("NocksupClient initialized")
    
    def set_phone_number(self, phone_number: str) -> None:
        """
        Set the user's phone number.
        
        Args:
            phone_number: User's phone number with country code
            
        Raises:
            ValidationError: If phone number is invalid
        """
        self.phone_number = validate_phone_number(phone_number)
        logger.info(f"Phone number set: {self.phone_number}")
    
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
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
            ValidationError: If phone number is not set
        """
        if not self.phone_number:
            raise ValidationError("Phone number not set")
        
        try:
            logger.info("Connecting to WhatsApp")
            
            # Initialize connection manager
            self.connection = ConnectionManager(
                on_message=self._on_message_received,
                on_error=self._on_connection_error,
                on_close=self._on_connection_closed
            )
            
            # Initialize authenticator
            self.authenticator = Authenticator(
                self.phone_number,
                self.session_store
            )
            
            # Authenticate with specified method
            auth_success = self.authenticator.connect(
                restore_session=restore_session,
                auth_method=auth_method,
                pairing_code=pairing_code
            )
            
            if auth_success:
                # Initialize other managers now that we're connected
                self.contact_manager = ContactManager(self.connection, self.contact_store)
                self.group_manager = GroupManager(self.connection)
                
                # Connect to WebSocket server
                self.connection.connect()
                
                # Register for messages
                self._register_message_handlers()
                
                self.connected = True
                logger.info("Connected to WhatsApp")
                return True
            else:
                logger.error("Authentication failed")
                raise AuthenticationError("Failed to authenticate with WhatsApp")
                
        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to WhatsApp: {str(e)}")
    
    def disconnect(self) -> None:
        """Disconnect from WhatsApp servers."""
        if self.connected:
            logger.info("Disconnecting from WhatsApp")
            
            if self.connection:
                self.connection.disconnect()
            
            if self.authenticator:
                self.authenticator.disconnect()
            
            self.connected = False
            logger.info("Disconnected from WhatsApp")
    
    def register_number(self, method: str = 'sms', 
                      language: str = 'en', country_code: str = None) -> Dict[str, Any]:
        """
        Register phone number with WhatsApp.
        
        Args:
            method: Verification method ('sms' or 'voice')
            language: Language code for the message
            country_code: Two-letter country code (optional)
            
        Returns:
            Response from registration request
            
        Raises:
            ValidationError: If phone number is not set
        """
        if not self.phone_number:
            raise ValidationError("Phone number not set")
        
        logger.info(f"Registering phone number: {self.phone_number}")
        return self.registration.request_code(
            self.phone_number, method, language, country_code
        )
    
    def verify_code(self, code: str) -> Dict[str, Any]:
        """
        Verify registration code.
        
        Args:
            code: Verification code received
            
        Returns:
            Response from verification request
            
        Raises:
            ValidationError: If phone number is not set
        """
        if not self.phone_number:
            raise ValidationError("Phone number not set")
        
        logger.info(f"Verifying code for {self.phone_number}")
        return self.registration.verify_code(self.phone_number, code)
    
    def send_text_message(self, to: str, text: str) -> str:
        """
        Send text message.
        
        Args:
            to: Recipient phone number or JID
            text: Message text
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Create message
            message = Message.create_text_message(to, text)
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send message")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            raise MessageError(f"Failed to send text message: {str(e)}")
    
    def send_image(self, to: str, image_path: str, caption: str = None) -> str:
        """
        Send image message.
        
        Args:
            to: Recipient phone number or JID
            image_path: Path to image file
            caption: Optional caption
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Upload media
            logger.info(f"Uploading image: {image_path}")
            media_info = self.media_uploader.upload(image_path, "image")
            
            # Create message
            message = Message.create_image_message(to, media_info['media_url'], caption)
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send image")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send image message: {e}")
            raise MessageError(f"Failed to send image message: {str(e)}")
    
    def send_video(self, to: str, video_path: str, caption: str = None) -> str:
        """
        Send video message.
        
        Args:
            to: Recipient phone number or JID
            video_path: Path to video file
            caption: Optional caption
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Upload media
            logger.info(f"Uploading video: {video_path}")
            media_info = self.media_uploader.upload(video_path, "video")
            
            # Create message
            message = Message.create_video_message(to, media_info['media_url'], caption)
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send video")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send video message: {e}")
            raise MessageError(f"Failed to send video message: {str(e)}")
    
    def send_audio(self, to: str, audio_path: str) -> str:
        """
        Send audio message.
        
        Args:
            to: Recipient phone number or JID
            audio_path: Path to audio file
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Upload media
            logger.info(f"Uploading audio: {audio_path}")
            media_info = self.media_uploader.upload(audio_path, "audio")
            
            # Create message
            message = Message.create_audio_message(to, media_info['media_url'])
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send audio")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send audio message: {e}")
            raise MessageError(f"Failed to send audio message: {str(e)}")
    
    def send_document(self, to: str, document_path: str, caption: str = None) -> str:
        """
        Send document message.
        
        Args:
            to: Recipient phone number or JID
            document_path: Path to document file
            caption: Optional caption
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Upload media
            logger.info(f"Uploading document: {document_path}")
            media_info = self.media_uploader.upload(document_path, "document")
            
            # Create message
            message = Message.create_document_message(to, media_info['media_url'], caption)
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send document")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send document message: {e}")
            raise MessageError(f"Failed to send document message: {str(e)}")
    
    def send_location(self, to: str, latitude: float, longitude: float,
                    name: str = None, address: str = None) -> str:
        """
        Send location message.
        
        Args:
            to: Recipient phone number or JID
            latitude: Location latitude
            longitude: Location longitude
            name: Optional location name
            address: Optional location address
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Create message
            message = Message.create_location_message(to, latitude, longitude, name, address)
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send location")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send location message: {e}")
            raise MessageError(f"Failed to send location message: {str(e)}")
    
    def send_contact(self, to: str, contacts: List[Dict[str, str]]) -> str:
        """
        Send contact message.
        
        Args:
            to: Recipient phone number or JID
            contacts: List of contact dictionaries
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            MessageError: If message sending fails
        """
        self._ensure_connected()
        
        try:
            # Create message
            message = Message.create_contact_message(to, contacts)
            
            # Prepare for sending
            encoded = message.prepare_for_sending()
            
            # Send message
            success = self.connection.send_message(encoded)
            
            if not success:
                raise MessageError("Failed to send contacts")
            
            return message.id
            
        except Exception as e:
            logger.error(f"Failed to send contact message: {e}")
            raise MessageError(f"Failed to send contact message: {str(e)}")
    
    def create_group(self, subject: str, participants: List[str]) -> Dict[str, Any]:
        """
        Create a new WhatsApp group.
        
        Args:
            subject: Group name
            participants: List of participant phone numbers
            
        Returns:
            Group information including group ID
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.create_group(subject, participants)
    
    def add_group_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Add participants to a group.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to add
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.add_participants(group_id, participants)
    
    def remove_group_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Remove participants from a group.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to remove
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.remove_participants(group_id, participants)
    
    def leave_group(self, group_id: str) -> bool:
        """
        Leave a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.leave_group(group_id)
    
    def get_group_info(self, group_id: str) -> Dict[str, Any]:
        """
        Get information about a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            Group information
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.get_group_info(group_id)
    
    def update_group_subject(self, group_id: str, subject: str) -> bool:
        """
        Update group subject.
        
        Args:
            group_id: Group ID
            subject: New group subject
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.update_subject(group_id, subject)
    
    def promote_group_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Promote participants to group admins.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to promote
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.promote_participants(group_id, participants)
    
    def demote_group_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Demote participants from group admins.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to demote
            
        Returns:
            True if successful
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.group_manager.demote_participants(group_id, participants)
    
    def get_contact(self, phone_number: str) -> Dict[str, Any]:
        """
        Get contact information.
        
        Args:
            phone_number: Contact phone number
            
        Returns:
            Contact information
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.contact_manager.get_contact(phone_number)
    
    def get_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts.
        
        Returns:
            List of contact information
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.contact_manager.get_contacts()
    
    def check_phone_exists(self, phone_number: str) -> bool:
        """
        Check if a phone number exists on WhatsApp.
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            True if the number exists on WhatsApp
            
        Raises:
            ConnectionError: If not connected
        """
        self._ensure_connected()
        return self.contact_manager.check_phone_exists(phone_number)
    
    def download_media(self, media_url: str, output_path: str, 
                     media_key: str = None) -> str:
        """
        Download media from a message.
        
        Args:
            media_url: URL of the media
            output_path: Path to save the file
            media_key: Optional media key for decryption
            
        Returns:
            Path to downloaded file
        """
        return self.media_downloader.download(media_url, output_path, media_key)
    
    def on_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for all messages.
        
        Args:
            callback: Function to call when a message is received
        """
        self.message_callbacks['*'] = callback
    
    def on_text_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for text messages.
        
        Args:
            callback: Function to call when a text message is received
        """
        self.message_callbacks['text'] = callback
    
    def on_image_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for image messages.
        
        Args:
            callback: Function to call when an image message is received
        """
        self.message_callbacks['image'] = callback
    
    def on_video_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for video messages.
        
        Args:
            callback: Function to call when a video message is received
        """
        self.message_callbacks['video'] = callback
    
    def on_audio_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for audio messages.
        
        Args:
            callback: Function to call when an audio message is received
        """
        self.message_callbacks['audio'] = callback
    
    def on_document_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for document messages.
        
        Args:
            callback: Function to call when a document message is received
        """
        self.message_callbacks['document'] = callback
    
    def on_location_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for location messages.
        
        Args:
            callback: Function to call when a location message is received
        """
        self.message_callbacks['location'] = callback
    
    def on_contact_message(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for contact messages.
        
        Args:
            callback: Function to call when a contact message is received
        """
        self.message_callbacks['contact'] = callback
    
    def _ensure_connected(self) -> None:
        """
        Ensure that client is connected.
        
        Raises:
            ConnectionError: If not connected
        """
        if not self.connected or not self.connection or not self.connection.is_connected():
            logger.error("Not connected to WhatsApp")
            raise ConnectionError("Not connected to WhatsApp")
    
    def _register_message_handlers(self) -> None:
        """Register message handlers with the connection manager."""
        if self.connection:
            # Register handlers for different message types
            self.connection.register_handler('text', self._handle_text_message)
            self.connection.register_handler('image', self._handle_media_message)
            self.connection.register_handler('video', self._handle_media_message)
            self.connection.register_handler('audio', self._handle_media_message)
            self.connection.register_handler('document', self._handle_media_message)
            self.connection.register_handler('location', self._handle_location_message)
            self.connection.register_handler('contact', self._handle_contact_message)
    
    def _on_message_received(self, message: Dict[str, Any]) -> None:
        """
        Handle received message.
        
        Args:
            message: Message data
        """
        # Call callback for all messages if registered
        if '*' in self.message_callbacks:
            self.message_callbacks['*'](message)
        
        # Call type-specific callback if registered
        message_type = message.get('type')
        if message_type in self.message_callbacks:
            self.message_callbacks[message_type](message)
    
    def _handle_text_message(self, message: Dict[str, Any]) -> None:
        """
        Handle text message.
        
        Args:
            message: Message data
        """
        # Process text message
        if 'text' in self.message_callbacks:
            self.message_callbacks['text'](message)
    
    def _handle_media_message(self, message: Dict[str, Any]) -> None:
        """
        Handle media message.
        
        Args:
            message: Message data
        """
        # Process media message based on type
        media_type = message.get('media_type')
        if media_type in self.message_callbacks:
            self.message_callbacks[media_type](message)
    
    def _handle_location_message(self, message: Dict[str, Any]) -> None:
        """
        Handle location message.
        
        Args:
            message: Message data
        """
        # Process location message
        if 'location' in self.message_callbacks:
            self.message_callbacks['location'](message)
    
    def _handle_contact_message(self, message: Dict[str, Any]) -> None:
        """
        Handle contact message.
        
        Args:
            message: Message data
        """
        # Process contact message
        if 'contact' in self.message_callbacks:
            self.message_callbacks['contact'](message)
    
    def _on_connection_error(self, error: Exception) -> None:
        """
        Handle connection error.
        
        Args:
            error: Error data
        """
        logger.error(f"Connection error: {error}")
        # Try to reconnect
        if self.connected:
            self.connected = False
            self._try_reconnect()
    
    def _on_connection_closed(self) -> None:
        """Handle connection closure."""
        logger.info("Connection closed")
        if self.connected:
            self.connected = False
            self._try_reconnect()
    
    def _try_reconnect(self) -> None:
        """Try to reconnect to WhatsApp."""
        # Try to reconnect a few times
        for attempt in range(3):
            try:
                logger.info(f"Reconnect attempt {attempt + 1}")
                time.sleep(5 * (attempt + 1))  # Exponential backoff
                
                # Reconnect
                if self.connect(restore_session=True):
                    logger.info("Reconnected successfully")
                    return
                    
            except Exception as e:
                logger.error(f"Reconnection attempt failed: {e}")
        
        logger.error("Failed to reconnect after multiple attempts")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
