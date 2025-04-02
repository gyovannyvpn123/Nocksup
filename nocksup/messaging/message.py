"""
Message handling for WhatsApp.

This module provides classes for WhatsApp message handling,
including message creation, sending, and parsing.
"""
import time
from enum import Enum
from typing import Dict, Any, Optional, Union, List

from nocksup.utils.logger import logger
from nocksup.utils import validate_phone_number, phone_to_jid
from nocksup.exceptions import MessageError, ValidationError
from nocksup.protocols.message_protocol import MessageProtocol
from nocksup.protocols.constants import MESSAGE_TYPES, WHATSAPP_DOMAIN

class MessageType(Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    
    @classmethod
    def from_string(cls, value: str) -> 'MessageType':
        """Convert string to MessageType."""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown message type: {value}")

class Message:
    """
    WhatsApp message representation.
    
    This class represents a WhatsApp message, providing methods
    for creating, sending, and parsing messages.
    """
    
    def __init__(self, message_type: Union[MessageType, str], to: str = None, 
                 content: Any = None, media_url: str = None, caption: str = None):
        """
        Initialize a new message.
        
        Args:
            message_type: Type of message
            to: Recipient phone number or JID
            content: Message content
            media_url: URL for media messages
            caption: Caption for media messages
        
        Raises:
            ValidationError: If message parameters are invalid
        """
        # Convert string type to enum if needed
        if isinstance(message_type, str):
            try:
                self.type = MessageType.from_string(message_type)
            except ValueError:
                raise ValidationError(f"Invalid message type: {message_type}")
        else:
            self.type = message_type
        
        # Validate recipient if provided
        self.to = None
        if to is not None:
            self.set_recipient(to)
        
        # Set content
        self.content = content
        self.media_url = media_url
        self.caption = caption
        
        # Message metadata
        self.id = None
        self.timestamp = None
        self.from_me = True
        self.status = 'pending'
        self.from_jid = None
        self.raw_data = None
        self.protocol = MessageProtocol()
    
    def set_recipient(self, to: str) -> None:
        """
        Set the message recipient.
        
        Args:
            to: Recipient phone number or JID
            
        Raises:
            ValidationError: If recipient is invalid
        """
        try:
            # Check if it's already a JID
            if '@' in to:
                self.to = to
            else:
                # Try to validate as phone number
                phone = validate_phone_number(to)
                self.to = phone_to_jid(phone, WHATSAPP_DOMAIN)
        except ValueError as e:
            raise ValidationError(f"Invalid recipient: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary.
        
        Returns:
            Dictionary representation of message
        """
        message_dict = {
            'type': self.type.value,
            'to': self.to,
            'timestamp': self.timestamp or int(time.time() * 1000),
            'from_me': self.from_me,
            'status': self.status
        }
        
        # Add content based on type
        if self.type == MessageType.TEXT:
            message_dict['content'] = self.content
        elif self.type in [MessageType.IMAGE, MessageType.VIDEO, 
                           MessageType.AUDIO, MessageType.DOCUMENT, 
                           MessageType.STICKER]:
            message_dict['media_url'] = self.media_url
            message_dict['caption'] = self.caption
            message_dict['media_type'] = self.type.value
        elif self.type == MessageType.LOCATION:
            # Location content should be a dict with lat, lng, name, address
            if isinstance(self.content, dict):
                message_dict.update({
                    'latitude': self.content.get('latitude'),
                    'longitude': self.content.get('longitude'),
                    'name': self.content.get('name'),
                    'address': self.content.get('address')
                })
        elif self.type == MessageType.CONTACT:
            # Contact content should be a list of contact dicts
            message_dict['contacts'] = self.content
        
        # Add message ID if available
        if self.id:
            message_dict['id'] = self.id
        
        return message_dict
    
    def prepare_for_sending(self) -> bytes:
        """
        Prepare message for sending.
        
        Returns:
            Encoded message ready for sending
            
        Raises:
            MessageError: If message preparation fails
            ValidationError: If message is invalid
        """
        # Validate message
        self._validate()
        
        try:
            # Convert to dictionary
            message_dict = self.to_dict()
            
            # Encode using protocol
            encoded = self.protocol.encode_message(message_dict)
            
            return encoded
            
        except Exception as e:
            logger.error(f"Failed to prepare message: {e}")
            raise MessageError(f"Failed to prepare message: {str(e)}")
    
    def _validate(self) -> None:
        """
        Validate message before sending.
        
        Raises:
            ValidationError: If message is invalid
        """
        # Check recipient
        if not self.to:
            raise ValidationError("No recipient specified")
        
        # Check content
        if self.type == MessageType.TEXT and not self.content:
            raise ValidationError("Text message with no content")
        
        # Check media URL for media messages
        if self.type in [MessageType.IMAGE, MessageType.VIDEO, 
                         MessageType.AUDIO, MessageType.DOCUMENT,
                         MessageType.STICKER] and not self.media_url:
            raise ValidationError(f"{self.type.value} message with no media URL")
        
        # Check location content
        if self.type == MessageType.LOCATION:
            if not isinstance(self.content, dict):
                raise ValidationError("Location content must be a dictionary")
            
            # Check required location fields
            if not all(k in self.content for k in ['latitude', 'longitude']):
                raise ValidationError("Location must have latitude and longitude")
        
        # Check contact content
        if self.type == MessageType.CONTACT:
            if not isinstance(self.content, list) or not self.content:
                raise ValidationError("Contact content must be a non-empty list")
    
    @classmethod
    def create_text_message(cls, to: str, text: str) -> 'Message':
        """
        Create a text message.
        
        Args:
            to: Recipient phone number or JID
            text: Message text
            
        Returns:
            Message object
        """
        return cls(MessageType.TEXT, to, text)
    
    @classmethod
    def create_image_message(cls, to: str, image_url: str, caption: str = None) -> 'Message':
        """
        Create an image message.
        
        Args:
            to: Recipient phone number or JID
            image_url: URL of the image
            caption: Optional caption
            
        Returns:
            Message object
        """
        return cls(MessageType.IMAGE, to, None, image_url, caption)
    
    @classmethod
    def create_video_message(cls, to: str, video_url: str, caption: str = None) -> 'Message':
        """
        Create a video message.
        
        Args:
            to: Recipient phone number or JID
            video_url: URL of the video
            caption: Optional caption
            
        Returns:
            Message object
        """
        return cls(MessageType.VIDEO, to, None, video_url, caption)
    
    @classmethod
    def create_audio_message(cls, to: str, audio_url: str) -> 'Message':
        """
        Create an audio message.
        
        Args:
            to: Recipient phone number or JID
            audio_url: URL of the audio file
            
        Returns:
            Message object
        """
        return cls(MessageType.AUDIO, to, None, audio_url)
    
    @classmethod
    def create_document_message(cls, to: str, document_url: str, 
                             caption: str = None) -> 'Message':
        """
        Create a document message.
        
        Args:
            to: Recipient phone number or JID
            document_url: URL of the document
            caption: Optional caption
            
        Returns:
            Message object
        """
        return cls(MessageType.DOCUMENT, to, None, document_url, caption)
    
    @classmethod
    def create_location_message(cls, to: str, latitude: float, longitude: float,
                             name: str = None, address: str = None) -> 'Message':
        """
        Create a location message.
        
        Args:
            to: Recipient phone number or JID
            latitude: Location latitude
            longitude: Location longitude
            name: Optional location name
            address: Optional location address
            
        Returns:
            Message object
        """
        location_data = {
            'latitude': latitude,
            'longitude': longitude,
            'name': name,
            'address': address
        }
        return cls(MessageType.LOCATION, to, location_data)
    
    @classmethod
    def create_contact_message(cls, to: str, contacts: List[Dict[str, str]]) -> 'Message':
        """
        Create a contact message.
        
        Args:
            to: Recipient phone number or JID
            contacts: List of contact dictionaries
            
        Returns:
            Message object
        """
        return cls(MessageType.CONTACT, to, contacts)
    
    @classmethod
    def create_sticker_message(cls, to: str, sticker_url: str) -> 'Message':
        """
        Create a sticker message.
        
        Args:
            to: Recipient phone number or JID
            sticker_url: URL of the sticker
            
        Returns:
            Message object
        """
        return cls(MessageType.STICKER, to, None, sticker_url)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from dictionary data.
        
        Args:
            data: Message data dictionary
            
        Returns:
            Message object
        """
        try:
            # Determine message type
            msg_type = data.get('type', 'text')
            
            # Create appropriate message based on type
            if msg_type == 'text':
                message = cls.create_text_message(
                    data.get('to'),
                    data.get('content', '')
                )
            elif msg_type in ['image', 'video', 'audio', 'document', 'sticker']:
                message = cls(
                    MessageType.from_string(msg_type),
                    data.get('to'),
                    None,
                    data.get('media_url'),
                    data.get('caption')
                )
            elif msg_type == 'location':
                message = cls.create_location_message(
                    data.get('to'),
                    data.get('latitude'),
                    data.get('longitude'),
                    data.get('name'),
                    data.get('address')
                )
            elif msg_type == 'contact':
                message = cls.create_contact_message(
                    data.get('to'),
                    data.get('contacts', [])
                )
            else:
                raise ValueError(f"Unknown message type: {msg_type}")
            
            # Set additional properties
            message.id = data.get('id')
            message.timestamp = data.get('timestamp')
            message.from_me = data.get('from_me', True)
            message.status = data.get('status', 'pending')
            message.from_jid = data.get('from')
            message.raw_data = data
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to create message from dict: {e}")
            raise MessageError(f"Failed to create message: {str(e)}")
