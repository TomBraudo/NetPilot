#!/usr/bin/env python3
"""
Commands Server Client

This is a minimal test client that demonstrates how to use the commands server integration.
It provides a simple interface to test the connection and execute basic operations.
"""

import sys
import os
import json
from typing import Dict, Any, Optional

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logging_config import get_logger
from managers.commands_server_manager import commands_server_manager

logger = get_logger('commands_server_client')

class CommandsServerClient:
    """A simple client for testing commands server operations."""
    
    def __init__(self):
        """Initialize the client."""
        self.manager = commands_server_manager
        logger.info("Commands server client initialized")
    
    def test_health_check(self) -> bool:
        """
        Test the health check endpoint.
        
        Returns:
            True if healthy, False otherwise
        """
        print("Testing commands server health check...")
        
        try:
            is_connected, error = self.manager.test_connection()
            
            if is_connected:
                print("✅ Commands server is healthy and connected")
                return True
            else:
                print(f"❌ Commands server health check failed: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error during health check: {e}")
            return False
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Get server information.
        
        Returns:
            Server info dict or None if failed
        """
        print("Getting server information...")
        
        try:
            server_info, error = self.manager.get_server_info()
            
            if server_info:
                print("✅ Server information retrieved successfully:")
                print(json.dumps(server_info, indent=2))
                return server_info
            else:
                print(f"❌ Failed to get server info: {error}")
                return None
                
        except Exception as e:
            print(f"❌ Unexpected error getting server info: {e}")
            return None
    
    def test_router_command(self, router_id: str, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Test executing a command on a router.
        
        Args:
            router_id: The router ID
            command: The command to execute
            params: Command parameters
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Testing router command '{command}' on router {router_id}...")
        
        try:
            response_data, error = self.manager.execute_router_command(router_id, command, params)
            
            if response_data:
                print("✅ Router command executed successfully:")
                print(json.dumps(response_data, indent=2))
                return True
            else:
                print(f"❌ Router command failed: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error executing router command: {e}")
            return False
    
    def test_router_status(self, router_id: str) -> Optional[Dict[str, Any]]:
        """
        Test getting router status.
        
        Args:
            router_id: The router ID
            
        Returns:
            Router status dict or None if failed
        """
        print(f"Getting router status for {router_id}...")
        
        try:
            status, error = self.manager.get_router_status(router_id)
            
            if status:
                print("✅ Router status retrieved successfully:")
                print(json.dumps(status, indent=2))
                return status
            else:
                print(f"❌ Failed to get router status: {error}")
                return None
                
        except Exception as e:
            print(f"❌ Unexpected error getting router status: {e}")
            return None
    
    def run_basic_tests(self) -> bool:
        """
        Run basic tests to verify the commands server integration.
        
        Returns:
            True if all tests pass, False otherwise
        """
        print("=" * 50)
        print("Running Commands Server Client Tests")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 2
        
        # Test 1: Health Check
        print("\n1. Testing Health Check")
        print("-" * 30)
        if self.test_health_check():
            tests_passed += 1
        
        # Test 2: Server Info
        print("\n2. Testing Server Info")
        print("-" * 30)
        if self.get_server_info():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print(f"Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("✅ All tests passed! Commands server integration is working.")
            return True
        else:
            print("❌ Some tests failed. Please check the configuration and server status.")
            return False
    
    def interactive_mode(self):
        """Run in interactive mode for manual testing."""
        print("\n" + "=" * 50)
        print("Commands Server Client - Interactive Mode")
        print("=" * 50)
        print("Available commands:")
        print("  1. health    - Check server health")
        print("  2. info      - Get server info")
        print("  3. status    - Get router status (requires router_id)")
        print("  4. command   - Execute router command (requires router_id and command)")
        print("  5. test      - Run basic tests")
        print("  6. quit      - Exit")
        print()
        
        while True:
            try:
                cmd = input("Enter command (1-6): ").strip().lower()
                
                if cmd in ['1', 'health']:
                    self.test_health_check()
                elif cmd in ['2', 'info']:
                    self.get_server_info()
                elif cmd in ['3', 'status']:
                    router_id = input("Enter router ID: ").strip()
                    if router_id:
                        self.test_router_status(router_id)
                elif cmd in ['4', 'command']:
                    router_id = input("Enter router ID: ").strip()
                    command = input("Enter command: ").strip()
                    if router_id and command:
                        self.test_router_command(router_id, command)
                elif cmd in ['5', 'test']:
                    self.run_basic_tests()
                elif cmd in ['6', 'quit']:
                    print("Goodbye!")
                    break
                else:
                    print("Invalid command. Please enter 1-6.")
                
                print()  # Add spacing between commands
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break

def main():
    """Main entry point."""
    print("Commands Server Client")
    print("=" * 30)
    
    client = CommandsServerClient()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Run basic tests
            success = client.run_basic_tests()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == 'health':
            # Quick health check
            success = client.test_health_check()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == 'interactive':
            # Interactive mode
            client.interactive_mode()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python commands-server-client.py [test|health|interactive]")
            sys.exit(1)
    else:
        # Default: run basic tests
        success = client.run_basic_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 