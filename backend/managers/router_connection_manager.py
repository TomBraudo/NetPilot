import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import os
import paramiko
import requests

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

        # Config
        base_url = os.getenv("PORT_MANAGER_URL", "http://localhost:3001")
        self._pm_client = PortManagerClient(base_url)
        self._connection_idle = int(os.getenv("CONNECTION_TIMEOUT_MINUTES", 5)) * 60
        self._session_idle = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30)) * 60

        # Start janitor thread
        self._stop_event = threading.Event()
        self._janitor = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._janitor.start()

    # ------------------------ public API -----------------------
    def execute(self, session_id: str, router_id: str, command: str, timeout: int = 30) -> Tuple[str, str]:
        conn = self._get_or_create_connection(session_id, router_id)
        try:
            return conn.exec_command(command, timeout=timeout)
        except Exception:
            # Mark connection dead and retry once
            conn.close()
            with self._lock:
                self._sessions.get(session_id, {}).pop(router_id, None)
            conn = self._get_or_create_connection(session_id, router_id)
            return conn.exec_command(command, timeout=timeout)

    # ------------------------ helpers --------------------------
    def _get_or_create_connection(self, session_id: str, router_id: str) -> _RouterConnection:
        with self._lock:
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
                sessions_to_delete = []
                for session_id, routers in list(self._sessions.items()):
                    routers_to_delete = []
                    for router_id, conn in list(routers.items()):
                        if (now - conn.last_used).total_seconds() > self._connection_idle:
                            conn.close()
                            routers_to_delete.append(router_id)
                    for router_id in routers_to_delete:
                        routers.pop(router_id, None)
                    # remove session if empty or idle
                    if not routers:
                        sessions_to_delete.append(session_id)
                        continue
                    # session idle check based on oldest last_used
                    oldest_last_used = max(r.last_used for r in routers.values())
                    if (now - oldest_last_used).total_seconds() > self._session_idle:
                        sessions_to_delete.append(session_id)
                for sid in sessions_to_delete:
                    for conn in self._sessions.get(sid, {}).values():
                        conn.close()
                    self._sessions.pop(sid, None)

    # ---------------------- shutdown ---------------------------
    def shutdown(self):
        self._stop_event.set()
        self._janitor.join(timeout=2)
        with self._lock:
            for routers in self._sessions.values():
                for conn in routers.values():
                    conn.close()
            self._sessions.clear() 