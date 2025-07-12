"""
Commands Server Service

This service handles low-level HTTP communication with the commands server.
It provides methods for making requests to various commands server endpoints.
"""

import requests
import time
from typing import Dict, Any, Optional, Tuple
from utils.logging_config import get_logger
from utils.response_unpack import unpack_commands_server_response

logger = get_logger('services.commands_server')

class CommandsServerService:
    """Service for communicating with the commands server."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the commands server service.
        
        Args:
            base_url: The base URL of the commands server (e.g., 'http://34.38.207.87:5000')
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set common headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'NetPilot-Backend2/1.0'
        })
        
        logger.info(f"Commands server service initialized with base URL: {self.base_url}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Make a request to the commands server.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/health')
            data: JSON data to send in the request body
            params: Query parameters
            
        Returns:
            Tuple of (response_data, error_message)
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            logger.debug(f"Request completed in {execution_time:.2f}s with status {response.status_code}")
            
            # Check if response is successful
            if response.status_code >= 400:
                error_msg = f"Commands server returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                return None, error_msg
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                logger.debug(f"Received response: {response_data}")
                
                # Unpack the commands server response format
                data, error = unpack_commands_server_response(response_data)
                return data, error
            except requests.exceptions.JSONDecodeError:
                # If not JSON, return the text content
                return {"message": response.text}, None
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error to commands server: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout to commands server: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error to commands server: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def health_check(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Check the health status of the commands server.
        
        Returns:
            Tuple of (response_data, error_message)
        """
        logger.info("Checking commands server health")
        return self._make_request('GET', '/health')
    
    def get_server_info(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get server information from the commands server.
        
        Returns:
            Tuple of (response_data, error_message)
        """
        logger.info("Getting commands server info")
        return self._make_request('GET', '/info')
    
    # Template methods for future endpoints
    def execute_command(
        self, 
        command: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Execute a command on the commands server.
        
        Args:
            command: The command to execute
            params: Command parameters
            
        Returns:
            Tuple of (response_data, error_message)
        """
        logger.info(f"Executing command: {command}")
        data = {"command": command}
        if params:
            data["params"] = params
        
        return self._make_request('POST', '/execute', data=data)
    
    def get_router_status(self, router_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get the status of a specific router.
        
        Args:
            router_id: The router ID
            
        Returns:
            Tuple of (response_data, error_message)
        """
        logger.info(f"Getting router status for: {router_id}")
        return self._make_request('GET', f'/router/{router_id}/status')
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.info("Commands server service session closed") 