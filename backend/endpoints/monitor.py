from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.monitor_service import (
    get_current_device_usage,
    get_last_week_device_usage,
    get_last_month_device_usage,
    get_device_usage_by_mac
)
import time

monitor_bp = Blueprint('monitor', __name__)
logger = get_logger('endpoints.monitor')

@monitor_bp.route("/current", methods=["GET"])
def get_current_usage():
    """Get current device usage"""
    start_time = time.time()
    result, error = get_current_device_usage()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@monitor_bp.route("/last-week", methods=["GET"])
def get_last_week_usage():
    """Get device usage for the last week"""
    start_time = time.time()
    result, error = get_last_week_device_usage()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@monitor_bp.route("/last-month", methods=["GET"])
def get_last_month_usage():
    """Get device usage for the last month"""
    start_time = time.time()
    result, error = get_last_month_device_usage()
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)

@monitor_bp.route("/device/<mac>", methods=["GET"])
def get_device_usage(mac):
    """Get device usage by MAC address"""
    start_time = time.time()
    period = request.args.get('period', 'current')
    result, error = get_device_usage_by_mac(mac, period)
    if error:
        return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
    return build_success_response(result, start_time)