from flask import g, jsonify
from datetime import datetime
import time

def build_success_response(data, execution_start_time):
    """Builds a standardized success response."""
    return jsonify({
        "success": True,
        "data": data,
        "error": None,
        "metadata": {
            "sessionId": g.get("session_id"),
            "routerId": g.get("router_id"),
            "timestamp": datetime.now().isoformat(),
            "executionTime": time.time() - execution_start_time
        }
    })

def build_error_response(message, status_code, error_code, execution_start_time):
    """Builds a standardized error response."""
    return jsonify({
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "details": None
        },
        "metadata": {
            "sessionId": g.get("session_id"),
            "routerId": g.get("router_id"),
            "timestamp": datetime.now().isoformat(),
            "executionTime": time.time() - execution_start_time
        }
    }), status_code
