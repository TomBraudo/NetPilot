from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
import os
import time

logger = get_logger('endpoints.download')
download_bp = Blueprint('download', __name__)
@download_bp.route('', methods=['GET'])
def download():
    start_time = time.time()
    link = os.getenv('AGENT_DOWNLOAD_URL')
    if not link:
        return build_error_response('AGENT_DOWNLOAD_URL is not set', 500, 'AGENT_DOWNLOAD_URL_NOT_SET', start_time)
    return build_success_response(link, start_time)