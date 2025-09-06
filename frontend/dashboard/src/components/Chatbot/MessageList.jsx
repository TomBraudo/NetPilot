import React from 'react';
import { User, Bot, AlertCircle, Trash2 } from 'lucide-react';
import { useChatbot } from '../../context/ChatbotContext';

const MessageList = () => {
  const { messages, messagesEndRef, clearHistory } = useChatbot();

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting for better readability
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded text-sm">$1</code>')
      .replace(/\n/g, '<br>');
  };

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <Bot className="w-12 h-12 text-gray-400 dark:text-gray-600 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Welcome to NetPilot Assistant
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4 max-w-sm">
          I'm here to help you navigate and use NetPilot. Ask me about features, how to use the app, or get help with any questions you have.
        </p>
        <div className="text-sm text-gray-400 dark:text-gray-500">
          <p className="mb-1">Try asking:</p>
          <p className="mb-1">• "How do I create a group?"</p>
          <p className="mb-1">• "Where can I block devices?"</p>
          <p>• "How do I set up parental controls?"</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`flex gap-3 ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.role === 'assistant' && (
            <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              {message.isError ? (
                <AlertCircle className="w-4 h-4 text-white" />
              ) : (
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>
          )}
          
          <div
            className={`max-w-[80%] rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : message.isError
                ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
            }`}
          >
            <div
              className="text-sm leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: formatMessage(message.content)
              }}
            />
            
            <div className={`text-xs mt-2 ${
              message.role === 'user' 
                ? 'text-blue-100' 
                : message.isError
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-500 dark:text-gray-400'
            }`}>
              {formatTime(message.timestamp)}
              {message.model && (
                <span className="ml-2 opacity-75">
                  via {message.model.split('/')[1]}
                </span>
              )}
            </div>
          </div>
          
          {message.role === 'user' && (
            <div className="flex-shrink-0 w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
          )}
        </div>
      ))}
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
