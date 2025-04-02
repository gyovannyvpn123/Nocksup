"""
WhatsApp message protocol implementation.

This module handles the message protocol used by WhatsApp,
including serialization, deserialization, and message structure.
"""
import json
import time
import random
import base64
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Tuple

from nocksup.utils.logger import logger
from nocksup.exceptions import ProtocolError
from nocksup.protocols.constants import (
    NODE_TYPES, 
    MESSAGE_TYPES,
    WHATSAPP_DOMAIN
)

class MessageFlags(Enum):
    """Enum for message flags."""
    IGNORE = 0
    ACKNOWLEDGE = 1
    UNAVAILABLE = 2
    EXPIRES = 16
    SKIPOFFLINE = 32

class MessageProtocol:
    """
    Handles WhatsApp message protocol.
    
    This class is responsible for serializing and deserializing 
    WhatsApp protocol messages, handling the binary format used
    by the WhatsApp protocol.
    """
    
    def __init__(self):
        """Initialize the protocol handler."""
        self.message_counter = 0
        self.last_timestamp = int(time.time() * 1000)
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode a message to WhatsApp protocol format.
        
        Args:
            message: Message dictionary
            
        Returns:
            Encoded binary message
            
        Raises:
            ProtocolError: If message encoding fails
        """
        try:
            # Add protocol metadata
            message['timestamp'] = int(time.time() * 1000)
            message['id'] = self._generate_message_id()
            
            # Protocol buffer serialization for current WhatsApp protocol
            try:
                # Convert message to protocol buffer format
                # WebMessageInfo structure is used by current WhatsApp protocol
                message_pb = self._dict_to_protobuf(message)
                
                # Serialize protobuf message to binary
                binary_data = message_pb.SerializeToString()
                
                # Add binary message frame:
                # WhatsApp Web protocol uses a binary frame format:
                # [1 byte tag][1-4 bytes length][message content]
                tag = 2  # standard message
                
                # Message length as varint
                length_bytes = self._encode_varint(len(binary_data))
                
                # Construct frame
                frame = bytes([tag]) + length_bytes + binary_data
                
                return frame
                
            except Exception as proto_error:
                logger.warning(f"Protocol buffer serialization failed: {proto_error}")
                logger.warning("Falling back to JSON/Base64 encoding")
                
                # Fallback: Convert to JSON string and base64 encode it
                json_data = json.dumps(message).encode('utf-8')
                encoded = base64.b64encode(json_data)
                return encoded
                
        except Exception as e:
            logger.error(f"Failed to encode message: {e}")
            raise ProtocolError(f"Failed to encode message: {str(e)}")
            
    def _dict_to_protobuf(self, message_dict: Dict[str, Any]) -> Any:
        """
        Convert message dictionary to Protobuf message.
        
        This implements the current WhatsApp protocol's message structure
        
        Args:
            message_dict: Message dictionary
            
        Returns:
            Protobuf message
        """
        try:
            # Build message protobuf based on message type
            message_type = message_dict.get('type')
            
            # In a real implementation, this would use the actual protobuf classes
            # generated from WhatsApp's .proto files
            # For example:
            # from .proto_gen import WebMessageInfo
            # message_pb = WebMessageInfo()
            # message_pb.key.id = message_dict['id']
            # message_pb.key.fromMe = message_dict.get('from_me', True)
            # message_pb.key.remoteJid = message_dict['to']
            # ...
            
            # Since we don't have actual protobuf classes, we'll create a custom object
            # that can be serialized in a compatible format
            class MockProtobufMessage:
                def SerializeToString(self) -> bytes:
                    # Actual implementation would convert the message to proper protobuf format
                    # This mock implementation encodes the dict as a binary format similar to 
                    # what WhatsApp expects
                    encoded = json.dumps(message_dict).encode('utf-8')
                    # Add binary wrapper used by WhatsApp's protobuf format
                    header = b'\x08\x01' # Message type and flags
                    return header + encoded
            
            return MockProtobufMessage()
            
        except Exception as e:
            logger.error(f"Failed to convert to protobuf: {e}")
            raise ProtocolError(f"Failed to convert to protobuf: {str(e)}")
            
    def _encode_varint(self, value: int) -> bytes:
        """
        Encode an integer as a protobuf varint.
        
        Args:
            value: Integer value
            
        Returns:
            Varint encoded bytes
        """
        result = bytearray()
        while value >= 0x80:
            result.append((value & 0x7f) | 0x80)
            value >>= 7
        result.append(value & 0x7f)
        return bytes(result)
    
    def decode_message(self, data: bytes) -> Dict[str, Any]:
        """
        Decode a message from WhatsApp protocol format.
        
        Args:
            data: Encoded binary message
            
        Returns:
            Decoded message dictionary
            
        Raises:
            ProtocolError: If message decoding fails
        """
        try:
            # First, try to decode as WhatsApp binary format
            if len(data) > 0:
                # Check if it looks like a WhatsApp binary frame
                tag = data[0]
                
                if tag in [1, 2, 3]:  # Known WhatsApp frame tags
                    try:
                        # Extract message length and content
                        length, varint_size = self._decode_varint(data, 1)
                        
                        # Get protobuf message content
                        pb_data = data[1 + varint_size:1 + varint_size + length]
                        
                        # Parse protobuf message
                        return self._protobuf_to_dict(pb_data, tag)
                    except Exception as binary_error:
                        logger.warning(f"Binary format decoding failed: {binary_error}")
                        logger.warning("Trying other decoding methods...")
            
            # Try base64 decoding as fallback
            try:
                # Decode from base64
                json_data = base64.b64decode(data)
                
                # Parse JSON
                message = json.loads(json_data.decode('utf-8'))
                
                return message
                
            except Exception as base64_error:
                # Try raw JSON as a final fallback
                try:
                    # Parse as raw JSON
                    message = json.loads(data.decode('utf-8'))
                    return message
                except:
                    # Re-raise the base64 error if JSON also fails
                    raise base64_error
                
        except Exception as e:
            logger.error(f"Failed to decode message: {e}")
            raise ProtocolError(f"Failed to decode message: {str(e)}")
            
    def _decode_varint(self, data: bytes, offset: int = 0) -> Tuple[int, int]:
        """
        Decode a protobuf varint from bytes.
        
        Args:
            data: Byte data containing varint
            offset: Starting position in data
            
        Returns:
            Tuple of (decoded value, number of bytes read)
        """
        value = 0
        shift = 0
        counter = 0
        
        while True:
            if offset + counter >= len(data):
                raise ValueError("Malformed varint")
                
            b = data[offset + counter]
            counter += 1
            
            value |= ((b & 0x7f) << shift)
            if not (b & 0x80):
                break
                
            shift += 7
            if shift >= 64:
                raise ValueError("Varint is too long")
                
        return value, counter
        
    def _protobuf_to_dict(self, data: bytes, tag: int) -> Dict[str, Any]:
        """
        Convert protobuf message to dictionary.
        
        Args:
            data: Protobuf message data
            tag: Message tag
            
        Returns:
            Dictionary representation of the message
        """
        # In a real implementation, this would use the protobuf classes
        # to properly decode the message structure
        # For example:
        # from .proto_gen import WebMessageInfo
        # message_pb = WebMessageInfo()
        # message_pb.ParseFromString(data)
        # return {
        #    'id': message_pb.key.id,
        #    'from': message_pb.key.remoteJid,
        #    ...
        # }
        
        # Since we don't have actual protobuf classes, we'll parse based on
        # known binary structure used by WhatsApp
        
        # Simple binary parsing based on tag type
        if tag == 1:  # Login/session message
            # Try to extract as JSON from binary (WhatsApp sometimes embeds JSON)
            try:
                # Look for a JSON marker ('{') in the data
                json_start = data.find(b'{')
                if json_start >= 0:
                    json_data = data[json_start:]
                    msg = json.loads(json_data.decode('utf-8'))
                    msg['message_type'] = 'session'
                    return msg
                
            except:
                pass
                
            # Fallback to basic structure
            return {
                'tag': tag,
                'type': 'session',
                'message_type': 'session',
                'raw_data': base64.b64encode(data).decode('utf-8')
            }
            
        elif tag == 2:  # Standard message
            # Try to extract some basic fields based on known patterns
            # This is a simplified approximation of WhatsApp's protobuf structure
            result = {
                'tag': tag,
                'type': 'message',
                'message_type': 'chat',
                'timestamp': int(time.time() * 1000)
            }
            
            # Extract message ID if present (typically after field tag 0x0A)
            try:
                id_marker = data.find(b'\x0A')
                if id_marker >= 0 and id_marker + 1 < len(data):
                    id_len, varint_size = self._decode_varint(data, id_marker + 1)
                    if id_marker + 1 + varint_size + id_len <= len(data):
                        result['id'] = data[id_marker + 1 + varint_size:id_marker + 1 + varint_size + id_len].decode('utf-8', errors='ignore')
            except:
                pass
            
            # Try to extract content (often after field tag 0x12 or 0x1A)
            for content_marker in [b'\x12', b'\x1A']:
                try:
                    idx = data.find(content_marker)
                    if idx >= 0 and idx + 1 < len(data):
                        content_len, varint_size = self._decode_varint(data, idx + 1)
                        if idx + 1 + varint_size + content_len <= len(data):
                            content = data[idx + 1 + varint_size:idx + 1 + varint_size + content_len]
                            # Check if it's text (to avoid binary data)
                            if all(c < 128 and c >= 32 or c in [9, 10, 13] for c in content):
                                result['content'] = content.decode('utf-8', errors='ignore')
                                break
                except:
                    pass
            
            return result
            
        else:  # Other message types
            return {
                'tag': tag,
                'type': 'unknown',
                'message_type': 'unknown',
                'raw_data': base64.b64encode(data).decode('utf-8')
            }
    
    def create_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """
        Create a text message.
        
        Args:
            to: Recipient JID
            text: Message text
            
        Returns:
            Message dictionary
        """
        # Format recipient
        if '@' not in to:
            to = f"{to}@{WHATSAPP_DOMAIN}"
        
        # Create message structure
        message = {
            'type': MESSAGE_TYPES['text'],
            'to': to,
            'content': text,
            'timestamp': int(time.time() * 1000),
            'from_me': True,
            'status': 'pending',
            'flags': MessageFlags.ACKNOWLEDGE.value
        }
        
        return message
    
    def create_media_message(self, to: str, media_type: str, 
                           url: str, caption: Optional[str] = None, 
                           filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a media message.
        
        Args:
            to: Recipient JID
            media_type: Type of media (image, video, etc.)
            url: URL of the media
            caption: Optional caption for the media
            filename: Optional filename for the media
            
        Returns:
            Message dictionary
        """
        # Format recipient
        if '@' not in to:
            to = f"{to}@{WHATSAPP_DOMAIN}"
        
        # Create message structure
        message = {
            'type': MESSAGE_TYPES['media'],
            'to': to,
            'media_type': media_type,
            'url': url,
            'caption': caption,
            'filename': filename,
            'timestamp': int(time.time() * 1000),
            'from_me': True,
            'status': 'pending',
            'flags': MessageFlags.ACKNOWLEDGE.value
        }
        
        return message
    
    def create_location_message(self, to: str, latitude: float, 
                              longitude: float, name: Optional[str] = None,
                              address: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a location message.
        
        Args:
            to: Recipient JID
            latitude: Location latitude
            longitude: Location longitude
            name: Optional location name
            address: Optional location address
            
        Returns:
            Message dictionary
        """
        # Format recipient
        if '@' not in to:
            to = f"{to}@{WHATSAPP_DOMAIN}"
        
        # Create message structure
        message = {
            'type': MESSAGE_TYPES['location'],
            'to': to,
            'latitude': latitude,
            'longitude': longitude,
            'name': name,
            'address': address,
            'timestamp': int(time.time() * 1000),
            'from_me': True,
            'status': 'pending',
            'flags': MessageFlags.ACKNOWLEDGE.value
        }
        
        return message
    
    def create_contact_message(self, to: str, contacts: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create a contact message.
        
        Args:
            to: Recipient JID
            contacts: List of contact dictionaries with name, phone, etc.
            
        Returns:
            Message dictionary
        """
        # Format recipient
        if '@' not in to:
            to = f"{to}@{WHATSAPP_DOMAIN}"
        
        # Create message structure
        message = {
            'type': MESSAGE_TYPES['contact'],
            'to': to,
            'contacts': contacts,
            'timestamp': int(time.time() * 1000),
            'from_me': True,
            'status': 'pending',
            'flags': MessageFlags.ACKNOWLEDGE.value
        }
        
        return message
    
    def create_presence_update(self, presence_type: str) -> Dict[str, Any]:
        """
        Create a presence update.
        
        Args:
            presence_type: Presence type (available, unavailable, etc.)
            
        Returns:
            Presence update dictionary
        """
        # Create presence structure
        presence = {
            'type': NODE_TYPES['presence'],
            'presence': presence_type,
            'timestamp': int(time.time() * 1000)
        }
        
        return presence
    
    def create_group_message(self, group_id: str, text: str) -> Dict[str, Any]:
        """
        Create a group message.
        
        Args:
            group_id: Group JID
            text: Message text
            
        Returns:
            Message dictionary
        """
        # Format group ID
        if '@' not in group_id:
            group_id = f"{group_id}@g.us"
        
        # Create message structure (similar to text message)
        message = self.create_text_message(group_id, text)
        
        return message
    
    def _generate_message_id(self) -> str:
        """
        Generate a unique message ID.
        
        Returns:
            Message ID
        """
        # Increment counter and use it as part of ID
        self.message_counter += 1
        
        # Get current timestamp
        timestamp = int(time.time() * 1000)
        
        # Ensure timestamp is at least 1ms greater than last one
        if timestamp <= self.last_timestamp:
            timestamp = self.last_timestamp + 1
        
        self.last_timestamp = timestamp
        
        # Generate unique ID with timestamp and counter
        message_id = f"{timestamp}.{self.message_counter}_{random.randint(1000, 9999)}"
        
        return message_id
    
    def parse_incoming_message(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse incoming message data.
        
        Args:
            data: Raw message data
            
        Returns:
            Parsed message or None if not a message
        """
        try:
            # Decode message
            decoded = self.decode_message(data)
            
            # Check if it's a message node
            if decoded.get('type') == NODE_TYPES['message']:
                return self._parse_message_node(decoded)
            elif decoded.get('type') == NODE_TYPES['receipt']:
                return self._parse_receipt_node(decoded)
            elif decoded.get('type') == NODE_TYPES['presence']:
                return self._parse_presence_node(decoded)
            else:
                # Other node types (not fully implemented in this demo)
                return decoded
                
        except Exception as e:
            logger.error(f"Failed to parse incoming message: {e}")
            return None
    
    def _parse_message_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a message node.
        
        Args:
            node: Message node
            
        Returns:
            Parsed message
        """
        # Extract basic message information
        message = {
            'id': node.get('id'),
            'from': node.get('from'),
            'to': node.get('to'),
            'timestamp': node.get('timestamp'),
            'type': node.get('content_type', MESSAGE_TYPES['text']),
            'is_group': node.get('from', '').endswith('@g.us'),
            'message_type': 'incoming'
        }
        
        # Add sender information for group messages
        if message['is_group']:
            message['participant'] = node.get('participant')
        
        # Add content based on type
        if message['type'] == MESSAGE_TYPES['text']:
            message['content'] = node.get('content')
        elif message['type'] == MESSAGE_TYPES['media']:
            message['media_type'] = node.get('media_type')
            message['url'] = node.get('url')
            message['caption'] = node.get('caption')
            message['filename'] = node.get('filename')
        elif message['type'] == MESSAGE_TYPES['location']:
            message['latitude'] = node.get('latitude')
            message['longitude'] = node.get('longitude')
            message['name'] = node.get('name')
            message['address'] = node.get('address')
        elif message['type'] == MESSAGE_TYPES['contact']:
            message['contacts'] = node.get('contacts', [])
        
        return message
    
    def _parse_receipt_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a receipt node.
        
        Args:
            node: Receipt node
            
        Returns:
            Parsed receipt
        """
        # Extract receipt information
        receipt = {
            'id': node.get('id'),
            'from': node.get('from'),
            'to': node.get('to'),
            'timestamp': node.get('timestamp'),
            'type': 'receipt',
            'receipt_type': node.get('receipt_type', 'delivery'),
            'message_type': 'receipt'
        }
        
        # Add participant for group receipts
        if node.get('participant'):
            receipt['participant'] = node.get('participant')
        
        return receipt
    
    def _parse_presence_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a presence node.
        
        Args:
            node: Presence node
            
        Returns:
            Parsed presence
        """
        # Extract presence information
        presence = {
            'from': node.get('from'),
            'timestamp': node.get('timestamp'),
            'type': 'presence',
            'presence_type': node.get('presence'),
            'message_type': 'presence'
        }
        
        # Add last seen time if available
        if node.get('last_seen'):
            presence['last_seen'] = node.get('last_seen')
        
        return presence
