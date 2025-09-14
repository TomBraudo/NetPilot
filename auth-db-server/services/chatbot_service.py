"""
Chatbot Service - AI Chat Integration

Handles chatbot interactions using OpenRouter API with DeepSeek model.
Fetches system prompt from GCP bucket and manages conversation history.
"""

import os
import requests
import json
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app
from utils.logging_config import get_logger
from .base import handle_service_errors, log_service_operation

logger = get_logger('services.chatbot_service')

# In-memory conversation storage (in production, consider using Redis or database)
conversation_history: Dict[str, List[Dict]] = {}

# Cache for system prompt to avoid repeated GCP bucket calls
_system_prompt_cache: Optional[str] = None
_cache_timestamp: Optional[float] = None
CACHE_DURATION = 300  # 5 minutes


def _fetch_system_prompt() -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch system prompt from GCP bucket with caching.
    
    Returns:
        Tuple of (system_prompt, error_message)
    """
    global _system_prompt_cache, _cache_timestamp
    
    import time
    current_time = time.time()
    
    # Return cached prompt if still valid
    if (_system_prompt_cache and _cache_timestamp and 
        current_time - _cache_timestamp < CACHE_DURATION):
        return _system_prompt_cache, None
    
    try:
        prompt_url = current_app.config.get('CHATBOT_SYSTEM_PROMPT_URL')
        if not prompt_url:
            return None, "CHATBOT_SYSTEM_PROMPT_URL not configured"
        
        logger.info(f"Fetching system prompt from: {prompt_url}")
        response = requests.get(prompt_url, timeout=10)
        response.raise_for_status()
        
        system_prompt = response.text.strip()
        if not system_prompt:
            return None, "System prompt is empty"
        
        # Update cache
        _system_prompt_cache = system_prompt
        _cache_timestamp = current_time
        
        logger.info("System prompt fetched and cached successfully")
        return system_prompt, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch system prompt: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching system prompt: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def _get_conversation_history(user_id: str, max_messages: int = 10) -> List[Dict]:
    """
    Get conversation history for user with message limit.
    
    Args:
        user_id: User's UUID
        max_messages: Maximum number of recent messages to return
        
    Returns:
        List of conversation messages
    """
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Return only the most recent messages
    return conversation_history[user_id][-max_messages:]


def _add_to_conversation_history(user_id: str, role: str, content: str) -> None:
    """
    Add message to conversation history.
    
    Args:
        user_id: User's UUID
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    conversation_history[user_id].append({
        "role": role,
        "content": content
    })
    
    # Keep only last 20 messages to prevent memory issues
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]


@handle_service_errors("Get chatbot completion")
def get_chatbot_completion(user_id: str, router_id: str, session_id: str, 
                          user_message: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get chatbot completion for user message.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        user_message: User's message
        
    Returns:
        Tuple of (completion_data, error_message)
    """
    log_service_operation("chatbot_completion", user_id, router_id, session_id, 
                         {"user_message_length": len(user_message)})
    
    try:
        # Validate input
        if not user_message or not user_message.strip():
            return None, "User message cannot be empty"
        
        # Fetch system prompt
        system_prompt, error = _fetch_system_prompt()
        if error:
            return None, f"Failed to fetch system prompt: {error}"
        
        # Get conversation history
        history = _get_conversation_history(user_id)
        
        # Prepare messages for OpenRouter API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message.strip()})
        
        # Prepare API request
        api_key = current_app.config.get('CHATBOT_KEY')
        if not api_key:
            return None, "CHATBOT_KEY not configured"
        
        model = current_app.config.get('CHATBOT_MODEL')
        api_url = current_app.config.get('OPENROUTER_API_URL')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': current_app.config.get('FRONTEND_URL', ''),  # Optional: for OpenRouter tracking
            'X-Title': 'NetPilot Chatbot'  # Optional: for OpenRouter tracking
        }
        
        payload = {
            'model': model,
            'messages': messages,
            'max_tokens': 1000,
            'temperature': 0.7,
            'stream': False
        }
        
        logger.info(f"Sending request to OpenRouter API: {model}")
        
        # Make API request
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract completion
        if 'choices' not in result or not result['choices']:
            return None, "No completion returned from API"
        
        completion = result['choices'][0]
        if 'message' not in completion:
            return None, "Invalid completion format from API"
        
        assistant_message = completion['message']['content']
        
        # Add messages to conversation history
        _add_to_conversation_history(user_id, "user", user_message.strip())
        _add_to_conversation_history(user_id, "assistant", assistant_message)
        
        # Prepare response data
        completion_data = {
            'message': assistant_message,
            'model': model,
            'usage': result.get('usage', {}),
            'conversation_length': len(conversation_history[user_id])
        }
        
        logger.info(f"Chatbot completion successful for user {user_id}")
        return completion_data, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"OpenRouter API request failed: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON response from OpenRouter API: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error in chatbot completion: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


@handle_service_errors("Clear conversation history")
def clear_conversation_history(user_id: str, router_id: str, session_id: str) -> Tuple[bool, Optional[str]]:
    """
    Clear conversation history for user.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (success, error_message)
    """
    log_service_operation("chatbot_clear_history", user_id, router_id, session_id)
    
    try:
        if user_id in conversation_history:
            del conversation_history[user_id]
            logger.info(f"Conversation history cleared for user {user_id}")
        return True, None
    except Exception as e:
        error_msg = f"Failed to clear conversation history: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


@handle_service_errors("Get conversation history")
def get_conversation_history(user_id: str, router_id: str, session_id: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Get conversation history for user.
    
    Args:
        user_id: User's UUID
        router_id: Router's UUID
        session_id: Session's UUID
        
    Returns:
        Tuple of (conversation_history, error_message)
    """
    log_service_operation("chatbot_get_history", user_id, router_id, session_id)
    
    try:
        history = _get_conversation_history(user_id)
        return history, None
    except Exception as e:
        error_msg = f"Failed to get conversation history: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
