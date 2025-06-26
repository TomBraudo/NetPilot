import paramiko
import os
from utils.path_utils import get_data_folder
from dotenv import load_dotenv
from typing import Optional
from flask import g, current_app
from managers.router_connection_manager import RouterConnectionManager

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

    def execute_command(self, command, session_id: Optional[str] = None, router_id: Optional[str] = None):
        """
        Execute *command* on the target router identified by *(session_id,
        router_id)*.  If the identifiers are omitted they are pulled from the
        active Flask request context (`flask.g`).  Both identifiers are
        mandatory – legacy single-connection behaviour has been removed.
        """
        # Attempt to pull IDs from Flask request context (no exception
        # raised if outside of an active request).
        try:
            session_id = session_id or getattr(g, "session_id", None)
            router_id = router_id or getattr(g, "router_id", None)
        except RuntimeError:
            # Not inside Flask application context
            pass
        if not session_id or not router_id:
            raise ValueError("session_id and router_id must be supplied for SSH commands")

        # Obtain connection via RouterConnectionManager
        
        rcm = current_app.router_connection_manager
        output, error = rcm.execute(session_id, router_id, command)
        return output, error if error else None

    def close_connection(self):
        """
        Closes the SSH connection.
        """
        if self.ssh:
            self.ssh.close()
            self.ssh = None

# Initialize a single global instance of the SSH client
ssh_manager = SSHClientManager()
