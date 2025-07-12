"""
Commands Server Manager

This manager provides high-level operations for interacting with the commands server.
It handles connection management, caching, and provides a clean interface for other components.
"""

import os
import time
from typing import Dict, Any, Optional, Tuple
from utils.logging_config import get_logger
from services.commands_server_service import CommandsServerService

logger = get_logger('managers.commands_server')

class CommandsServerManager:
    """Manager for commands server operations."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the commands server manager.
        
        Args:
            base_url: The base URL of the commands server. If None, will use COMMANDS_SERVER_URL env var.
        """
        self.base_url = base_url or os.getenv('COMMANDS_SERVER_URL', 'http://34.38.207.87:5000')
        self.service = None
        self._is_connected = False
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        self._server_info = None
        
        logger.info(f"Commands server manager initialized with URL: {self.base_url}")
    
    def _get_service(self) -> CommandsServerService:
        """Get or create the commands server service."""
        if self.service is None:
            self.service = CommandsServerService(self.base_url)
        return self.service
    
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
            service = self._get_service()
            response_data, error = service.health_check()
            
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
    
    def get_server_info(self, force_refresh: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get server information from the commands server.
        
        Args:
            force_refresh: If True, force a refresh of cached server info
            
        Returns:
            Tuple of (server_info, error_message)
        """
        # Return cached info if available and not forcing refresh
        if self._server_info and not force_refresh:
            return self._server_info, None
        
        if not self.is_connected():
            return None, "Commands server is not connected"
        
        try:
            service = self._get_service()
            response_data, error = service.get_server_info()
            
            if error:
                logger.error(f"Failed to get server info: {error}")
                return None, error
            
            # Cache the server info
            self._server_info = response_data
            return response_data, None
            
        except Exception as e:
            error_msg = f"Unexpected error getting server info: {e}"
            logger.error(error_msg)
            return None, error_msg
    
    def execute_router_command(
        self, 
        router_id: str, 
        command: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Execute a command on a specific router through the commands server.
        
        Args:
            router_id: The router ID
            command: The command to execute
            params: Command parameters
            
        Returns:
            Tuple of (response_data, error_message)
        """
        if not self.is_connected():
            return None, "Commands server is not connected"
        
        try:
            service = self._get_service()
            
            # Add router_id to params
            if params is None:
                params = {}
            params['router_id'] = router_id
            
            response_data, error = service.execute_command(command, params)
            
            if error:
                logger.error(f"Failed to execute command '{command}' on router {router_id}: {error}")
                return None, error
            
            logger.info(f"Successfully executed command '{command}' on router {router_id}")
            return response_data, None
            
        except Exception as e:
            error_msg = f"Unexpected error executing command '{command}' on router {router_id}: {e}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_router_status(self, router_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get the status of a specific router.
        
        Args:
            router_id: The router ID
            
        Returns:
            Tuple of (router_status, error_message)
        """
        if not self.is_connected():
            return None, "Commands server is not connected"
        
        try:
            service = self._get_service()
            response_data, error = service.get_router_status(router_id)
            
            if error:
                logger.error(f"Failed to get router status for {router_id}: {error}")
                return None, error
            
            return response_data, None
            
        except Exception as e:
            error_msg = f"Unexpected error getting router status for {router_id}: {e}"
            logger.error(error_msg)
            return None, error_msg
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test the connection to the commands server.
        
        Returns:
            Tuple of (is_connected, error_message)
        """
        logger.info("Testing commands server connection...")
        
        try:
            # Force a health check
            is_healthy = self._perform_health_check()
            
            if is_healthy:
                logger.info("Commands server connection test successful")
                return True, None
            else:
                error_msg = "Commands server connection test failed"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error testing connection: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def close(self):
        """Close the connection to the commands server."""
        if self.service:
            self.service.close()
            self.service = None
        
        self._is_connected = False
        self._server_info = None
        logger.info("Commands server manager closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Global instance for shared use
commands_server_manager = CommandsServerManager() 