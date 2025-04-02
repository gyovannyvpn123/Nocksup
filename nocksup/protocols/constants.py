"""
Constants for WhatsApp protocols.
"""

# WhatsApp version used by this library
WHATSAPP_WEB_VERSION = '2.2402.12'
WHATSAPP_VERSION = '2.24.3.76'

# Protocol definitions
PROTOCOL_VERSION = [0, 4]
WHATSAPP_DOMAIN = 's.whatsapp.net'
WHATSAPP_GROUP_DOMAIN = 'g.us'
WHATSAPP_BROADCAST_DOMAIN = 'broadcast'
WHATSAPP_SERVER = 'e{0}.whatsapp.net'  # {0} is replaced with a server ID (1-16)
WHATSAPP_WEBSOCKET_SERVER = 'web.whatsapp.com'

# Connection constants
WEBSOCKET_URL = 'wss://web.whatsapp.com/ws/chat'
ORIGIN_URL = 'https://web.whatsapp.com'

# Supported browser capabilities (sent when connecting)
CLIENT_CAPABILITIES = {
    'multi_device': True,
    'starred_messages': True,
    'status_messages': True,
    'label_display': True,
    'voice_message_transcription': True,
    'rich_presence': True,
    'app_background_sync': True,
    'business_features': True
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
}

# Authentication states
AUTH_STATES = {
    'disconnected': 'disconnected',
    'connecting': 'connecting',
    'authenticating': 'authenticating',
    'connected': 'connected',
    'failed': 'failed',
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
}

# Media upload/download URLs 
MEDIA_UPLOAD_URL = 'https://web.whatsapp.com/upload'
MEDIA_DOWNLOAD_URL = 'https://web.whatsapp.com/download'

# New Multi-device endpoints
MD_INIT_URL = 'https://web.whatsapp.com/multidevice/init'
MD_AUTH_URL = 'https://web.whatsapp.com/multidevice/auth'
MD_PAIR_URL = 'https://web.whatsapp.com/multidevice/pair'

# Registration/verification URLs
REGISTER_URL = 'https://v.whatsapp.net/v2/register'
VERIFY_URL = 'https://v.whatsapp.net/v2/code'
EXIST_URL = 'https://v.whatsapp.net/v2/exist'

# Max retry counts
MAX_LOGIN_RETRIES = 3
MAX_MESSAGE_RETRIES = 5
MAX_MEDIA_RETRIES = 3
