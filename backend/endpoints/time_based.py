from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.time_based_service import (
    create_time_rules,
    delete_time_rules,
    add_devices_to_group,
    remove_devices_from_group,
    add_device_to_group,
    remove_device_from_group,
)
import time


time_based_bp = Blueprint('time_based', __name__)
logger = get_logger('endpoints.time_based')


def _days_list_to_cron(days):
    """Validate list[int|str] in range 0..6 and convert to comma-separated cron string."""
    if not isinstance(days, list) or not days:
        return None, "'activate_days'/'deactivate_days' must be a non-empty list of 0-6"
    normalized = []
    for d in days:
        try:
            val = int(str(d).strip())
        except Exception:
            return None, "Days must be integers 0-6"
        if val < 0 or val > 6:
            return None, "Days must be in range 0-6 (0=Sunday)"
        normalized.append(val)
    # unique, sorted
    uniq_sorted = sorted(set(normalized))
    return ",".join(str(v) for v in uniq_sorted), None


@time_based_bp.route("/<group_id>/rules", methods=["POST"])
def post_group_time_rules(group_id: str):
    start_time = time.time()
    try:
        data = request.get_json() or {}
        members = data.get("members") or []
        activate_days = data.get("activate_days")
        start_hour = data.get("start_hour")
        deactivate_days = data.get("deactivate_days")
        stop_hour = data.get("stop_hour")

        if activate_days is None or start_hour is None or deactivate_days is None or stop_hour is None:
            return build_error_response("Missing required fields: activate_days, start_hour, deactivate_days, stop_hour", 400, "BAD_REQUEST", start_time)
        if members and not isinstance(members, list):
            return build_error_response("'members' must be a list of MAC addresses", 400, "BAD_REQUEST", start_time)

        activate_days_cron, err = _days_list_to_cron(activate_days)
        if err:
            return build_error_response(err, 400, "BAD_REQUEST", start_time)
        deactivate_days_cron, err = _days_list_to_cron(deactivate_days)
        if err:
            return build_error_response(err, 400, "BAD_REQUEST", start_time)

        result, error = create_time_rules(
            group_id=group_id,
            members=members,
            activate_days=activate_days_cron,
            start_hour=start_hour,
            deactivate_days=deactivate_days_cron,
            stop_hour=stop_hour,
        )
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_group_time_rules: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@time_based_bp.route("/<group_id>/rules", methods=["DELETE"])
def delete_group_time_rules(group_id: str):
    start_time = time.time()
    try:
        result, error = delete_time_rules(group_id)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response({"deleted": bool(result)}, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_group_time_rules: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@time_based_bp.route("/<group_id>/devices", methods=["POST"])
def post_group_devices(group_id: str):
    start_time = time.time()
    try:
        data = request.get_json() or {}
        macs = data.get("macs") or []
        if not isinstance(macs, list) or not macs:
            return build_error_response("Missing or invalid 'macs' list", 400, "BAD_REQUEST", start_time)

        result, error = add_devices_to_group(group_id, macs)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_group_devices: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@time_based_bp.route("/<group_id>/devices", methods=["DELETE"])
def delete_group_devices(group_id: str):
    start_time = time.time()
    try:
        data = request.get_json() or {}
        macs = data.get("macs") or []
        if not isinstance(macs, list) or not macs:
            return build_error_response("Missing or invalid 'macs' list", 400, "BAD_REQUEST", start_time)

        result, error = remove_devices_from_group(group_id, macs)
        if error:
            return build_error_response(f"Command failed: {error}", 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_group_devices: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@time_based_bp.route("/<group_id>/devices/<mac>", methods=["POST"])
def post_group_device(group_id: str, mac: str):
    start_time = time.time()
    try:
        result, error = add_device_to_group(group_id, mac)
        if error:
            return build_error_response(f"Command failed: {error}", 400 if "Invalid" in (error or "") else 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in post_group_device: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)


@time_based_bp.route("/<group_id>/devices/<mac>", methods=["DELETE"])
def delete_group_device(group_id: str, mac: str):
    start_time = time.time()
    try:
        result, error = remove_device_from_group(group_id, mac)
        if error:
            return build_error_response(f"Command failed: {error}", 400 if "Invalid" in (error or "") else 500, "COMMAND_FAILED", start_time)
        return build_success_response(result, start_time)
    except Exception as e:
        logger.error(f"Unexpected error in delete_group_device: {e}", exc_info=True)
        return build_error_response(str(e), 500, "UNEXPECTED_SERVER_ERROR", start_time)



