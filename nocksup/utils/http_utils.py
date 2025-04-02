"""
HTTP utilities for WhatsApp API communication.
"""
import json
import time
from typing import Dict, Any, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from nocksup.exceptions import ConnectionError
from nocksup.utils.logger import logger
from nocksup.config import USER_AGENT, SOCKET_TIMEOUT, MAX_RETRIES, RETRY_DELAY

class HttpClient:
    """HTTP client for WhatsApp API communication."""
    
    def __init__(self, timeout: int = None, max_retries: int = None, 
                 retry_delay: int = None, user_agent: str = None):
        """
        Initialize the HTTP client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            user_agent: User agent string to use
        """
        self.timeout = timeout or SOCKET_TIMEOUT
        self.max_retries = max_retries or MAX_RETRIES
        self.retry_delay = retry_delay or RETRY_DELAY
        self.user_agent = user_agent or USER_AGENT
        
        # Create session with retry strategy
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry capability.
        
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        return session
    
    def get(self, url: str, params: Dict[str, Any] = None, 
            headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send a GET request.
        
        Args:
            url: URL to request
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response as dictionary
        
        Raises:
            ConnectionError: If request fails
        """
        try:
            response = self.session.get(
                url, 
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return self._parse_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {e}")
            raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
    
    def post(self, url: str, data: Optional[Union[Dict[str, Any], bytes]] = None,
             json_data: Optional[Dict[str, Any]] = None,
             headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send a POST request.
        
        Args:
            url: URL to request
            data: Form data or raw bytes
            json_data: JSON data (will be serialized)
            headers: Additional headers
            
        Returns:
            Response as dictionary
        
        Raises:
            ConnectionError: If request fails
        """
        try:
            response = self.session.post(
                url, 
                data=data,
                json=json_data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return self._parse_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {e}")
            raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse the response based on content type.
        
        Args:
            response: Response object
            
        Returns:
            Parsed response as dictionary
        """
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            return response.json()
        else:
            # Return text response in a dictionary
            return {
                'status': response.status_code,
                'text': response.text,
                'headers': dict(response.headers)
            }
    
    def download_file(self, url: str, output_path: str, 
                      headers: Dict[str, str] = None) -> bool:
        """
        Download a file.
        
        Args:
            url: URL to download from
            output_path: Path to save the file to
            headers: Additional headers
            
        Returns:
            True if successful, False otherwise
        
        Raises:
            ConnectionError: If download fails
        """
        try:
            response = self.session.get(
                url,
                headers=headers,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except (requests.exceptions.RequestException, IOError) as e:
            logger.error(f"File download failed: {e}")
            raise ConnectionError(f"Failed to download file from {url}: {str(e)}")
    
    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
