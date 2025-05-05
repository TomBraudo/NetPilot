import paramiko
import os
import sys
import logging
from utils.path_utils import get_data_folder
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSHClientManager:
    """
    Manages a persistent SSH connection to the router.
    """

    def __init__(self):
        # Load environment variables from .env file
        env_path = os.path.join(get_data_folder(), '.env')
        load_dotenv(dotenv_path=env_path)
        
        # Get configuration from environment variables
        self.router_ip = os.environ.get('ROUTER_IP', '192.168.1.1')
        self.username = os.environ.get('ROUTER_USERNAME', 'root')
        self.password = os.environ.get('ROUTER_PASSWORD', 'admin')
        self.ssh = None  # SSH session

    def connect(self):
        """
        Establish an SSH connection if not already connected.
        """
        try:
            if self.ssh is None or not self.ssh.get_transport() or not self.ssh.get_transport().is_active():
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(self.router_ip, username=self.username, password=self.password)
                return True
            return True
        except Exception as e:
            logger.error(f"SSH connection error: {str(e)}")
            return False

    def execute_command(self, command):
        """
        Executes a command on the router via SSH.
        """
        try:
            if not self.connect():  # Ensure connection is active
                return None, "Failed to connect to router"
                
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode().strip() if stdout else ""
            error = stderr.read().decode().strip() if stderr else ""
            
            return output, error if error else None
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return None, str(e)

    def close_connection(self):
        """
        Closes the SSH connection.
        """
        if self.ssh:
            try:
                self.ssh.close()
            except Exception as e:
                logger.error(f"Error closing SSH connection: {str(e)}")
            finally:
                self.ssh = None

# Initialize a single global instance of the SSH client
ssh_manager = SSHClientManager()
