# Chatbot Implementation Plan

## Overview
This document outlines the implementation plan for adding a chatbot feature to NetPilot that helps users navigate and use the app's features. The chatbot will use OpenRouter API with DeepSeek model and store the system prompt in a GCP bucket for security.

## Implementation Steps

### 1. Environment Configuration ✅ COMPLETED

#### 1.1 Backend2 Environment Setup ✅ COMPLETED
- Add `CHATBOT_KEY` to backend2/.env file (already exists)
- Add `CHATBOT_MODEL` to backend2/.env file (e.g., "deepseek/deepseek-chat-v3.1:free")
- Add `CHATBOT_SYSTEM_PROMPT_URL` to backend2/.env file (GCP bucket URL to txt file)
- Add `OPENROUTER_API_URL` to backend2/.env file (e.g., "https://openrouter.ai/api/v1")
- Update backend2/env.example with new environment variables

#### 1.2 Frontend Environment Setup ✅ COMPLETED
- Add `CHATBOT_API_URL` to frontend/dashboard/.env file (backend2 API endpoint)
- Update frontend/dashboard/env.example with new environment variables

### 2. System Prompt Storage in GCP ✅ COMPLETED

#### 2.1 GCP Bucket Setup ✅ COMPLETED
- Create a new GCP Storage bucket (e.g., "netpilot-chatbot-prompts")
- Set bucket permissions to allow public read access for the system prompt file
- Upload the system prompt as a plain text file (e.g., "system-prompt.txt")
- The text file contains the complete system prompt as a single string

#### 2.2 System Prompt Management ✅ COMPLETED
- When app features change, simply update the text file in the GCP bucket
- Update the `CHATBOT_SYSTEM_PROMPT_URL` in .env if the file name changes
- No versioning needed - just replace the file content
- Ensure the prompt is always accessible and up-to-date

### 3. Backend2 Service Implementation ✅ COMPLETED

#### 3.1 Chatbot Service Creation ✅ COMPLETED
- Create `backend2/services/chatbot_service.py`
- Implement OpenRouter API client with proper error handling
- Add conversation history management (in-memory or database)
- Implement rate limiting and request validation
- Add logging for chatbot interactions

#### 3.2 API Endpoint Implementation ✅ COMPLETED
- Create `backend2/endpoints/chatbot.py`
- Add `POST /api/chatbot/message` endpoint
- Implement request validation and response formatting
- Follow existing API envelope structure (success, data, error, metadata)
- Add authentication middleware integration

#### 3.3 System Prompt Integration ✅ COMPLETED
- Create function to fetch system prompt from GCP bucket URL
- Fetch the text file content directly from the URL
- Implement caching mechanism for system prompt (optional)
- Add fallback handling if prompt fetch fails
- No JSON parsing needed - use the text content directly

#### 3.4 Dependencies and Configuration ✅ COMPLETED
- Add required Python packages to backend2/requirements.txt
- Update backend2/server.py to include chatbot endpoints
- Add chatbot configuration to Flask app config
- Configure CORS for frontend integration
- Remove hardcoded values, use config system for all environment variables

### 4. Frontend Chatbot Implementation ✅ COMPLETED

#### 4.1 Chatbot Component Structure ✅ COMPLETED
- Create `frontend/dashboard/src/components/Chatbot/` directory
- Create main `Chatbot.jsx` component
- Create `ChatBubble.jsx` for the floating chat button
- Create `ChatWindow.jsx` for the popup chat interface
- Create `MessageList.jsx` for displaying conversation
- Create `MessageInput.jsx` for user input

#### 4.2 Chatbot State Management ✅ COMPLETED
- Create `frontend/dashboard/src/context/ChatbotContext.jsx`
- Implement conversation history state
- Add loading states for API calls
- Handle error states and retry logic
- Implement message persistence (localStorage)

#### 4.3 API Integration ✅ COMPLETED
- Create `frontend/dashboard/src/utils/chatbotApi.js`
- Implement API calls to backend2 chatbot endpoint
- Add proper error handling and user feedback
- Implement request/response logging for debugging

#### 4.4 UI/UX Implementation ✅ COMPLETED
- Design floating chat bubble with notification badge
- Create responsive popup chat window
- Implement smooth animations for open/close
- Add typing indicators and message status
- Design message bubbles for user and bot messages
- Add scroll-to-bottom functionality

#### 4.5 Global Integration ✅ COMPLETED
- Add chatbot to main App.jsx
- Ensure chatbot is available on all pages
- Add keyboard shortcuts (e.g., Ctrl+/ to open chat)
- Implement chat history persistence across page navigation
- Add accessibility features (ARIA labels, keyboard navigation)

### 5. Testing and Validation

#### 5.1 Backend Testing
- Test OpenRouter API integration with various prompts
- Validate system prompt fetching from GCP bucket URL
- Test error handling and fallback scenarios
- Verify API response formatting and structure
- Test rate limiting and concurrent requests

#### 5.2 Frontend Testing
- Test chatbot component rendering on all pages
- Validate API integration and error handling
- Test conversation history persistence
- Verify responsive design on different screen sizes
- Test accessibility features

#### 5.3 Integration Testing
- Test end-to-end chatbot functionality
- Validate system prompt effectiveness with real user queries
- Test chatbot responses for all app features
- Verify conversation context maintenance
- Test performance with multiple concurrent users

### 6. Deployment and Monitoring

#### 6.1 Backend Deployment
- Update backend2 deployment to include new environment variables
- Deploy chatbot service and endpoints
- Verify GCP bucket access from deployed backend
- Test chatbot functionality in production environment

#### 6.2 Frontend Deployment
- Build and deploy frontend with chatbot components
- Verify chatbot integration in production
- Test cross-browser compatibility
- Ensure mobile responsiveness

#### 6.3 Monitoring and Analytics
- Add logging for chatbot usage and performance
- Monitor API response times and error rates
- Track user engagement with chatbot
- Implement feedback collection for chatbot responses
- Set up alerts for chatbot service failures

### 7. Documentation and Maintenance

#### 7.1 User Documentation
- Create user guide for chatbot features
- Document common chatbot use cases
- Add FAQ section for chatbot-related questions
- Create troubleshooting guide

#### 7.2 Developer Documentation
- Document chatbot service architecture
- Create API documentation for chatbot endpoints
- Document system prompt update process
- Create maintenance procedures

#### 7.3 Ongoing Maintenance
- When app features change, update the system-prompt.txt file in GCP bucket
- Monitor chatbot performance and user feedback
- Update chatbot responses based on user interactions
- Maintain GCP bucket permissions and access

## Security Considerations

- Store API keys securely in environment variables
- Validate all user inputs before sending to OpenRouter API
- Implement rate limiting to prevent abuse
- Sanitize chatbot responses before displaying to users
- Ensure system prompt is not exposed in client-side code
- Use HTTPS for all API communications

## Performance Considerations

- Implement caching for system prompt to reduce GCP bucket calls
- Use conversation history limits to prevent memory issues
- Implement request debouncing for user input
- Optimize chatbot component rendering
- Consider implementing conversation summarization for long chats

## Future Enhancements

- Add conversation export functionality
- Implement chatbot analytics dashboard
- Add support for multiple languages
- Implement conversation search functionality
- Add chatbot response rating system
- Consider implementing conversation context persistence across sessions
