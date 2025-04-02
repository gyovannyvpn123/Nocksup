"""
Connection manager for WhatsApp.

This module handles the WebSocket connection to WhatsApp servers,
including connection establishment, reconnection, and message handling.
"""
import json
import time
import threading
import queue
from typing import Dict, Any, List, Optional, Callable, Union

import websocket

from nocksup.utils.logger import logger
from nocksup.exceptions import ConnectionError
from nocksup.protocols.constants import (
    WEBSOCKET_URL, 
    AUTH_STATES,
    WHATSAPP_WEB_VERSION
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
                                  f'Chrome/96.0.4664.110 Safari/537.36'
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
        
        self.reconnect_count += 1
        
        # Exponential backoff for reconnect delay
        delay = min(self.reconnect_delay * (2 ** (self.reconnect_count - 1)), 
                   self.max_reconnect_delay)
        
        logger.info(f"Attempting to reconnect in {delay} seconds (attempt {self.reconnect_count})")
        time.sleep(delay)
        
        try:
            # Close existing connection if any
            self._cleanup()
            
            # Attempt to connect
            return self.connect()
            
        except ConnectionError as e:
            logger.error(f"Reconnection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        Disconnect from WhatsApp servers.
        """
        logger.info("Disconnecting from WhatsApp servers")
        self._cleanup()
        self.state = AUTH_STATES['disconnected']
        logger.info("Disconnected from WhatsApp")
    
    def _cleanup(self) -> None:
        """Clean up connections and threads."""
        # Signal threads to stop
        self.stop_threads = True
        
        # Close WebSocket connection
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
        
        self.ws = None
        self.connected = False
        
        # Wait for threads to finish
        for thread in [self.send_thread, self.recv_thread, self.keepalive_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2)
        
        # Reset threads
        self.send_thread = None
        self.recv_thread = None
        self.keepalive_thread = None
    
    def _start_threads(self) -> None:
        """Start worker threads for message handling."""
        # Thread for sending queued messages
        self.send_thread = threading.Thread(
            target=self._send_thread_func,
            daemon=True
        )
        self.send_thread.start()
        
        # Thread for receiving messages
        self.recv_thread = threading.Thread(
            target=self._recv_thread_func,
            daemon=True
        )
        self.recv_thread.start()
        
        # Thread for keepalive pings
        self.keepalive_thread = threading.Thread(
            target=self._keepalive_thread_func,
            daemon=True
        )
        self.keepalive_thread.start()
    
    def _send_thread_func(self) -> None:
        """Thread function for sending queued messages."""
        while not self.stop_threads:
            try:
                # Get message from queue with timeout
                try:
                    message = self.message_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Skip if not connected
                if not self.connected or not self.ws:
                    # Put message back in queue
                    self.message_queue.put(message)
                    time.sleep(1)
                    continue
                
                # Send message
                try:
                    self.ws.send(message)
                    logger.debug(f"Sent message: {message[:100]}...")
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    # Put message back in queue
                    self.message_queue.put(message)
                    # Trigger reconnect if needed
                    if self.connected:
                        self.connected = False
                        threading.Thread(target=self.reconnect, daemon=True).start()
                
                # Mark task as done
                self.message_queue.task_done()
                
                # Small delay to avoid flooding
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in send thread: {e}")
                time.sleep(1)
    
    def _recv_thread_func(self) -> None:
        """Thread function for receiving messages."""
        while not self.stop_threads:
            try:
                # Skip if not connected
                if not self.connected or not self.ws:
                    time.sleep(1)
                    continue
                
                # Set timeout for receiving
                self.ws.settimeout(1)
                
                try:
                    # Receive message
                    data = self.ws.recv()
                    if data:
                        logger.debug(f"Received data: {data[:100]}...")
                        self._handle_message(data)
                except websocket.WebSocketTimeoutException:
                    # Timeout is normal, continue
                    pass
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    # Trigger reconnect if needed
                    if self.connected:
                        self.connected = False
                        threading.Thread(target=self.reconnect, daemon=True).start()
                
            except Exception as e:
                logger.error(f"Error in receive thread: {e}")
                time.sleep(1)
    
    def _keepalive_thread_func(self) -> None:
        """Thread function for sending keepalive pings."""
        ping_interval = 30  # seconds
        
        while not self.stop_threads:
            try:
                # Skip if not connected
                if not self.connected or not self.ws:
                    time.sleep(1)
                    continue
                
                # Send ping
                self._send_ping()
                
                # Wait for next ping
                time.sleep(ping_interval)
                
            except Exception as e:
                logger.error(f"Error in keepalive thread: {e}")
                time.sleep(1)
    
    def _send_init_message(self) -> None:
        """
        Send initialization message to WhatsApp servers.
        
        This message contains the credentials and client info.
        """
        # Create initialization message
        init_message = {
            "clientId": self.credentials.get("client_id"),
            "browserToken": self.credentials.get("browser_token"),
            "serverToken": self.credentials.get("server_token"),
            "clientVersion": WHATSAPP_WEB_VERSION,
            "platform": "CHROMIUM_WEB"
        }
        
        # Send as JSON
        self.ws.send(json.dumps(init_message))
        
        # Update state
        self.state = AUTH_STATES['authenticating']
    
    def _send_ping(self) -> None:
        """Send a ping message to keep the connection alive."""
        if self.connected and self.ws:
            try:
                # Simple ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": int(time.time() * 1000)
                }
                
                # Send as JSON
                self.ws.send(json.dumps(ping_message))
                logger.debug("Sent ping message")
                
            except Exception as e:
                logger.error(f"Failed to send ping: {e}")
    
    def _handle_message(self, data: str) -> None:
        """
        Handle incoming message from WebSocket.
        
        Args:
            data: Raw message data
        """
        try:
            # Parse the message
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "message":
                # Regular message
                self._handle_chat_message(message)
            elif message.get("type") == "receipt":
                # Message receipt (delivered/read)
                self._handle_receipt(message)
            elif message.get("type") == "presence":
                # Presence update
                self._handle_presence(message)
            elif message.get("type") == "pong":
                # Response to ping
                logger.debug("Received pong")
            else:
                # Other message types
                logger.debug(f"Unhandled message type: {message.get('type')}")
            
            # Call message callback if provided
            if self.on_message_callback:
                self.on_message_callback(message)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _handle_chat_message(self, message: Dict[str, Any]) -> None:
        """
        Handle chat message.
        
        Args:
            message: Chat message
        """
        logger.info(f"Received message from {message.get('from')}: {message.get('body', '')[:50]}...")
        
        # Check if there's a specific handler for this message type
        message_type = message.get("subtype", "text")
        handler = self.message_handlers.get(message_type)
        
        if handler:
            handler(message)
    
    def _handle_receipt(self, receipt: Dict[str, Any]) -> None:
        """
        Handle message receipt.
        
        Args:
            receipt: Receipt message
        """
        logger.debug(f"Received receipt: {receipt.get('type')} for {receipt.get('id')}")
    
    def _handle_presence(self, presence: Dict[str, Any]) -> None:
        """
        Handle presence update.
        
        Args:
            presence: Presence message
        """
        logger.debug(f"Received presence update: {presence.get('from')} is {presence.get('status')}")
    
    def send_message(self, message: Union[Dict[str, Any], bytes, str]) -> bool:
        """
        Queue a message for sending.
        
        Args:
            message: Message to send (dict, bytes, or string)
            
        Returns:
            True if message was queued
        """
        try:
            # Convert dict to JSON string if needed
            if isinstance(message, dict):
                message = json.dumps(message)
            
            # Add to send queue
            self.message_queue.put(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
            return False
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def is_connected(self) -> bool:
        """Check if connected to WhatsApp servers."""
        return self.connected and self.ws is not None
