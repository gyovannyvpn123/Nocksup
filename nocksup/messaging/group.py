"""
Group chat functionality for WhatsApp.

This module provides classes and functions for managing WhatsApp groups,
including creation, adding/removing participants, and group information.
"""
import time
from typing import Dict, Any, List, Optional, Union

from nocksup.utils.logger import logger
from nocksup.utils import validate_phone_number, phone_to_jid, is_group_jid
from nocksup.exceptions import GroupError, ValidationError
from nocksup.protocols.constants import (
    GROUP_PARTICIPANT_TYPES,
    WHATSAPP_GROUP_DOMAIN
)

class GroupManager:
    """
    Manages WhatsApp group operations.
    
    This class provides functionality for creating and managing WhatsApp
    groups, including adding/removing participants and changing group settings.
    """
    
    def __init__(self, connection_manager):
        """
        Initialize the group manager.
        
        Args:
            connection_manager: Connection manager for sending/receiving messages
        """
        self.connection = connection_manager
    
    def create_group(self, subject: str, participants: List[str]) -> Dict[str, Any]:
        """
        Create a new WhatsApp group.
        
        Args:
            subject: Group name
            participants: List of participant phone numbers
            
        Returns:
            Group information including group ID
            
        Raises:
            GroupError: If group creation fails
            ValidationError: If parameters are invalid
        """
        if not subject or not subject.strip():
            raise ValidationError("Group subject cannot be empty")
        
        if not participants or len(participants) < 1:
            raise ValidationError("Group must have at least one participant")
        
        try:
            # Validate and format participants
            formatted_participants = []
            for participant in participants:
                try:
                    if '@' not in participant:
                        # Convert phone number to JID
                        phone = validate_phone_number(participant)
                        jid = phone_to_jid(phone)
                    else:
                        jid = participant
                    
                    formatted_participants.append(jid)
                except ValueError as e:
                    logger.warning(f"Invalid participant {participant}: {e}")
                    # Skip invalid participants
            
            if not formatted_participants:
                raise ValidationError("No valid participants provided")
            
            # Create group creation message
            create_msg = {
                "type": "group",
                "action": "create",
                "subject": subject,
                "participants": formatted_participants
            }
            
            # Send group creation request
            encoded = self.connection.protocol.encode_message(create_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            # from the server with the group information
            
            # For this demo, we'll simulate a successful response
            group_id = f"{int(time.time() * 1000)}@{WHATSAPP_GROUP_DOMAIN}"
            
            # Return group info
            return {
                "group_id": group_id,
                "subject": subject,
                "creation_time": int(time.time()),
                "creator": "me",
                "participants": formatted_participants
            }
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            raise GroupError(f"Failed to create group: {str(e)}")
    
    def add_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Add participants to a group.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to add
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        if not participants:
            raise ValidationError("No participants provided")
        
        try:
            # Validate and format participants
            formatted_participants = []
            for participant in participants:
                try:
                    if '@' not in participant:
                        # Convert phone number to JID
                        phone = validate_phone_number(participant)
                        jid = phone_to_jid(phone)
                    else:
                        jid = participant
                    
                    formatted_participants.append(jid)
                except ValueError as e:
                    logger.warning(f"Invalid participant {participant}: {e}")
                    # Skip invalid participants
            
            if not formatted_participants:
                raise ValidationError("No valid participants provided")
            
            # Create add participants message
            add_msg = {
                "type": "group",
                "action": "add",
                "group": group_id,
                "participants": formatted_participants
            }
            
            # Send add participants request
            encoded = self.connection.protocol.encode_message(add_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to add participants: {e}")
            raise GroupError(f"Failed to add participants: {str(e)}")
    
    def remove_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Remove participants from a group.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to remove
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        if not participants:
            raise ValidationError("No participants provided")
        
        try:
            # Validate and format participants
            formatted_participants = []
            for participant in participants:
                try:
                    if '@' not in participant:
                        # Convert phone number to JID
                        phone = validate_phone_number(participant)
                        jid = phone_to_jid(phone)
                    else:
                        jid = participant
                    
                    formatted_participants.append(jid)
                except ValueError as e:
                    logger.warning(f"Invalid participant {participant}: {e}")
                    # Skip invalid participants
            
            if not formatted_participants:
                raise ValidationError("No valid participants provided")
            
            # Create remove participants message
            remove_msg = {
                "type": "group",
                "action": "remove",
                "group": group_id,
                "participants": formatted_participants
            }
            
            # Send remove participants request
            encoded = self.connection.protocol.encode_message(remove_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to remove participants: {e}")
            raise GroupError(f"Failed to remove participants: {str(e)}")
    
    def leave_group(self, group_id: str) -> bool:
        """
        Leave a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        try:
            # Create leave group message
            leave_msg = {
                "type": "group",
                "action": "leave",
                "group": group_id
            }
            
            # Send leave group request
            encoded = self.connection.protocol.encode_message(leave_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to leave group: {e}")
            raise GroupError(f"Failed to leave group: {str(e)}")
    
    def update_subject(self, group_id: str, subject: str) -> bool:
        """
        Update group subject.
        
        Args:
            group_id: Group ID
            subject: New group subject
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        if not subject or not subject.strip():
            raise ValidationError("Group subject cannot be empty")
        
        try:
            # Create update subject message
            subject_msg = {
                "type": "group",
                "action": "subject",
                "group": group_id,
                "subject": subject
            }
            
            # Send update subject request
            encoded = self.connection.protocol.encode_message(subject_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update group subject: {e}")
            raise GroupError(f"Failed to update group subject: {str(e)}")
    
    def get_group_info(self, group_id: str) -> Dict[str, Any]:
        """
        Get information about a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            Group information
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        try:
            # Create get info message
            info_msg = {
                "type": "group",
                "action": "info",
                "group": group_id
            }
            
            # Send get info request
            encoded = self.connection.protocol.encode_message(info_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            # from the server with the group information
            
            # For this demo, we'll simulate a response
            # This would normally come from the server
            group_info = {
                "group_id": group_id,
                "subject": "Sample Group",
                "creation_time": int(time.time()) - 3600,  # 1 hour ago
                "participants": [
                    {
                        "jid": "1234567890@s.whatsapp.net",
                        "type": GROUP_PARTICIPANT_TYPES["admin"]
                    },
                    {
                        "jid": "0987654321@s.whatsapp.net",
                        "type": GROUP_PARTICIPANT_TYPES["member"]
                    }
                ]
            }
            
            return group_info
            
        except Exception as e:
            logger.error(f"Failed to get group info: {e}")
            raise GroupError(f"Failed to get group info: {str(e)}")
    
    def promote_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Promote participants to group admins.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to promote
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        if not participants:
            raise ValidationError("No participants provided")
        
        try:
            # Validate and format participants
            formatted_participants = []
            for participant in participants:
                try:
                    if '@' not in participant:
                        # Convert phone number to JID
                        phone = validate_phone_number(participant)
                        jid = phone_to_jid(phone)
                    else:
                        jid = participant
                    
                    formatted_participants.append(jid)
                except ValueError as e:
                    logger.warning(f"Invalid participant {participant}: {e}")
                    # Skip invalid participants
            
            if not formatted_participants:
                raise ValidationError("No valid participants provided")
            
            # Create promote participants message
            promote_msg = {
                "type": "group",
                "action": "promote",
                "group": group_id,
                "participants": formatted_participants
            }
            
            # Send promote participants request
            encoded = self.connection.protocol.encode_message(promote_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to promote participants: {e}")
            raise GroupError(f"Failed to promote participants: {str(e)}")
    
    def demote_participants(self, group_id: str, participants: List[str]) -> bool:
        """
        Demote participants from group admins.
        
        Args:
            group_id: Group ID
            participants: List of participant phone numbers to demote
            
        Returns:
            True if successful
            
        Raises:
            GroupError: If operation fails
            ValidationError: If parameters are invalid
        """
        if not is_group_jid(group_id):
            raise ValidationError(f"Invalid group ID: {group_id}")
        
        if not participants:
            raise ValidationError("No participants provided")
        
        try:
            # Validate and format participants
            formatted_participants = []
            for participant in participants:
                try:
                    if '@' not in participant:
                        # Convert phone number to JID
                        phone = validate_phone_number(participant)
                        jid = phone_to_jid(phone)
                    else:
                        jid = participant
                    
                    formatted_participants.append(jid)
                except ValueError as e:
                    logger.warning(f"Invalid participant {participant}: {e}")
                    # Skip invalid participants
            
            if not formatted_participants:
                raise ValidationError("No valid participants provided")
            
            # Create demote participants message
            demote_msg = {
                "type": "group",
                "action": "demote",
                "group": group_id,
                "participants": formatted_participants
            }
            
            # Send demote participants request
            encoded = self.connection.protocol.encode_message(demote_msg)
            self.connection.send_message(encoded)
            
            # In a real implementation, we would wait for a response
            
            return True
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to demote participants: {e}")
            raise GroupError(f"Failed to demote participants: {str(e)}")
