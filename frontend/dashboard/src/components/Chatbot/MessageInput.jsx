import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useChatbot } from '../../context/ChatbotContext';

const MessageInput = () => {
  const { sendMessage, isLoading, isTyping } = useChatbot();
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const messageToSend = message.trim();
    setMessage('');
    await sendMessage(messageToSend);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 p-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isTyping ? "Neti is typing..." : "Type your message..."}
            disabled={isLoading || isTyping}
            className="
              w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-600 
              rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500
              bg-white dark:bg-gray-800 text-gray-900 dark:text-white
              placeholder-gray-500 dark:placeholder-gray-400
              disabled:opacity-50 disabled:cursor-not-allowed
              max-h-32 min-h-[48px] overflow-hidden no-scrollbar
            "
            rows={1}
            maxLength={1000}
          />
          <div className="absolute right-2 bottom-2 text-xs text-gray-400">
            {message.length}/1000
          </div>
        </div>
        
        <button
          type="submit"
          disabled={!message.trim() || isLoading || isTyping}
          className="
            px-4 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 
            text-white rounded-lg transition-colors duration-200
            disabled:cursor-not-allowed flex items-center justify-center
            min-w-[48px]
          "
          title="Send message"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>
      
      {isTyping && (
        <div className="mt-2 text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
          <span>Neti is typing...</span>
        </div>
      )}
    </div>
  );
};

export default MessageInput;
