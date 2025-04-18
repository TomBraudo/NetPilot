from flask import Blueprint
from utils.response_helpers import success

health_bp = Blueprint('health', __name__)

''' 
    API endpoint for health checking.
    Returns a simple success message to confirm the server is running.
'''
@health_bp.route("/health", methods=["GET"])
def health():
    return success("Server is healthy")