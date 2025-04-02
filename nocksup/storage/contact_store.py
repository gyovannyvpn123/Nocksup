"""
Contact storage for WhatsApp contacts.

This module provides functionality for storing and retrieving
WhatsApp contact information.
"""
import os
import json
import time
from typing import Dict, Any, Optional, List

from nocksup.utils.logger import logger
from nocksup.exceptions import StorageError

class ContactStore:
    """
    Store and retrieve WhatsApp contact data.
    
    This class provides functionality for persistently storing WhatsApp contact
    information to avoid repeated network requests.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize contact store.
        
        Args:
            storage_dir: Directory for storing contact data
        """
        self.storage_dir = storage_dir or os.path.expanduser('~/.nocksup/contacts')
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # In-memory cache
        self.contacts_cache = {}
        
        # Contact database file
        self.contacts_file = os.path.join(self.storage_dir, 'contacts.json')
        
        # Load contacts from file
        self._load_contacts()
        
        logger.debug(f"Contact store initialized with directory: {self.storage_dir}")
    
    def add_contact(self, contact: Dict[str, Any]) -> bool:
        """
        Add or update a contact.
        
        Args:
            contact: Contact data to save
            
        Returns:
            True if successful
            
        Raises:
            StorageError: If saving fails
        """
        try:
            # Ensure required fields
            if 'phone' not in contact and 'jid' not in contact:
                raise ValueError("Contact must have either 'phone' or 'jid'")
            
            # Extract phone from JID if not provided
            if 'jid' in contact and 'phone' not in contact:
                jid_parts = contact['jid'].split('@')
                if len(jid_parts) > 0:
                    contact['phone'] = jid_parts[0]
            
            # Use phone as key
            key = contact['phone']
            
            # Update timestamp
            contact['last_updated'] = int(time.time())
            
            # Add to cache
            self.contacts_cache[key] = contact
            
            # Save to file
            self._save_contacts()
            
            logger.debug(f"Contact saved: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save contact: {e}")
            raise StorageError(f"Failed to save contact: {str(e)}")
    
    def get_contact(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get contact by phone number.
        
        Args:
            phone: Contact phone number
            
        Returns:
            Contact data or None if not found
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            # Ensure phone is string
            phone = str(phone)
            
            # Check cache
            contact = self.contacts_cache.get(phone)
            
            if contact:
                logger.debug(f"Contact found in cache: {phone}")
                return contact.copy()  # Return a copy to prevent modifications
            else:
                logger.debug(f"Contact not found: {phone}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get contact: {e}")
            raise StorageError(f"Failed to get contact: {str(e)}")
    
    def get_contact_by_jid(self, jid: str) -> Optional[Dict[str, Any]]:
        """
        Get contact by JID.
        
        Args:
            jid: Contact JID
            
        Returns:
            Contact data or None if not found
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            # Extract phone from JID
            jid_parts = jid.split('@')
            if len(jid_parts) > 0:
                phone = jid_parts[0]
                return self.get_contact(phone)
            
            # If phone extraction fails, search in cache
            for contact in self.contacts_cache.values():
                if contact.get('jid') == jid:
                    logger.debug(f"Contact found by JID: {jid}")
                    return contact.copy()  # Return a copy to prevent modifications
            
            logger.debug(f"Contact not found by JID: {jid}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get contact by JID: {e}")
            raise StorageError(f"Failed to get contact by JID: {str(e)}")
    
    def delete_contact(self, phone: str) -> bool:
        """
        Delete a contact.
        
        Args:
            phone: Contact phone number
            
        Returns:
            True if successful, False if not found
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            # Ensure phone is string
            phone = str(phone)
            
            # Check if contact exists
            if phone not in self.contacts_cache:
                logger.debug(f"Contact not found for deletion: {phone}")
                return False
            
            # Remove from cache
            del self.contacts_cache[phone]
            
            # Save to file
            self._save_contacts()
            
            logger.debug(f"Contact deleted: {phone}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete contact: {e}")
            raise StorageError(f"Failed to delete contact: {str(e)}")
    
    def get_all_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts.
        
        Returns:
            List of contact data dictionaries
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            # Return copies of all contacts
            return [contact.copy() for contact in self.contacts_cache.values()]
            
        except Exception as e:
            logger.error(f"Failed to get all contacts: {e}")
            raise StorageError(f"Failed to get all contacts: {str(e)}")
    
    def clear_contacts(self) -> bool:
        """
        Clear all contacts.
        
        Returns:
            True if successful
            
        Raises:
            StorageError: If clearing fails
        """
        try:
            # Clear cache
            self.contacts_cache.clear()
            
            # Save to file
            self._save_contacts()
            
            logger.debug("All contacts cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear contacts: {e}")
            raise StorageError(f"Failed to clear contacts: {str(e)}")
    
    def _load_contacts(self) -> None:
        """
        Load contacts from file.
        
        Raises:
            StorageError: If loading fails
        """
        try:
            # Check if file exists
            if not os.path.isfile(self.contacts_file):
                logger.debug("Contacts file not found, starting with empty cache")
                self.contacts_cache = {}
                return
            
            # Load from file
            with open(self.contacts_file, 'r') as f:
                contacts_data = json.load(f)
            
            # Set cache
            self.contacts_cache = contacts_data
            
            logger.debug(f"Loaded {len(self.contacts_cache)} contacts from file")
            
        except Exception as e:
            logger.error(f"Failed to load contacts: {e}")
            # Start with empty cache if loading fails
            self.contacts_cache = {}
    
    def _save_contacts(self) -> None:
        """
        Save contacts to file.
        
        Raises:
            StorageError: If saving fails
        """
        try:
            # Save to file
            with open(self.contacts_file, 'w') as f:
                json.dump(self.contacts_cache, f, indent=2)
            
            logger.debug(f"Saved {len(self.contacts_cache)} contacts to file")
            
        except Exception as e:
            logger.error(f"Failed to save contacts: {e}")
            raise StorageError(f"Failed to save contacts to file: {str(e)}")
