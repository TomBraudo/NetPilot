import uuid
from managers.commands_server_manager import commands_server_manager

def start_session(router_id, session_id=None, restart=False):
    """
    Start a new session for the given router using the command server client.
    Args:
        router_id (str): The router's unique ID
        session_id (str, optional): The session ID to use, or None to generate one
        restart (bool): Whether to restart the session if it exists
    Returns:
        tuple: (result, error) where result is the session info or None, error is error message or None
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    payload = {
        "routerId": router_id,
        "sessionId": session_id,
        "restart": restart
    }
    response, error = commands_server_manager.execute_router_command(
        router_id=router_id,
        session_id=session_id,
        endpoint="/session/start",
        method="POST",
        body=payload
    )
    if error is None and response and response.get("session_id"):
        return {
            "sessionId": response["session_id"],
            "routerReachable": response.get("router_reachable"),
            "infrastructureReady": response.get("infrastructure_ready"),
            "message": response.get("message")
        }, None
    else:
        return None, error or (response.get("error") if response else "Session start failed") 