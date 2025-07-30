"""
Commands Server Manager

This manager provides connection management and command execution for the commands server.
It handles connection health checking and provides a clean interface for executing commands
with enforced router_id and session_id requirements.
"""

import os
import time
import requests
from typing import Dict, Any, Optional, Tuple
from utils.logging_config import get_logger
from utils.response_unpack import unpack_commands_server_response

logger = get_logger('managers.commands_server')

class CommandsServerManager:
    """Manager for commands server operations with integrated HTTP communication."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize the commands server manager.
        
        Args:
            base_url: The base URL of the commands server. If None, will use COMMANDS_SERVER_URL env var.
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or os.getenv('COMMANDS_SERVER_URL', 'http://34.38.207.87:5000')).rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self._is_connected = False
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        
        # Set common headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'NetPilot-Backend2/1.0'
        })
        
        logger.info(f"Commands server manager initialized with URL: {self.base_url}")
    
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
                
                # Log the raw response for debugging
                if response_data.get('success') == False:
                    logger.warning(f"Commands server returned success=false but operation may have succeeded. Raw response: {response_data}")
                
                # Unpack the commands server response format
                data, error = unpack_commands_server_response(response_data)
                
                # Additional debugging for failed responses
                if error:
                    logger.error(f"Commands server operation failed. Unpacked error: {error}")
                
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
    
    def _is_health_check_needed(self) -> bool:
        """Check if a health check is needed."""
        current_time = time.time()
        return current_time - self._last_health_check > self._health_check_interval
    
    def is_connected(self) -> bool:
        """
        Check if the commands server is connected and healthy.
        
        Returns:
            True if connected and healthy, False otherwise
        """
        # If we need a health check, perform it
        if self._is_health_check_needed():
            logger.debug("Performing health check...")
            self._perform_health_check()
        
        return self._is_connected
    
    def _perform_health_check(self) -> bool:
        """
        Perform a health check on the commands server.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            logger.info("Checking commands server health")
            response_data, error = self._make_request('GET', '/health')
            
            if error:
                logger.warning(f"Commands server health check failed: {error}")
                self._is_connected = False
            else:
                logger.debug("Commands server health check successful")
                self._is_connected = True
                
            self._last_health_check = time.time()
            return self._is_connected
            
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            self._is_connected = False
            return False
    
    def execute_router_command(
        self,
        router_id: str,
        session_id: str,
        endpoint: str,
        method: str = "POST",
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Execute a command on a specific router through the commands server by sending a direct API call to the given endpoint.
        Args:
            router_id: The router ID (required, enforced but not used in path construction)
            session_id: The session ID (required, enforced but not used in path construction)
            endpoint: The full API endpoint path (e.g., '/router/123/session/abc/do_something')
            method: HTTP method (default 'POST')
            query_params: Query parameters for the request
            body: JSON body to send in the request
        Returns:
            Tuple of (response_data, error_message)
        """
        if not router_id:
            return None, "router_id is required"
        if not session_id:
            return None, "session_id is required"
        if not self.is_connected():
            return None, "Commands server is not connected"
        
        try:
            response_data, error = self._make_request(method, endpoint, data=body, params=query_params)
            
            if error:
                logger.error(f"Failed to execute command via direct endpoint '{endpoint}': {error}")
                return None, error
            
            logger.info(f"Successfully executed command via direct endpoint '{endpoint}'")
            return response_data, None
        except Exception as e:
            error_msg = f"Unexpected error executing command via direct endpoint '{endpoint}': {e}"
            logger.error(error_msg)
            return None, error_msg
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        self._is_connected = False
        logger.info("Commands server manager closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Global instance for shared use
commands_server_manager = CommandsServerManager() 