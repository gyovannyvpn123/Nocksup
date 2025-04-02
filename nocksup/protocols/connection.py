"""
Connection manager for WhatsApp.

This module handles the WebSocket connection to WhatsApp servers,
including connection establishment, reconnection, and message handling.
"""
import json
import time
import threading
import queue
import struct
from typing import Dict, Any, List, Optional, Callable, Union

import websocket

from nocksup.utils.logger import logger
from nocksup.exceptions import ConnectionError, ProtocolError
from nocksup.protocols.constants import (
    WEBSOCKET_URL, 
    AUTH_STATES,
    WHATSAPP_WEB_VERSION,
    WS_OPCODES,
    WA_FRAME_PREFIX,
    WA_METADATA_SIZE,
    WA_VERSION_SIZE
)
from nocksup.protocols.message_protocol import MessageProtocol

class ConnectionManager:
    """
    Manages the WebSocket connection to WhatsApp servers.
    
    Handles connection establishment, reconnection logic, message
    sending/receiving, and connection state management.
    """
    
    def __init__(self, credentials: Dict[str, Any] = None, on_message: Callable = None,
                on_error: Callable = None, on_close: Callable = None):
        """
        Initialize connection manager.
        
        Args:
            credentials: Authentication credentials
            on_message: Callback for received messages
            on_error: Callback for errors
            on_close: Callback for connection closure
        """
        self.credentials = credentials
        self.ws = None
        self.connected = False
        self.reconnect_count = 0
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_delay = 60  # seconds
        self.max_reconnect_attempts = 10
        self.state = AUTH_STATES['disconnected']
        self.protocol = MessageProtocol()
        self.message_queue = queue.Queue()
        self.send_thread = None
        self.recv_thread = None
        self.keepalive_thread = None
        self.stop_threads = False
        
        # Callbacks
        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.on_close_callback = on_close
        
        # Message handlers
        self.message_handlers = {}
    
    def connect(self) -> bool:
        """
        Connect to WhatsApp servers.
        
        Returns:
            True if connected successfully
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info("Connecting to WhatsApp servers...")
            self.state = AUTH_STATES['connecting']
            
            # Create WebSocket connection
            self.ws = websocket.create_connection(
                WEBSOCKET_URL,
                header={
                    'Origin': 'https://web.whatsapp.com',
                    'User-Agent': f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                                  f'AppleWebKit/537.36 (KHTML, like Gecko) '
                                  f'Chrome/108.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits'
                }
            )
            
            # Initialize connection with credentials if available
            if self.credentials:
                self._send_init_message()
                
            # Start worker threads
            self.stop_threads = False
            self._start_threads()
            
            self.connected = True
            self.reconnect_count = 0
            self.state = AUTH_STATES['connected']
            logger.info("Connected to WhatsApp servers")
            
            return True
            
        except (websocket.WebSocketException, OSError) as e:
            logger.error(f"Connection error: {e}")
            self.state = AUTH_STATES['failed']
            raise ConnectionError(f"Failed to connect to WhatsApp: {str(e)}")
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to WhatsApp servers.
        
        Returns:
            True if reconnected successfully
        """
        if self.reconnect_count >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return False
        
        logger.info(f"Attempting to reconnect (attempt {self.reconnect_count + 1}/{self.max_reconnect_attempts})...")
        
        # Stop all threads
        self.stop_threads = True
        self._stop_threads()
        
        # Calculate reconnect delay with exponential backoff
        delay = min(self.reconnect_delay * (2 ** self.reconnect_count), self.max_reconnect_delay)
        time.sleep(delay)
        
        # Increment reconnect counter
        self.reconnect_count += 1
        
        try:
            return self.connect()
        except ConnectionError:
            logger.warning("Reconnection attempt failed")
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from WhatsApp servers.
        """
        logger.info("Disconnecting from WhatsApp servers...")
        
        # Stop all threads
        self.stop_threads = True
        self._stop_threads()
        
        # Close WebSocket
        if self.ws:
            try:
                self.ws.close()
            except websocket.WebSocketException:
                pass
            finally:
                self.ws = None
        
        self.connected = False
        self.state = AUTH_STATES['disconnected']
        logger.info("Disconnected from WhatsApp servers")
    
    def send_message(self, message: Dict[str, Any]) -> str:
        """
        Send a message to WhatsApp servers.
        
        Args:
            message: Message to send
            
        Returns:
            Message ID
            
        Raises:
            ConnectionError: If not connected
            ProtocolError: If message sending fails
        """
        if not self.connected or not self.ws:
            raise ConnectionError("Not connected to WhatsApp servers")
        
        # Add message to queue
        message_id = self.protocol.generate_message_id()
        message['id'] = message_id
        self.message_queue.put(message)
        
        return message_id
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        self.message_handlers[message_type] = handler
    
    def _start_threads(self) -> None:
        """
        Start worker threads for message sending and receiving.
        """
        # Create threads
        self.send_thread = threading.Thread(target=self._send_worker)
        self.recv_thread = threading.Thread(target=self._recv_worker)
        self.keepalive_thread = threading.Thread(target=self._keepalive_worker)
        
        # Set as daemon threads so they exit when main thread exits
        self.send_thread.daemon = True
        self.recv_thread.daemon = True
        self.keepalive_thread.daemon = True
        
        # Start threads
        self.send_thread.start()
        self.recv_thread.start()
        self.keepalive_thread.start()
    
    def _stop_threads(self) -> None:
        """
        Stop worker threads.
        """
        # Wait for threads to exit
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=1.0)
        
        if self.recv_thread and self.recv_thread.is_alive():
            self.recv_thread.join(timeout=1.0)
        
        if self.keepalive_thread and self.keepalive_thread.is_alive():
            self.keepalive_thread.join(timeout=1.0)
        
        # Reset threads
        self.send_thread = None
        self.recv_thread = None
        self.keepalive_thread = None
    
    def _send_worker(self) -> None:
        """
        Worker thread for sending messages.
        """
        while not self.stop_threads and self.connected:
            try:
                # Get message from queue with timeout to allow checking stop flag
                try:
                    message = self.message_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Encode and send message
                try:
                    encoded = self.protocol.encode_message(message)
                    self._send_raw(encoded)
                    logger.debug(f"Sent message: {message['id']}")
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                finally:
                    self.message_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error in send worker: {e}")
                time.sleep(0.5)  # Prevent tight loop on error
    
    def _recv_worker(self) -> None:
        """
        Worker thread for receiving messages.
        """
        while not self.stop_threads and self.connected:
            try:
                # Receive message
                data = self._recv_raw()
                if not data:
                    continue
                
                # Decode message using the new WAW protocol format
                try:
                    message = self._decode_message(data)
                    
                    # Handle message
                    if message:
                        self._handle_message(message)
                except Exception as e:
                    logger.error(f"Error decoding/handling message: {e}")
                    
            except Exception as e:
                logger.error(f"Error in receive worker: {e}")
                
                # Check if connection is closed
                if isinstance(e, (websocket.WebSocketConnectionClosedException, ConnectionError)):
                    logger.warning("Connection closed")
                    if not self.stop_threads:
                        self.reconnect()
                    break
                
                time.sleep(0.5)  # Prevent tight loop on error
    
    def _keepalive_worker(self) -> None:
        """
        Worker thread for keeping the connection alive.
        """
        while not self.stop_threads and self.connected:
            try:
                # Send ping every 30 seconds
                time.sleep(30)
                if self.connected and self.ws:
                    # Send a ping frame directly via websocket
                    self.ws.ping("keepalive")
                    logger.debug("Sent keepalive ping")
            except Exception as e:
                logger.error(f"Error in keepalive worker: {e}")
                time.sleep(5)  # Prevent tight loop on error
    
    def _decode_message(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Decode message from raw bytes using the new WhatsApp Web protocol.
        
        Args:
            data: Raw message data
            
        Returns:
            Decoded message or None if decoding fails
        """
        try:
            # Check for WAW prefix (WhatsApp Web message format)
            if data.startswith(WA_FRAME_PREFIX):
                # Parse WAW format: WAW + metadata (4 bytes) + version (3 bytes) + payload
                prefix_size = len(WA_FRAME_PREFIX)
                
                # Extract metadata and version info
                # The WAW format starts with:
                # - 'WAW' (3 bytes)
                # - Metadata (4 bytes)
                # - Protocol version (3 bytes)
                # - Payload (remaining bytes)
                
                # Skip the prefix and parse metadata
                metadata = struct.unpack('>I', data[prefix_size:prefix_size + WA_METADATA_SIZE])[0]
                
                # Skip metadata and extract versioning info (not used currently)
                version_offset = prefix_size + WA_METADATA_SIZE
                version_bytes = data[version_offset:version_offset + WA_VERSION_SIZE]
                
                # Get the payload (the actual message content)
                payload_offset = version_offset + WA_VERSION_SIZE
                payload = data[payload_offset:]
                
                # Let the MessageProtocol decode the payload
                return self.protocol.decode_message(payload)
            else:
                # Legacy format or other format
                return self.protocol.decode_message(data)
                
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            # Dump hex representation of message for debugging
            logger.debug(f"Raw message (hex): {data.hex()}")
            return None
    
    def _send_raw(self, data: bytes) -> None:
        """
        Send raw data over WebSocket.
        
        Args:
            data: Data to send
            
        Raises:
            ConnectionError: If sending fails
        """
        if not self.ws:
            raise ConnectionError("WebSocket not connected")
        
        try:
            # Format data to include WAW prefix, metadata, and version
            if not data.startswith(WA_FRAME_PREFIX):
                metadata = len(data)  # Simple metadata - just the payload length
                version = WHATSAPP_WEB_VERSION.split('.')
                version_int = (int(version[0]) << 16) | (int(version[1]) << 8) | int(version[2])
                version_bytes = struct.pack('>I', version_int)[-3:]  # Take only last 3 bytes
                
                # Create the full frame with WAW prefix
                frame = WA_FRAME_PREFIX + struct.pack('>I', metadata) + version_bytes + data
                data = frame
            
            # Send binary frame
            self.ws.send_binary(data)
        except websocket.WebSocketException as e:
            logger.error(f"WebSocket send error: {e}")
            raise ConnectionError(f"Failed to send data: {str(e)}")
    
    def _recv_raw(self) -> Optional[bytes]:
        """
        Receive raw data from WebSocket.
        
        Returns:
            Received data or None if no data
            
        Raises:
            ConnectionError: If connection is closed
        """
        if not self.ws:
            raise ConnectionError("WebSocket not connected")
        
        try:
            # Set a timeout to allow checking stop flag
            self.ws.settimeout(0.5)
            
            # Receive binary (opcode 2) or text (opcode 1) frame
            opcode, data = self.ws.recv_data()
            
            if opcode == WS_OPCODES['BINARY']:
                # Binary data
                return data
            elif opcode == WS_OPCODES['TEXT']:
                # Text data - decode as JSON
                try:
                    # Tratăm datele text (probabil JSON) ca atare
                    return data
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON text data")
                    return data
            elif opcode == WS_OPCODES['PING']:
                # Respond to ping with pong
                self.ws.pong(data)
                logger.debug("Received ping, sent pong")
                return None
            elif opcode == WS_OPCODES['CLOSE']:
                # Connection closed
                logger.warning("Received close frame")
                raise ConnectionError("Connection closed by server")
            else:
                logger.warning(f"Received unknown opcode: {opcode}")
                return None
                
        except websocket.WebSocketTimeoutException:
            # Timeout - no data received
            return None
        except websocket.WebSocketConnectionClosedException:
            logger.warning("WebSocket connection closed")
            raise ConnectionError("Connection closed")
        except websocket.WebSocketException as e:
            logger.error(f"WebSocket receive error: {e}")
            raise ConnectionError(f"Failed to receive data: {str(e)}")
    
    def _send_init_message(self) -> None:
        """
        Send initialization message with credentials.
        
        Raises:
            ConnectionError: If sending fails
        """
        if not self.credentials:
            logger.warning("No credentials available for initialization")
            return
        
        try:
            # Create initialization message
            init_message = {
                'type': 'init',
                'version': WHATSAPP_WEB_VERSION,
                'browser_details': {
                    'browser': 'Chrome',
                    'browser_version': '108.0.0.0',
                    'os': 'Mac OS X',
                    'platform': 'desktop'
                },
                'credentials': self.credentials
            }
            
            # Send as JSON string
            json_data = json.dumps(init_message)
            self.ws.send(json_data)
            logger.debug("Sent initialization message")
            
        except Exception as e:
            logger.error(f"Failed to send initialization message: {e}")
            raise ConnectionError(f"Failed to initialize connection: {str(e)}")
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a received message.
        
        Args:
            message: Decoded message
        """
        # Get message type
        message_type = message.get('type')
        
        # Call registered handler for this message type
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type](message)
            except Exception as e:
                logger.error(f"Error in message handler for {message_type}: {e}")
        
        # Call general message callback
        if self.on_message_callback:
            try:
                self.on_message_callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
                
        # Default handling for some message types
        if message_type == 'error':
            logger.error(f"Received error message: {message.get('error', {}).get('message', 'Unknown error')}")
            if self.on_error_callback:
                try:
                    self.on_error_callback(message)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
        elif message_type == 'stream:error':
            logger.error(f"Received stream error: {message.get('error')}")
            if self.on_error_callback:
                try:
                    self.on_error_callback(message)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
        elif message_type == 'connection:error':
            logger.error(f"Received connection error: {message.get('error')}")
            if self.on_error_callback:
                try:
                    self.on_error_callback(message)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
        elif message_type == 'connection:close':
            logger.warning("Received connection close message")
            if self.on_close_callback:
                try:
                    self.on_close_callback(message)
                except Exception as e:
                    logger.error(f"Error in close callback: {e}")
        elif message_type == 'challenge':
            # Authentication challenge
            logger.info("Received authentication challenge")
            # Handle challenge in authenticator
        elif message_type == 'success':
            # Authentication success
            logger.info("Authentication successful")
            # Update state
            self.state = AUTH_STATES['connected']
        elif message_type == 'failure':
            # Authentication failure
            logger.error(f"Authentication failed: {message.get('reason', 'Unknown reason')}")
            # Update state
            self.state = AUTH_STATES['failed']
            if self.on_error_callback:
                try:
                    self.on_error_callback(message)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")