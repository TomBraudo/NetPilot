from flask import Blueprint, request, g
from utils.response_helpers import build_success_response, build_error_response
from utils.logging_config import get_logger
from utils.middleware import router_context_required
from services.chatbot_service import (
    get_chatbot_completion,
    clear_conversation_history,
    get_conversation_history
)
import time

chatbot_bp = Blueprint('chatbot', __name__)
logger = get_logger('endpoints.chatbot')


@chatbot_bp.route('/message', methods=['POST'])
@router_context_required
def send_message():
    """Send a message to the chatbot and get a response"""
    start_time = time.time()
    data = request.get_json() or {}
    
    # Validate required fields
    message = data.get('message', '').strip()
    if not message:
        return build_error_response("Message is required", 400, "INVALID_INPUT", start_time)
    
    # Validate message length
    if len(message) > 1000:
        return build_error_response("Message too long (max 1000 characters)", 400, "INVALID_INPUT", start_time)
    
    try:
        completion_data, error = get_chatbot_completion(g.user_id, g.router_id, g.session_id, message)
        if error:
            return build_error_response(f"Failed to get chatbot response: {error}", 500, "CHATBOT_ERROR", start_time)
        
        return build_success_response(completion_data, start_time)
    except Exception as e:
        logger.error(f"Failed to process chatbot message: {str(e)}")
        return build_error_response(f"Failed to process chatbot message: {str(e)}", 500, "CHATBOT_ERROR", start_time)


@chatbot_bp.route('/history', methods=['GET'])
@router_context_required
def get_history():
    """Get conversation history for the current user"""
    start_time = time.time()
    
    try:
        history, error = get_conversation_history(g.user_id, g.router_id, g.session_id)
        if error:
            return build_error_response(f"Failed to get conversation history: {error}", 500, "GET_HISTORY_FAILED", start_time)
        
        return build_success_response(history, start_time)
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        return build_error_response(f"Failed to get conversation history: {str(e)}", 500, "GET_HISTORY_FAILED", start_time)


@chatbot_bp.route('/history', methods=['DELETE'])
@router_context_required
def clear_history():
    """Clear conversation history for the current user"""
    start_time = time.time()
    
    try:
        success, error = clear_conversation_history(g.user_id, g.router_id, g.session_id)
        if error:
            return build_error_response(f"Failed to clear conversation history: {error}", 500, "CLEAR_HISTORY_FAILED", start_time)
        
        if not success:
            return build_error_response("Failed to clear conversation history", 500, "CLEAR_HISTORY_FAILED", start_time)
        
        return build_success_response({"message": "Conversation history cleared successfully"}, start_time)
    except Exception as e:
        logger.error(f"Failed to clear conversation history: {str(e)}")
        return build_error_response(f"Failed to clear conversation history: {str(e)}", 500, "CLEAR_HISTORY_FAILED", start_time)
