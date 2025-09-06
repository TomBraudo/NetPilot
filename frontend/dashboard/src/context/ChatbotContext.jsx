import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { chatbotAPI } from '../constants/api';

const ChatbotContext = createContext();

export const useChatbot = () => {
  const context = useContext(ChatbotContext);
  if (!context) {
    throw new Error('useChatbot must be used within a ChatbotProvider');
  }
  return context;
};

export const ChatbotProvider = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const routerId = localStorage.getItem("routerId");
      if (!routerId) {
        console.warn('No routerId found in localStorage');
        return;
      }
      
      const response = await chatbotAPI.getHistory(routerId);
      if (response.success && response.data) {
        // Convert backend format to frontend format
        const formattedMessages = response.data.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: new Date().toISOString() // Backend doesn't include timestamp
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  }, []);

  // Load conversation history on mount
  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = useCallback(async (message) => {
    if (!message.trim()) return;

    const routerId = localStorage.getItem("routerId");
    if (!routerId) {
      setError('No router ID found. Please refresh the page.');
      return;
    }

    const userMessage = {
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setIsTyping(true);

    try {
      const response = await chatbotAPI.sendMessage(routerId, message);
      
      if (response.success && response.data) {
        const assistantMessage = {
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date().toISOString(),
          model: response.data.model,
          usage: response.data.usage
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(response.error || 'Failed to get response from chatbot');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setError(error.message);
      
      // Add error message
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  }, []);

  const clearHistory = useCallback(async () => {
    try {
      const routerId = localStorage.getItem("routerId");
      if (!routerId) {
        setError('No router ID found. Please refresh the page.');
        return;
      }
      
      const response = await chatbotAPI.clearHistory(routerId);
      if (response.success) {
        setMessages([]);
        setError(null);
      } else {
        throw new Error(response.error || 'Failed to clear history');
      }
    } catch (error) {
      console.error('Failed to clear history:', error);
      setError(error.message);
    }
  }, []);

  const toggleChat = useCallback(() => {
    setIsOpen(prev => !prev);
    if (!isOpen) {
      setError(null);
    }
  }, [isOpen]);

  const closeChat = useCallback(() => {
    setIsOpen(false);
    setError(null);
  }, []);

  const value = {
    isOpen,
    messages,
    isLoading,
    error,
    isTyping,
    messagesEndRef,
    sendMessage,
    clearHistory,
    toggleChat,
    closeChat,
    loadHistory
  };

  return (
    <ChatbotContext.Provider value={value}>
      {children}
    </ChatbotContext.Provider>
  );
};
