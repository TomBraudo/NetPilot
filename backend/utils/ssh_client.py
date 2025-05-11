import paramiko
import json
import os
import sys
from utils.path_utils import get_data_folder
from dotenv import load_dotenv

class SSHClientManager:
    """
    Manages a persistent SSH connection to the router.
    """

    def __init__(self):
        # Load .env from the data folder
        self.env_path = self.get_env_path()
        load_dotenv(self.env_path)

        self.router_ip = os.getenv("ROUTER_IP")
        self.username = os.getenv("ROUTER_USERNAME")
        self.password = os.getenv("ROUTER_PASSWORD")
        self.ssh = None  # SSH session

        # Debug: print loaded values (mask password for safety)
        print(f"ROUTER_IP: {self.router_ip}")
        print(f"USERNAME: {self.username}")
        print(f"PASSWORD: {'*' * len(self.password) if self.password else None}")

    def get_env_path(self):
        """
        Determines the correct location of .env.
        Ensures it works for both normal script execution and when packaged as an .exe.
        """
        print(f"Getting env path: {get_data_folder()}")
        print(f"Env path: {os.path.join(get_data_folder(), '.env')}")
        return os.path.join(get_data_folder(), ".env")  # Ensures .env is in the same folder as server.exe


    def connect(self):
        """
        Establish an SSH connection if not already connected.
        """
        if self.ssh is None or not self.ssh.get_transport().is_active():
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.router_ip, username=self.username, password=self.password)

    def execute_command(self, command):
        """
        Executes a command on the router via SSH.
        """
        try:
            self.connect()  # Ensure connection is active
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            return output, error if error else None
        except Exception as e:
            return None, str(e)

    def close_connection(self):
        """
        Closes the SSH connection.
        """
        if self.ssh:
            self.ssh.close()
            self.ssh = None

# Initialize a single global instance of the SSH client
ssh_manager = SSHClientManager()
