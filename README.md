# Nocksup - Python Library for WhatsApp

Nocksup is a modern Python library for WhatsApp communication, developed as a replacement for Yowsup.

## Features

- Compatible with current WhatsApp protocols (2025 update)
- Support for QR code or pairing code authentication
- Send and receive text messages
- Robust WebSocket connection management
- Support for multiple devices and persistent sessions
- Compatible with Termux on Android devices

## Installation

```bash
pip install nocksup
```

Or install from source:

```bash
git clone https://github.com/gyovannyvpn123/Nocksup.git
cd Nocksup
pip install -e .
```

## Basic Usage

### Connect with QR Code

```python
from nocksup.client.client import NocksupClient

# Create a client with your phone number
client = NocksupClient(phone_number="1234567890")

# Callback for received messages
def on_message(message):
    print(f"Message received from {message.get('sender')}: {message.get('text')}")

# Callback for QR code
def on_qr_code(qr_data):
    print("Scan this QR code with WhatsApp on your phone")
    # In real applications, you might display the QR code here

# Register the callbacks
client.on_message(on_message)
client.on_qr_code(on_qr_code)

# Connect using QR code
client.connect(auth_method='qr')

if client.is_connected():
    # Send a message
    client.send_text_message("1234567890", "Hello from Nocksup!")
    
    # Keep the application running to receive messages
    try:
        while client.is_connected():
            pass
    except KeyboardInterrupt:
        client.disconnect()
```

### Connect with Pairing Code

```python
from nocksup.client.client import NocksupClient

# Create a client with your phone number
client = NocksupClient(phone_number="1234567890")

# Callback for pairing code
def on_pairing_code(code):
    print(f"Enter this code in WhatsApp: {code}")

# Register the callback
client.on_pairing_code(on_pairing_code)

# Generate the pairing code
pairing_code = client.generate_pairing_code()

# Connect using the pairing code
client.connect(auth_method='pairing_code')

if client.is_connected():
    print("Successfully connected!")
    # Code for sending messages...
    
    client.disconnect()
```

## Troubleshooting

### Common Issues

1. **Connection errors**: Make sure you have a stable internet connection. The library will automatically attempt to reconnect.

2. **Authentication error**: Scan the QR code or enter the pairing code in the WhatsApp app on your phone.

3. **bad_baram error**: This error that occurs in other libraries has been resolved in Nocksup by updating the communication protocols.

4. **Unicode character errors**: Nocksup uses robust UTF-8 decoding to handle messages in any language.

### Debugging

To enable debug logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Current Limitations

- Support for audio/video calls is still in development
- Group message support is in beta
- Media message sending is still in development

## Legal Notes

This library is not affiliated with or officially endorsed by WhatsApp. Its use should comply with WhatsApp's terms and conditions.