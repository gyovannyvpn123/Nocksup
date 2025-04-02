"""
WhatsApp message protocol implementation.

This module handles the message protocol used by WhatsApp,
including serialization, deserialization, and message structure.
"""
import json
import time
import random
import base64
import struct
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Tuple

from nocksup.utils.logger import logger
from nocksup.exceptions import ProtocolError
from nocksup.protocols.constants import (
    NODE_TYPES, 
    MESSAGE_TYPES,
    WHATSAPP_DOMAIN,
    WHATSAPP_WEB_VERSION
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
            if 'id' not in message:
                message['id'] = self.generate_message_id()
            
            # For 2025 WhatsApp protocol: Binary format
            try:
                # Serialize message to binary format using the new protocol
                # We'll use a simple format for now:
                # [1 byte message type][4 bytes length][JSON data]
                
                # Convert message to JSON
                json_data = json.dumps(message).encode('utf-8')
                
                # Message type: 1 = normal message
                message_type = 1
                
                # Message length
                length = len(json_data)
                length_bytes = struct.pack('>I', length)
                
                # Construct frame
                frame = bytes([message_type]) + length_bytes + json_data
                
                return frame
                
            except Exception as proto_error:
                logger.warning(f"Binary serialization failed: {proto_error}")
                logger.warning("Falling back to JSON encoding")
                
                # Fallback: Convert to JSON string
                json_data = json.dumps(message).encode('utf-8')
                return json_data
                
        except Exception as e:
            logger.error(f"Failed to encode message: {e}")
            raise ProtocolError(f"Failed to encode message: {str(e)}")
    
    def decode_message(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Decode a message from WhatsApp protocol format.
        
        Args:
            data: Encoded binary message
            
        Returns:
            Decoded message dictionary or None if decoding fails
            
        Raises:
            ProtocolError: If message decoding fails
        """
        try:
            # First, try to parse as binary format
            try:
                # Noul format WhatsApp 2025
                # Verificăm dacă avem lungime adecvată pentru header-ul nostru
                if len(data) >= 5:  # 1 byte type + 4 bytes length
                    # Extragem tipul mesajului și lungimea
                    message_type = data[0]
                    length = struct.unpack('>I', data[1:5])[0]
                    
                    # Verificăm dacă avem suficienți octeți pentru întregul mesaj
                    if len(data) >= 5 + length:
                        # Extragem și decodăm payload-ul JSON
                        json_data = data[5:5+length]
                        try:
                            return json.loads(json_data.decode('utf-8'))
                        except UnicodeDecodeError:
                            # Dacă nu putem decoda ca UTF-8, încercăm să tratăm partea binară diferit
                            logger.warning("UTF-8 decoding failed, trying alternative approach")
                            
                            # Facem un dump hex pentru debugging
                            hex_dump = json_data.hex()
                            logger.debug(f"Binary data (hex): {hex_dump[:100]}...")
                            
                            # Încercăm să găsim începutul unui JSON valid
                            json_start = json_data.find(b'{')
                            if json_start >= 0:
                                try:
                                    return json.loads(json_data[json_start:].decode('utf-8', errors='ignore'))
                                except json.JSONDecodeError:
                                    logger.warning("JSON decoding failed after finding JSON start")
                            
                            # Încercăm să decodăm ca base64
                            try:
                                decoded = base64.b64decode(json_data)
                                return {'type': 'binary', 'data': decoded}
                            except:
                                logger.warning("Base64 decoding failed")
                
                # Dacă nu am reușit încă, încercăm să vedem dacă întregul pachet este un JSON
                return json.loads(data.decode('utf-8', errors='ignore'))
                    
            except (struct.error, json.JSONDecodeError) as e:
                logger.warning(f"Binary format parsing failed: {e}")
                
                # Try to decode as JSON
                try:
                    # First try UTF-8 decoding
                    return json.loads(data.decode('utf-8', errors='ignore'))
                except json.JSONDecodeError:
                    # Try to find JSON in binary data
                    json_start = data.find(b'{')
                    if json_start >= 0:
                        try:
                            return json.loads(data[json_start:].decode('utf-8', errors='ignore'))
                        except json.JSONDecodeError:
                            pass
                    
                    # As a last resort, return raw data
                    return {
                        'type': 'binary',
                        'data': base64.b64encode(data).decode('ascii'),
                        'raw': True
                    }
                
        except Exception as e:
            logger.error(f"Failed to decode message: {e}")
            # Log hexdump of data for debugging
            hex_dump = data.hex()
            logger.debug(f"Failed to decode data (hex): {hex_dump[:100]}...")
            
            # Return a generic error message
            return {
                'type': 'error',
                'error': {
                    'code': 'decode_error',
                    'message': f"Failed to decode message: {str(e)}"
                }
            }
    
    def generate_message_id(self) -> str:
        """
        Generate a unique message ID.
        
        Returns:
            Message ID string
        """
        # Generate a unique ID based on timestamp and counter
        timestamp = int(time.time() * 1000)
        
        # Ensure timestamp is always increasing
        if timestamp <= self.last_timestamp:
            timestamp = self.last_timestamp + 1
        
        self.last_timestamp = timestamp
        
        # Combine timestamp with a random component and counter
        self.message_counter = (self.message_counter + 1) % 10000
        random_component = random.randint(1000, 9999)
        
        return f"{timestamp}.{self.message_counter}{random_component}"
        
    def _encode_varint(self, value: int) -> bytes:
        """
        Encode an integer as a variable-length integer.
        
        Args:
            value: Integer to encode
            
        Returns:
            Encoded bytes
        """
        result = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            if value:
                byte |= 0x80
            result.append(byte)
            if not value:
                break
        return bytes(result)
    
    def _decode_varint(self, data: bytes, offset: int = 0) -> Tuple[int, int]:
        """
        Decode a variable-length integer.
        
        Args:
            data: Encoded data
            offset: Starting offset in data
            
        Returns:
            Tuple of (decoded value, new offset)
        """
        result = 0
        shift = 0
        position = offset
        
        while position < len(data):
            byte = data[position]
            position += 1
            
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
                
            shift += 7
            if shift >= 64:
                raise ProtocolError("Varint is too long")
        
        return result, position