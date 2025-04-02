"""
Constants for WhatsApp protocols.
"""

# WhatsApp version used by this library - aceste versiuni trebuie actualizate periodic
WHATSAPP_WEB_VERSION = '2.2413.59'  # Actualizat pentru 2025
WHATSAPP_VERSION = '2.25.4.76'      # Actualizat pentru 2025

# Protocol definitions
PROTOCOL_VERSION = [0, 5]  # Actualizat la protocolul 0.5
WHATSAPP_DOMAIN = 's.whatsapp.net'
WHATSAPP_GROUP_DOMAIN = 'g.us'
WHATSAPP_BROADCAST_DOMAIN = 'broadcast'
WHATSAPP_SERVER = 'e{0}.whatsapp.net'  # {0} is replaced with a server ID (1-16)
WHATSAPP_WEBSOCKET_SERVER = 'web.whatsapp.com'

# Connection constants
WEBSOCKET_URL = 'wss://web.whatsapp.com/ws/chat'
ORIGIN_URL = 'https://web.whatsapp.com'

# WebSocket opcodes pentru noul protocol
WS_OPCODES = {
    'CONTINUATION': 0x0,
    'TEXT': 0x1,
    'BINARY': 0x2,
    'CLOSE': 0x8,
    'PING': 0x9,
    'PONG': 0xA
}

# WAWebXXX Frame constants pentru noul protocol
WA_FRAME_PREFIX = b'WAW'      # Noul prefix pentru mesajele WhatsApp Web
WA_METADATA_SIZE = 4          # Dimensiunea metadatelor în octeți
WA_VERSION_SIZE = 3           # Dimensiunea versiunii în octeți

# Supported browser capabilities (sent when connecting)
CLIENT_CAPABILITIES = {
    'multi_device': True,
    'starred_messages': True,
    'status_messages': True,
    'label_display': True,
    'voice_message_transcription': True,
    'rich_presence': True,
    'app_background_sync': True,
    'business_features': True,
    'companion_features': True,   # Adăugat pentru dispozitive asociate
    'link_preview': True          # Adăugat pentru previzualizări link-uri
}

# Media types
MEDIA_TYPES = {
    'image': 'image',
    'video': 'video',
    'audio': 'audio',
    'document': 'document',
    'sticker': 'sticker',
    'ptt': 'ptt',       # Push to talk voice message
    'gif': 'gif',
    'voice_note': 'voice_note'  # Adăugat pentru note vocale
}

# Message types
MESSAGE_TYPES = {
    'text': 'text',
    'media': 'media',
    'contact': 'contact',
    'location': 'location',
    'call': 'call',
    'system': 'system',
    'revoked': 'revoked',
    'groups_v4_invite': 'groups_v4_invite',
    'reaction': 'reaction',     # Adăugat pentru reacții
    'poll': 'poll',             # Adăugat pentru sondaje
    'template': 'template',     # Adăugat pentru mesaje template
    'product': 'product'        # Adăugat pentru produse
}

# Presence types
PRESENCE_TYPES = {
    'available': 'available',        # Online
    'unavailable': 'unavailable',    # Offline
    'composing': 'composing',        # Typing
    'recording': 'recording',        # Recording audio
    'paused': 'paused',              # Paused typing/recording
}

# Account status
ACCOUNT_STATUS = {
    'active': 'active',             # Active account
    'banned': 'banned',             # Banned account
    'restricted': 'restricted',     # Restricted account
    'unregistered': 'unregistered', # Not registered
}

# Node types (based on WhatsApp protocol)
NODE_TYPES = {
    'message': 'message',
    'receipt': 'receipt',
    'presence': 'presence',
    'iq': 'iq',                      # Info/Query
    'notification': 'notification',
    'stream': 'stream',
    'success': 'success',
    'failure': 'failure',
    'ack': 'ack',                    # Acknowledgement
    'error': 'error',
    'stream:features': 'stream:features',
    'auth': 'auth',
    'challenge': 'challenge',
    'response': 'response',
    'stream:error': 'stream:error',
    'ping': 'ping',
    'pong': 'pong',
    'handshake': 'handshake',        # Adăugat pentru noul protocol
    'pairing': 'pairing',            # Adăugat pentru asocierea dispozitivelor
}

# Stream error codes
STREAM_ERROR_CODES = {
    'invalid-stream': 'invalid-stream',
    'not-authorized': 'not-authorized',
    'service-unavailable': 'service-unavailable',
    'internal-server-error': 'internal-server-error',
    'connection-timeout': 'connection-timeout',
    'system-shutdown': 'system-shutdown',
    'conflict': 'conflict',
    'invalid-from': 'invalid-from',
    'invalid-to': 'invalid-to',
    'unsupported-encoding': 'unsupported-encoding',
    'unsupported-stanza-type': 'unsupported-stanza-type',
    'unsupported-version': 'unsupported-version',
    'stream-closed': 'stream-closed',
    'recipient-unavailable': 'recipient-unavailable',
    'stanza-too-big': 'stanza-too-big',
    'bad-namespace-prefix': 'bad-namespace-prefix',
    'unsupported-feature': 'unsupported-feature',
    'restricted-xml': 'restricted-xml',
    'bad-baram': 'bad-baram',               # Adăugat pentru eroarea bad_baram
    'unknown-protocol': 'unknown-protocol',  # Adăugat pentru protocol necunoscut
}

# Authentication states
AUTH_STATES = {
    'disconnected': 'disconnected',
    'connecting': 'connecting',
    'authenticating': 'authenticating',
    'connected': 'connected',
    'failed': 'failed',
    'pairing': 'pairing',         # Adăugat pentru asociere
    'paired': 'paired',           # Adăugat pentru asociere completă
}

# Message status
MESSAGE_STATUS = {
    'pending': 'pending',           # Not yet sent
    'sent': 'sent',                 # Sent but not delivered
    'delivered': 'delivered',       # Delivered but not read
    'read': 'read',                 # Read by recipient
    'played': 'played',             # Played (for audio/video)
    'failed': 'failed',             # Failed to send
}

# Group participant types
GROUP_PARTICIPANT_TYPES = {
    'admin': 'admin',               # Group admin
    'superadmin': 'superadmin',     # Group creator
    'member': 'member',             # Regular member
    'restricted': 'restricted',     # Restricted member
    'removed': 'removed',           # Removed member
}