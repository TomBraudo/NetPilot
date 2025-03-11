import paramiko
import json
import os
import sys

class SSHClientManager:
    """
    Manages a persistent SSH connection to the router.
    """

    def __init__(self):
        # Determine the correct path for config.json
        self.config_path = self.get_config_path()
        
        # Load router credentials from config.json
        with open(self.config_path, "r") as config_file:
            config = json.load(config_file)

        self.router_ip = config["router_ip"]
        self.username = config["username"]
        self.password = config["password"]
        self.ssh = None  # SSH session

    def get_config_path(self):
        """
        Determines the correct location of config.json.
        Ensures it works for both normal script execution and when packaged as an .exe.
        """
        if getattr(sys, 'frozen', False):  # Running as a .exe
            base_path = os.path.dirname(sys.executable)  # Directory of server.exe
        else:  # Running as a script
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, "config.json")  # Ensures config.json is in the same folder as server.exe


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
