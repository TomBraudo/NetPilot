import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import os
import paramiko
import requests
from flask import g

# Local
from utils.logging_config import get_logger

# Module-level logger
logger = get_logger('managers.router_connection_manager')

__all__ = ["RouterConnectionManager"]


class PortManagerClient:
    """Simple HTTP client for the cloud Port-Manager service."""

    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_allocation(self, router_id: str) -> Optional[dict]:
        """Return allocation dict with keys: port, routerUsername, routerPassword"""
        try:
            resp = requests.get(
                f"{self.base_url}/api/port-status",
                params={"routerId": router_id},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data.get("data")
        except requests.RequestException:
            pass
        return None


class _RouterConnection:
    """Wrapper containing a paramiko client and metadata."""

    def __init__(self, client: paramiko.SSHClient, tunnel_port: int):
        self.client = client
        self.tunnel_port = tunnel_port
        self.last_used: datetime = datetime.utcnow()

    def exec_command(self, command: str, timeout: int = 30) -> Tuple[str, str]:
        self.last_used = datetime.utcnow()
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err

    def is_active(self) -> bool:
        transport = self.client.get_transport()
        return transport is not None and transport.is_active()

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass


class RouterConnectionManager:
    """Singleton that manages SSH connections per (sessionId, routerId)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_internal()
        return cls._instance

    # ------------------------ internal -------------------------
    def _init_internal(self):
        self._lock = threading.RLock()
        self._sessions: Dict[str, Dict[str, _RouterConnection]] = {}
        self._active_sessions: Dict[str, datetime] = {}

        # Config
        base_url = os.getenv("PORT_MANAGER_URL", "http://localhost:8080")
        self._pm_client = PortManagerClient(base_url)
        self._connection_idle = int(os.getenv("CONNECTION_TIMEOUT_MINUTES", 5)) * 60
        self._session_idle = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30)) * 60

        # Start janitor thread
        self._stop_event = threading.Event()
        self._janitor = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._janitor.start()

    # ------------------------ public API -----------------------
    def start_session(self, session_id: str):
        with self._lock:
            self._active_sessions[session_id] = datetime.utcnow()

    def end_session(self, session_id: str):
        with self._lock:
            self._active_sessions.pop(session_id, None)
            routers = self._sessions.pop(session_id, {})
            for conn in routers.values():
                conn.close()

    def get_session_status(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._active_sessions

    def execute(self, command: str, timeout: int = 30) -> Tuple[str, str]:
        session_id = g.get("session_id")
        router_id = g.get("router_id")
        if not session_id or not router_id:
            raise RuntimeError("Session context (sessionId, routerId) not found in g")

        conn = self._get_or_create_connection(session_id, router_id)
        try:
            return conn.exec_command(command, timeout=timeout)
        except Exception as e:
            logger.error(f"Unexpected error when executing command for router {router_id}: {e}")
            return None, str(e)

    def copy_file(self, local_path: str, remote_path: str, make_executable: bool = True, normalize_crlf: bool = True) -> Tuple[bool, str]:
        """Copy a local file to the router using SFTP (scp-like) with optional CRLF normalization and chmod.

        Returns (True, None) on success, or (False, error_message) on failure.
        """
        session_id = g.get("session_id")
        router_id = g.get("router_id")
        if not session_id or not router_id:
            return False, "Session context not found"

        # Ensure an active SSH connection exists
        try:
            conn = self._get_or_create_connection(session_id, router_id)
        except Exception as e:
            return False, f"Failed to establish SSH connection: {e}"

        # Determine remote parent directory early (used by both paths)
        import os as _os
        parent = _os.path.dirname(remote_path) or "/"

        # Helper: inline fallback using streamed stdin (preferred), then heredoc as final fallback
        def _fallback_inline_copy() -> Tuple[bool, str]:
            # Read local file
            try:
                with open(local_path, 'rb') as f:
                    data = f.read()
            except Exception as e:
                return False, f"Failed to read local file: {e}"

            # Normalize CRLF locally if requested
            if normalize_crlf:
                try:
                    data = data.replace(b'\r\n', b'\n')
                except Exception:
                    pass

            # Ensure remote parent directory
            self.execute(f"mkdir -p {parent} 2>/dev/null || true")

            # Stream to remote via stdin
            try:
                stdin, stdout, stderr = conn.client.exec_command(f"cat > {remote_path}")
                try:
                    stdin.write(data)
                except TypeError:
                    # Paramiko expects str for write in some versions; decode as ISO-8859-1 as raw passthrough
                    stdin.write(data.decode('ISO-8859-1', errors='ignore'))
                stdin.flush()
                stdin.channel.shutdown_write()
                # Wait for command to finish
                stdout.channel.recv_exit_status()
            except Exception as e:
                # Fallback to heredoc if streaming fails
                try:
                    content = data.decode('utf-8', errors='ignore')
                    heredoc_cmd = f"cat > {remote_path} << 'NP_EOF'\n{content}\nNP_EOF"
                    out, err = self.execute(heredoc_cmd)
                    if err:
                        return False, f"Inline copy failed: {err}"
                except Exception as e2:
                    return False, f"Both streaming and heredoc copy failed: {e} / {e2}"

            # Normalize CR remotely and chmod
            if normalize_crlf:
                self.execute(f"sed -i 's/\\r$//' {remote_path} 2>/dev/null || true")
            if make_executable:
                self.execute(f"chmod +x {remote_path} 2>/dev/null || true")

            # Verify size
            out, err = self.execute(f"[ -s {remote_path} ] && echo ok || echo missing")
            if err or (out or '').strip() != 'ok':
                return False, "Remote file missing or empty after inline copy"
            return True, None

        try:
            sftp = conn.client.open_sftp()
        except Exception as e:
            # Fallback when SFTP subsystem is unavailable (e.g., Dropbear without sftp-server)
            return _fallback_inline_copy()

        # Ensure remote parent directory exists
        try:
            # Recursively create directories
            parts = [p for p in parent.split('/') if p]
            cur = '/' if parent.startswith('/') else ''
            for p in parts:
                cur = f"{cur}/{p}" if cur else p
                try:
                    sftp.stat(cur)
                except Exception:
                    try:
                        sftp.mkdir(cur)
                    except Exception:
                        pass
        except Exception:
            # Fallback to remote mkdir
            self.execute(f"mkdir -p {parent}")

        # Upload the file
        try:
            sftp.put(local_path, remote_path)
        except Exception as e:
            try:
                sftp.close()
            except Exception:
                pass
            # Fallback to inline copy if SFTP put fails
            return _fallback_inline_copy()

        # Optionally normalize CRLF on router (sed -i)
        if normalize_crlf:
            self.execute(f"sed -i 's/\\r$//' {remote_path} 2>/dev/null || true")

        # Optionally chmod +x
        if make_executable:
            self.execute(f"chmod +x {remote_path} 2>/dev/null || true")

        # Verify size > 0
        try:
            st = sftp.stat(remote_path)
            sftp.close()
            if st.st_size <= 0:
                return False, "Remote file is empty after upload"
        except Exception as e:
            try:
                sftp.close()
            except Exception:
                pass
            return False, f"SFTP stat failed: {e}"

        return True, None

    def _get_current_connection(self) -> Optional['_RouterConnection']:
        """Helper to get the connection for the current request context."""
        session_id = g.get("session_id")
        router_id = g.get("router_id")
        if not session_id or not router_id:
            return None
        
        with self._lock:
            # This assumes the connection exists, created by a previous execute call
            return self._sessions.get(session_id, {}).get(router_id)

    # ------------------------ helpers --------------------------
    def _get_or_create_connection(self, session_id: str, router_id: str) -> _RouterConnection:
        with self._lock:
            # First, ensure the session is active
            if not self.get_session_status(session_id):
                raise RuntimeError(f"Session {session_id} is not active or has expired.")

            session = self._sessions.setdefault(session_id, {})
            if router_id in session:
                conn = session[router_id]
                if conn.is_active():
                    return conn
                else:
                    conn.close()
                    del session[router_id]

        # Need to create a new one
        alloc = self._pm_client.get_allocation(router_id)
        if not alloc:
            raise RuntimeError(f"Router {router_id} not found in Port-Manager")
        tunnel_port = alloc.get("port")
        username = alloc.get("routerUsername") or alloc.get("router_username")
        password = alloc.get("routerPassword") or alloc.get("router_password")
        if not (tunnel_port and username and password):
            raise RuntimeError("Incomplete allocation info from Port-Manager")

        client = self._create_paramiko_client(tunnel_port, username, password)
        conn = _RouterConnection(client, tunnel_port)
        with self._lock:
            self._sessions.setdefault(session_id, {})[router_id] = conn
        
        return conn

    @staticmethod
    def _create_paramiko_client(tunnel_port: int, username: str, password: str) -> paramiko.SSHClient:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname="127.0.0.1",
            port=tunnel_port,
            username=username,
            password=password,
            timeout=int(os.getenv("SSH_CONNECT_TIMEOUT", 10)),
        )
        return ssh

    # -------------------- cleanup thread -----------------------
    def _cleanup_loop(self):
        while not self._stop_event.is_set():
            time.sleep(30)  # run every 30s
            now = datetime.utcnow()
            with self._lock:
                # --- Session Cleanup ---
                sessions_to_delete = []
                for session_id, last_active in list(self._active_sessions.items()):
                    if (now - last_active).total_seconds() > self._session_idle:
                        sessions_to_delete.append(session_id)
                
                for sid in sessions_to_delete:
                    self.end_session(sid) # Use end_session to ensure proper cleanup

                # --- Connection Cleanup ---
                for session_id, routers in list(self._sessions.items()):
                    routers_to_delete = []
                    for router_id, conn in list(routers.items()):
                        if (now - conn.last_used).total_seconds() > self._connection_idle:
                            conn.close()
                            routers_to_delete.append(router_id)
                    
                    for router_id in routers_to_delete:
                        routers.pop(router_id, None)
                    
                    # Update session's last active time if it's still alive
                    if routers:
                        latest_activity = max(c.last_used for c in routers.values())
                        self._active_sessions[session_id] = latest_activity

    # ---------------------- shutdown ---------------------------
    def shutdown(self):
        self._stop_event.set()
        self._janitor.join(timeout=2)
        with self._lock:
            for routers in self._sessions.values():
                for conn in routers.values():
                    conn.close()
            self._sessions.clear() 