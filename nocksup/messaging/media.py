"""
Media handling for WhatsApp messages.

This module provides functionality for uploading, downloading, and
processing media content for WhatsApp messages.
"""
import os
import hashlib
import mimetypes
from typing import Dict, Any, Optional, Tuple, BinaryIO

from nocksup.utils.http_utils import HttpClient
from nocksup.utils.logger import logger
from nocksup.exceptions import MediaError
from nocksup.protocols.constants import (
    MEDIA_UPLOAD_URL,
    MEDIA_DOWNLOAD_URL,
    MEDIA_TYPES
)

class MediaUploader:
    """
    Handles uploading media for WhatsApp messages.
    """
    
    def __init__(self, http_client: HttpClient = None):
        """
        Initialize media uploader.
        
        Args:
            http_client: Optional HTTP client instance
        """
        self.http_client = http_client or HttpClient()
    
    def upload(self, file_path: str, media_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to WhatsApp servers.
        
        Args:
            file_path: Path to file
            media_type: Type of media (auto-detected if not provided)
            
        Returns:
            Dictionary with upload info
            
        Raises:
            MediaError: If upload fails
        """
        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                raise MediaError(f"File not found: {file_path}")
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Detect media type if not provided
            if not media_type:
                media_type = self._detect_media_type(file_path)
            
            # Validate media type
            if media_type not in MEDIA_TYPES.values():
                logger.warning(f"Unrecognized media type: {media_type}")
            
            # Calculate hash for file
            file_hash = self._calculate_file_hash(file_path)
            
            # Get mime type
            mime_type = self._get_mime_type(file_path)
            
            # Prepare upload parameters
            params = {
                'hash': file_hash,
                'type': media_type,
                'size': file_size,
                'mime': mime_type
            }
            
            # Get upload URL
            upload_info = self._request_upload_url(params)
            
            # Upload the file
            upload_url = upload_info.get('url')
            if not upload_url:
                raise MediaError("No upload URL received")
            
            # Upload file to provided URL
            with open(file_path, 'rb') as f:
                self._upload_to_url(upload_url, f, mime_type, file_size)
            
            # Return upload info with additional details
            return {
                'media_url': upload_info.get('url'),
                'media_key': upload_info.get('media_key'),
                'file_enc_sha256': upload_info.get('file_enc_sha256'),
                'direct_path': upload_info.get('direct_path'),
                'mime_type': mime_type,
                'file_size': file_size,
                'file_name': os.path.basename(file_path),
                'media_type': media_type
            }
            
        except MediaError:
            # Re-raise existing MediaError
            raise
        except Exception as e:
            logger.error(f"Media upload failed: {e}")
            raise MediaError(f"Failed to upload media: {str(e)}")
    
    def _request_upload_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request upload URL from WhatsApp servers.
        
        Args:
            params: Upload parameters
            
        Returns:
            Upload URL info
            
        Raises:
            MediaError: If request fails
        """
        try:
            # Request upload URL
            response = self.http_client.post(
                MEDIA_UPLOAD_URL,
                json_data=params
            )
            
            # Check response
            if 'url' not in response:
                error = response.get('error', 'Unknown error')
                raise MediaError(f"Failed to get upload URL: {error}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to request upload URL: {e}")
            raise MediaError(f"Failed to request upload URL: {str(e)}")
    
    def _upload_to_url(self, url: str, file: BinaryIO, mime_type: str, 
                     file_size: int) -> None:
        """
        Upload file to provided URL.
        
        Args:
            url: Upload URL
            file: File object to upload
            mime_type: MIME type of file
            file_size: Size of file in bytes
            
        Raises:
            MediaError: If upload fails
        """
        try:
            # Set headers for upload
            headers = {
                'Content-Type': mime_type,
                'Content-Length': str(file_size)
            }
            
            # Upload file
            response = self.http_client.post(
                url,
                data=file.read(),
                headers=headers
            )
            
            # Check response
            if 'success' not in response or not response['success']:
                error = response.get('error', 'Unknown error')
                raise MediaError(f"Upload failed: {error}")
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise MediaError(f"Failed to upload file: {str(e)}")
    
    def _detect_media_type(self, file_path: str) -> str:
        """
        Detect media type from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Media type
        """
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Map extension to media type
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return MEDIA_TYPES['image']
        elif ext in ['.mp4', '.mov', '.avi', '.webm']:
            return MEDIA_TYPES['video']
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            return MEDIA_TYPES['audio']
        elif ext in ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt']:
            return MEDIA_TYPES['document']
        elif ext in ['.webp', '.sticker']:
            return MEDIA_TYPES['sticker']
        else:
            # Default to document
            return MEDIA_TYPES['document']
    
    def _get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type for file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MIME type
        """
        # Try to get MIME type from file
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Default MIME types based on extension if not detected
        if not mime_type:
            ext = os.path.splitext(file_path)[1].lower()
            
            # Default MIME types for common extensions
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo',
                '.webm': 'video/webm',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.ogg': 'audio/ogg',
                '.m4a': 'audio/mp4',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.txt': 'text/plain'
            }
            
            mime_type = mime_map.get(ext, 'application/octet-stream')
        
        return mime_type
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash for file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of hash
        """
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()

class MediaDownloader:
    """
    Handles downloading media from WhatsApp messages.
    """
    
    def __init__(self, http_client: HttpClient = None):
        """
        Initialize media downloader.
        
        Args:
            http_client: Optional HTTP client instance
        """
        self.http_client = http_client or HttpClient()
    
    def download(self, media_url: str, output_path: str, 
                media_key: str = None) -> str:
        """
        Download media from WhatsApp servers.
        
        Args:
            media_url: URL of the media
            output_path: Path to save the file
            media_key: Optional media key for decryption
            
        Returns:
            Path to downloaded file
            
        Raises:
            MediaError: If download fails
        """
        try:
            # Make sure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Download the file
            logger.info(f"Downloading media from {media_url}")
            success = self.http_client.download_file(media_url, output_path)
            
            if not success:
                raise MediaError("Download failed")
            
            # Decrypt if media key provided (not implemented in demo)
            if media_key:
                logger.info("Media key provided, decryption would happen here")
                # self._decrypt_media(output_path, media_key)
            
            logger.info(f"Media downloaded to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Media download failed: {e}")
            raise MediaError(f"Failed to download media: {str(e)}")
    
    def _decrypt_media(self, file_path: str, media_key: str) -> None:
        """
        Decrypt downloaded media file.
        
        Args:
            file_path: Path to encrypted file
            media_key: Key for decryption
            
        Raises:
            MediaError: If decryption fails
        """
        # In a real implementation, this would decrypt the file using the media key
        # WhatsApp uses AES for media encryption
        logger.info(f"Decrypting media file: {file_path}")
        
        # Simplified example - real implementation would be more complex
        try:
            # This is a placeholder for the actual decryption code
            # which would involve:
            # 1. Parsing the file header
            # 2. Extracting the initialization vector
            # 3. Decrypting using AES
            # 4. Validating the decrypted data
            pass
            
        except Exception as e:
            logger.error(f"Media decryption failed: {e}")
            raise MediaError(f"Failed to decrypt media: {str(e)}")

class MediaMessage:
    """
    Represents a WhatsApp media message.
    
    This class provides additional functionality for media messages,
    including uploading and downloading.
    """
    
    def __init__(self, media_type: str, file_path: str = None, url: str = None, 
                caption: str = None, uploader: MediaUploader = None):
        """
        Initialize media message.
        
        Args:
            media_type: Type of media
            file_path: Path to local file (for sending)
            url: URL of media (for received messages)
            caption: Optional caption
            uploader: Optional media uploader instance
        """
        self.media_type = media_type
        self.file_path = file_path
        self.url = url
        self.caption = caption
        self.uploader = uploader or MediaUploader()
        self.media_info = None
        
    def prepare_for_sending(self) -> Dict[str, Any]:
        """
        Prepare media for sending.
        
        Returns:
            Media info dictionary
            
        Raises:
            MediaError: If preparation fails
        """
        if not self.file_path:
            raise MediaError("No file path provided for media")
        
        try:
            # Upload the file
            self.media_info = self.uploader.upload(self.file_path, self.media_type)
            
            # Add caption if provided
            if self.caption:
                self.media_info['caption'] = self.caption
            
            return self.media_info
            
        except Exception as e:
            logger.error(f"Failed to prepare media: {e}")
            raise MediaError(f"Failed to prepare media: {str(e)}")
    
    @staticmethod
    def download_media(media_url: str, output_path: str, 
                     media_key: str = None) -> str:
        """
        Download media from a message.
        
        Args:
            media_url: URL of the media
            output_path: Path to save the file
            media_key: Optional media key for decryption
            
        Returns:
            Path to downloaded file
        """
        downloader = MediaDownloader()
        return downloader.download(media_url, output_path, media_key)
