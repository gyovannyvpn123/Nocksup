"""
Contact management for WhatsApp.

This module provides functionality for managing WhatsApp contacts,
including retrieving contact information and checking phone numbers.
"""
from typing import Dict, Any, List, Optional, Union

from nocksup.utils.logger import logger
from nocksup.utils import validate_phone_number, phone_to_jid
from nocksup.exceptions import ContactError, ValidationError
from nocksup.protocols.constants import WHATSAPP_DOMAIN
from nocksup.storage.contact_store import ContactStore

class ContactManager:
    """
    Manages WhatsApp contacts.
    
    This class provides functionality for retrieving contact information
    and checking phone numbers on WhatsApp.
    """
    
    def __init__(self, connection_manager, contact_store: ContactStore = None):
        """
        Initialize contact manager.
        
        Args:
            connection_manager: Connection manager for sending/receiving messages
            contact_store: Storage for contact information
        """
        self.connection = connection_manager
        self.contact_store = contact_store or ContactStore()
    
    def get_contact(self, phone_number: str) -> Dict[str, Any]:
        """
        Get contact information.
        
        Args:
            phone_number: Contact phone number
            
        Returns:
            Contact information
            
        Raises:
            ContactError: If operation fails
            ValidationError: If phone number is invalid
        """
        try:
            # Validate phone number
            phone = validate_phone_number(phone_number)
            
            # Check if we have contact in local storage
            contact = self.contact_store.get_contact(phone)
            if contact:
                logger.debug(f"Contact found in local storage: {phone}")
                return contact
            
            # If not in local storage, request from server
            jid = phone_to_jid(phone, WHATSAPP_DOMAIN)
            
            # Create contact info request
            info_msg = {
                "type": "contact",
                "action": "info",
                "jid": jid
            }
            
            # Send request
            encoded = self.connection.protocol.encode_message(info_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            # from the server with the contact information
            
            # For this demo, we'll simulate a response
            # This would normally come from the server
            contact_info = {
                "jid": jid,
                "phone": phone,
                "name": "Unknown",
                "status": "Hey there! I am using WhatsApp.",
                "is_whatsapp_user": True
            }
            
            # Store in local storage
            self.contact_store.add_contact(contact_info)
            
            return contact_info
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to get contact: {e}")
            raise ContactError(f"Failed to get contact: {str(e)}")
    
    def get_contacts(self) -> List[Dict[str, Any]]:
        """
        Get all contacts.
        
        Returns:
            List of contact information
            
        Raises:
            ContactError: If operation fails
        """
        try:
            # Check if we have contacts in local storage
            contacts = self.contact_store.get_all_contacts()
            if contacts:
                logger.debug(f"Found {len(contacts)} contacts in local storage")
                return contacts
            
            # If not in local storage, request from server
            contacts_msg = {
                "type": "contact",
                "action": "list"
            }
            
            # Send request
            encoded = self.connection.protocol.encode_message(contacts_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            # from the server with the contact list
            
            # For this demo, we'll simulate a response
            # This would normally come from the server
            contacts = [
                {
                    "jid": "1234567890@s.whatsapp.net",
                    "phone": "1234567890",
                    "name": "Contact 1",
                    "status": "Hey there! I am using WhatsApp.",
                    "is_whatsapp_user": True
                },
                {
                    "jid": "0987654321@s.whatsapp.net",
                    "phone": "0987654321",
                    "name": "Contact 2",
                    "status": "Available",
                    "is_whatsapp_user": True
                }
            ]
            
            # Store in local storage
            for contact in contacts:
                self.contact_store.add_contact(contact)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            raise ContactError(f"Failed to get contacts: {str(e)}")
    
    def check_phone_exists(self, phone_number: str) -> bool:
        """
        Check if a phone number exists on WhatsApp.
        
        Args:
            phone_number: Phone number to check
            
        Returns:
            True if the number exists on WhatsApp
            
        Raises:
            ContactError: If operation fails
            ValidationError: If phone number is invalid
        """
        try:
            # Validate phone number
            phone = validate_phone_number(phone_number)
            
            # Create exists request
            exists_msg = {
                "type": "contact",
                "action": "exists",
                "phone": phone
            }
            
            # Send request
            encoded = self.connection.protocol.encode_message(exists_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            # from the server with the existence information
            
            # For this demo, we'll simulate a response
            # This would normally come from the server
            exists = True
            
            # If exists, add minimal contact info to local storage
            if exists:
                jid = phone_to_jid(phone, WHATSAPP_DOMAIN)
                self.contact_store.add_contact({
                    "jid": jid,
                    "phone": phone,
                    "is_whatsapp_user": True
                })
            
            return exists
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to check phone existence: {e}")
            raise ContactError(f"Failed to check phone existence: {str(e)}")
    
    def sync_contacts(self, phone_numbers: List[str]) -> List[Dict[str, Any]]:
        """
        Sync multiple contacts with WhatsApp.
        
        Args:
            phone_numbers: List of phone numbers to sync
            
        Returns:
            List of contact information for WhatsApp users
            
        Raises:
            ContactError: If operation fails
        """
        try:
            # Validate and format phone numbers
            formatted_numbers = []
            for phone in phone_numbers:
                try:
                    formatted_numbers.append(validate_phone_number(phone))
                except ValidationError as e:
                    logger.warning(f"Invalid phone number {phone}: {e}")
                    # Skip invalid numbers
            
            if not formatted_numbers:
                raise ValidationError("No valid phone numbers provided")
            
            # Create sync request
            sync_msg = {
                "type": "contact",
                "action": "sync",
                "phones": formatted_numbers
            }
            
            # Send request
            encoded = self.connection.protocol.encode_message(sync_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            # from the server with the synced contacts
            
            # For this demo, we'll simulate a response
            # This would normally come from the server
            whatsapp_contacts = []
            for phone in formatted_numbers:
                # Simulate that some contacts are on WhatsApp
                if len(phone) % 2 == 0:  # Just a simple way to simulate some exist, some don't
                    jid = phone_to_jid(phone, WHATSAPP_DOMAIN)
                    contact = {
                        "jid": jid,
                        "phone": phone,
                        "name": f"Contact {phone[-4:]}",
                        "status": "Hey there! I am using WhatsApp.",
                        "is_whatsapp_user": True
                    }
                    whatsapp_contacts.append(contact)
                    
                    # Store in local storage
                    self.contact_store.add_contact(contact)
            
            return whatsapp_contacts
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to sync contacts: {e}")
            raise ContactError(f"Failed to sync contacts: {str(e)}")
    
    def update_contact_name(self, phone_number: str, name: str) -> bool:
        """
        Update contact name locally.
        
        Args:
            phone_number: Contact phone number
            name: New contact name
            
        Returns:
            True if successful
            
        Raises:
            ContactError: If operation fails
            ValidationError: If phone number is invalid
        """
        try:
            # Validate phone number
            phone = validate_phone_number(phone_number)
            
            # Get current contact info
            contact = self.contact_store.get_contact(phone)
            
            if not contact:
                # Get from server if not in local storage
                contact = self.get_contact(phone)
            
            # Update name
            contact['name'] = name
            
            # Store updated contact
            self.contact_store.add_contact(contact)
            
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to update contact name: {e}")
            raise ContactError(f"Failed to update contact name: {str(e)}")
