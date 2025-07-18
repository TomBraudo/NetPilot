import os
import requests
from flask import current_app


def get_command_server_config(app=None):
    """
    Retrieve Command Server URL and timeout from Flask app config or environment variables.
    """
    if app is None:
        try:
            app = current_app
        except RuntimeError:
            app = None
    url = None
    timeout = None
    if app:
        url = app.config.get('COMMAND_SERVER_URL')
        timeout = app.config.get('COMMAND_SERVER_TIMEOUT')
    if not url:
        url = os.getenv('COMMAND_SERVER_URL', 'http://34.38.207.87:5000')
    if not timeout:
        timeout = int(os.getenv('COMMAND_SERVER_TIMEOUT', 30))
    return url, timeout


def send_command_server_request(endpoint, method="GET", payload=None, app=None, use_api_prefix=True):
    """
    Proxy a request to the Command Server.
    Args:
        endpoint (str): Endpoint path, e.g. '/network/block'
        method (str): 'GET' or 'POST'
        payload (dict): Data to send (query params for GET, JSON for POST)
        app (Flask): Optional Flask app context
        use_api_prefix (bool): Whether to prepend '/api' to the endpoint
    Returns:
        dict: Parsed JSON response or error dict
    """
    url_base, timeout = get_command_server_config(app)
    if use_api_prefix:
        url = url_base.rstrip("/") + "/api" + "/" + endpoint.lstrip("/")
    else:
        url = url_base.rstrip("/") + "/" + endpoint.lstrip("/")
    try:
        if method.upper() == "GET":
            resp = requests.get(url, params=payload, timeout=timeout)
        else:
            resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            print("Command Server error status:", e.response.status_code)
            print("Command Server error response:", e.response.text)
        else:
            print("No response object in exception.")
        print(f"Command Server request error: {e}")
        return {"success": False, "error": str(e)}


def command_server_health_check(app=None):
    """
    Proxy a health check request to the Command Server.
    Returns:
        dict: Parsed JSON response or error dict
    """
    return send_command_server_request("/health", method="GET", payload=None, app=app, use_api_prefix=False) 