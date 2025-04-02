#!/usr/bin/env python3
"""
Simple WhatsApp client example using nocksup.

This example demonstrates how to use the nocksup library
to create a simple WhatsApp client for sending and receiving messages.
"""
import os
import sys
import time
import logging
from getpass import getpass

# Add parent directory to path to allow importing nocksup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nocksup import NocksupClient
from nocksup.exceptions import (
    ConnectionError, 
    AuthenticationError, 
    MessageError,
    ValidationError
)

def main():
    """Run the simple WhatsApp client example."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create client
    client = NocksupClient()
    
    try:
        # Get phone number
        phone_number = input("Enter your phone number with country code (e.g., 1234567890): ")
        client.set_phone_number(phone_number)
        
        # Connect to WhatsApp
        print("Connecting to WhatsApp...")
        
        try:
            # Try to connect with existing session
            client.connect(restore_session=True)
            print("Connected with existing session")
        except AuthenticationError:
            print("No valid session found, need to register or authenticate")
            
            auth_choices = ["r", "q", "p"]
            auth_choice = ""
            while auth_choice not in auth_choices:
                auth_choice = input(
                    "Choose authentication method:\n"
                    "(r) Register number\n"
                    "(q) QR code authentication\n"
                    "(p) Pairing code authentication\n"
                    "Enter choice (r/q/p): "
                ).lower()
            
            if auth_choice == "r":
                # Register number
                method = input("Verification method (sms/voice): ").lower() or 'sms'
                response = client.register_number(method=method)
                print(f"Verification code sent via {method}")
                
                # Verify code
                code = input("Enter verification code: ")
                client.verify_code(code)
                print("Verification successful")
                
                # Now connect
                client.connect(restore_session=False)
                print("Connected with new registration")
            
            elif auth_choice == "q":
                print("Connecting with QR code authentication...")
                client.connect(restore_session=False, auth_method="qr")
                print("Please scan the QR code with your WhatsApp mobile app")
                print("Go to WhatsApp Settings > Linked Devices > Link a device")
            
            elif auth_choice == "p":
                print("Connecting with pairing code authentication...")
                pairing_code = input("Enter the 8-digit pairing code from your WhatsApp mobile app: ")
                print("To get a pairing code, open WhatsApp on your phone")
                print("Go to Settings > Linked Devices > Link a device > Can't scan QR code?")
                client.connect(restore_session=False, auth_method="pairing_code", pairing_code=pairing_code)
                print("Pairing code sent, waiting for authentication confirmation")
            
            else:
                print("To use the library, you need to authenticate first")
                sys.exit(1)
        
        # Set up message handler
        def on_message(message):
            print("\nNew message received:")
            if message.get('type') == 'text':
                print(f"From: {message.get('from')}")
                print(f"Content: {message.get('content')}")
                print()
            elif message.get('type') == 'media':
                print(f"From: {message.get('from')}")
                print(f"Media type: {message.get('media_type')}")
                print(f"Caption: {message.get('caption')}")
                print()
        
        # Register message handler
        client.on_message(on_message)
        
        # Main menu loop
        while True:
            print("\nWhatsApp Client Menu:")
            print("1. Send text message")
            print("2. Send image message")
            print("3. Create group")
            print("4. Get contact info")
            print("5. Disconnect and exit")
            
            choice = input("Enter choice (1-5): ")
            
            if choice == '1':
                # Send text message
                recipient = input("Enter recipient phone number: ")
                message = input("Enter message: ")
                
                try:
                    message_id = client.send_text_message(recipient, message)
                    print(f"Message sent with ID: {message_id}")
                except Exception as e:
                    print(f"Failed to send message: {e}")
                
            elif choice == '2':
                # Send image message
                recipient = input("Enter recipient phone number: ")
                image_path = input("Enter path to image file: ")
                caption = input("Enter caption (optional): ")
                
                try:
                    message_id = client.send_image(recipient, image_path, caption)
                    print(f"Image sent with ID: {message_id}")
                except Exception as e:
                    print(f"Failed to send image: {e}")
                
            elif choice == '3':
                # Create group
                subject = input("Enter group name: ")
                participants_input = input("Enter participant phone numbers (comma-separated): ")
                participants = [p.strip() for p in participants_input.split(',')]
                
                try:
                    group_info = client.create_group(subject, participants)
                    print(f"Group created with ID: {group_info['group_id']}")
                except Exception as e:
                    print(f"Failed to create group: {e}")
                
            elif choice == '4':
                # Get contact info
                phone = input("Enter contact phone number: ")
                
                try:
                    contact_info = client.get_contact(phone)
                    print("\nContact Information:")
                    print(f"Name: {contact_info.get('name', 'Unknown')}")
                    print(f"Phone: {contact_info.get('phone')}")
                    print(f"Status: {contact_info.get('status', 'No status')}")
                    print(f"WhatsApp User: {contact_info.get('is_whatsapp_user', False)}")
                except Exception as e:
                    print(f"Failed to get contact: {e}")
                
            elif choice == '5':
                # Disconnect and exit
                print("Disconnecting...")
                client.disconnect()
                print("Disconnected. Goodbye!")
                break
                
            else:
                print("Invalid choice, please try again")
            
            # Small delay before showing menu again
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure we disconnect properly
        if client and getattr(client, 'connected', False):
            client.disconnect()

if __name__ == "__main__":
    main()
