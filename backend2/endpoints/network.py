from flask import Blueprint, request, g
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.network_service import scan_network
import time
from utils.middleware import router_context_required

network_bp = Blueprint('network', __name__)
logger = get_logger('endpoints.network')

@network_bp.route("/scan", methods=["GET"])
@router_context_required
def scan_router():
    """Scan the network via router to find connected devices"""
    start_time = time.time()
    
    result, error = scan_network(g.user_id, g.router_id, g.session_id)
    if error:
        return build_error_response(f"Network scan failed: {error}", 500, "NETWORK_SCAN_FAILED", start_time)
    return build_success_response(result, start_time) 