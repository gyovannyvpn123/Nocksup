"""
Session storage for WhatsApp authentication.

This module provides functionality for storing and retrieving
WhatsApp session data for persistent authentication.
"""
import os
import json
import time
from typing import Dict, Any, Optional, List

from nocksup.utils.logger import logger
from nocksup.exceptions import StorageError

class SessionStore:
    """
    Store and retrieve WhatsApp session data.
    
    This class provides functionality for persisting WhatsApp authentication
    sessions to enable reconnection without re-authentication.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize session store.
        
        Args:
            storage_dir: Directory for storing session data
        """
        self.storage_dir = storage_dir or os.path.expanduser('~/.nocksup/sessions')
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.debug(f"Session store initialized with directory: {self.storage_dir}")
    
    def save_session(self, phone_number: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data.
        
        Args:
            phone_number: User's phone number
            session_data: Session data to save
            
        Returns:
            True if successful
            
        Raises:
            StorageError: If saving fails
        """
        try:
            # Create session filename
            filename = self._get_session_filename(phone_number)
            
            # Add timestamp
            session_data['timestamp'] = int(time.time())
            
            # Save session data
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.debug(f"Session saved for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            raise StorageError(f"Failed to save session: {str(e)}")
    
    def load_session(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Load session data.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Session data or None if not found
            
        Raises:
            StorageError: If loading fails
        """
        try:
            # Create session filename
            filename = self._get_session_filename(phone_number)
            
            # Check if file exists
            if not os.path.isfile(filename):
                logger.debug(f"No session found for {phone_number}")
                return None
            
            # Load session data
            with open(filename, 'r') as f:
                session_data = json.load(f)
            
            logger.debug(f"Session loaded for {phone_number}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            raise StorageError(f"Failed to load session: {str(e)}")
    
    def delete_session(self, phone_number: str) -> bool:
        """
        Delete session data.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            True if successful, False if no session found
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            # Create session filename
            filename = self._get_session_filename(phone_number)
            
            # Check if file exists
            if not os.path.isfile(filename):
                logger.debug(f"No session found for {phone_number}")
                return False
            
            # Delete file
            os.remove(filename)
            
            logger.debug(f"Session deleted for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            raise StorageError(f"Failed to delete session: {str(e)}")
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all saved sessions.
        
        Returns:
            List of session data dictionaries
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            sessions = []
            
            # Check if directory exists
            if not os.path.isdir(self.storage_dir):
                return sessions
            
            # List session files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.session'):
                    # Extract phone number from filename
                    phone_number = filename[:-8]  # Remove .session
                    
                    # Load session
                    session = self.load_session(phone_number)
                    if session:
                        # Add phone number to session data
                        session['phone_number'] = phone_number
                        sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get all sessions: {e}")
            raise StorageError(f"Failed to get all sessions: {str(e)}")
    
    def _get_session_filename(self, phone_number: str) -> str:
        """
        Get filename for a session.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Session filename
        """
        # Sanitize phone number for filename
        phone = ''.join(c for c in phone_number if c.isdigit())
        
        # Create filename
        return os.path.join(self.storage_dir, f"{phone}.session")
