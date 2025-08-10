from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.nft_qos_service import (
    set_group_limits,
    remove_group_limits,
    set_device_limit,
    remove_device_limit,
    activate_global_limits,
    deactivate_global_limits,
    add_whitelist,
    remove_whitelist,
    convert_mbps_to_kbytes,
)
import time

bandwidth_bp = Blueprint('bandwidth', __name__)
logger = get_logger('endpoints.bandwidth')


@bandwidth_bp.route("/limits/group", methods=["POST"]) 
def post_group_limits():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        ips = data.get("ips") or []
        if not isinstance(ips, list) or not ips:
            return build_error_response("Missing or invalid 'ips' list", 400, "BAD_REQUEST", start_time)

        # Accept either kbytes or mbps (convert if mbps provided)
        dl_kbytes = data.get("download_kbytes")
        ul_kbytes = data.get("upload_kbytes")
        if dl_kbytes is None or ul_kbytes is None:
            dl_mbps = data.get("download_mbps")
            ul_mbps = data.get("upload_mbps")
            if dl_mbps is None or ul_mbps is None:
                return build_error_response("Missing limits: provide download_kbytes/upload_kbytes or download_mbps/upload_mbps", 400, "BAD_REQUEST", start_time)
            dl_kbytes = convert_mbps_to_kbytes(dl_mbps)
            ul_kbytes = convert_mbps_to_kbytes(ul_mbps)

        result, error = set_group_limits(ips, int(dl_kbytes), int(ul_kbytes))
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_group_limits: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/limits/group", methods=["DELETE"]) 
def delete_group_limits():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        ips = data.get("ips") or []
        if not isinstance(ips, list) or not ips:
            return build_error_response("Missing or invalid 'ips' list", 400, "BAD_REQUEST", start_time)

        result, error = remove_group_limits(ips)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_group_limits: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/limits/device", methods=["POST"]) 
def post_device_limit():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        ip = data.get("ip")
        if not ip:
            return build_error_response("Missing 'ip'", 400, "BAD_REQUEST", start_time)

        dl_kbytes = data.get("download_kbytes")
        ul_kbytes = data.get("upload_kbytes")
        if dl_kbytes is None or ul_kbytes is None:
            dl_mbps = data.get("download_mbps")
            ul_mbps = data.get("upload_mbps")
            if dl_mbps is None or ul_mbps is None:
                return build_error_response("Missing limits: provide download_kbytes/upload_kbytes or download_mbps/upload_mbps", 400, "BAD_REQUEST", start_time)
            dl_kbytes = convert_mbps_to_kbytes(dl_mbps)
            ul_kbytes = convert_mbps_to_kbytes(ul_mbps)

        result, error = set_device_limit(ip, int(dl_kbytes), int(ul_kbytes))
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_device_limit: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/limits/device", methods=["DELETE"]) 
def delete_device_limit():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        ip = data.get("ip")
        if not ip:
            return build_error_response("Missing 'ip'", 400, "BAD_REQUEST", start_time)

        result, error = remove_device_limit(ip)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_device_limit: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/global/activate", methods=["POST"]) 
def post_global_activate():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        dl_kbytes = data.get("download_kbytes")
        ul_kbytes = data.get("upload_kbytes")
        if dl_kbytes is None or ul_kbytes is None:
            return build_error_response("Missing 'download_kbytes'/'upload_kbytes'", 400, "BAD_REQUEST", start_time)
        lan_cidr = data.get("lan_cidr")

        result, error = activate_global_limits(int(dl_kbytes), int(ul_kbytes), lan_cidr)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_global_activate: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/global/deactivate", methods=["DELETE"]) 
def delete_global_deactivate():
    start_time = time.time()
    try:
        result, error = deactivate_global_limits()
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_global_deactivate: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/global/whitelist", methods=["POST"]) 
def post_global_whitelist():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        ips = data.get("ips") or []
        if not isinstance(ips, list) or not ips:
            return build_error_response("Missing or invalid 'ips' list", 400, "BAD_REQUEST", start_time)

        result, error = add_whitelist(ips)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_global_whitelist: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@bandwidth_bp.route("/global/whitelist", methods=["DELETE"]) 
def delete_global_whitelist():
    start_time = time.time()
    try:
        data = request.get_json() or {}
        ips = data.get("ips") or []
        if not isinstance(ips, list) or not ips:
            return build_error_response("Missing or invalid 'ips' list", 400, "BAD_REQUEST", start_time)

        result, error = remove_whitelist(ips)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_global_whitelist: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


