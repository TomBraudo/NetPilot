import React from 'react';
import { MessageCircle, X } from 'lucide-react';
import { useChatbot } from '../../context/ChatbotContext';

const ChatBubble = () => {
  const { isOpen, toggleChat } = useChatbot();

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Chat Toggle Button */}
      <button
        onClick={toggleChat}
        className={`
          relative w-14 h-14 rounded-full shadow-lg transition-all duration-300 ease-in-out
          flex items-center justify-center text-white
          ${isOpen 
            ? 'bg-red-500 hover:bg-red-600 scale-110' 
            : 'bg-blue-500 hover:bg-blue-600 hover:scale-110'
          }
          transform hover:shadow-xl
        `}
        title={isOpen ? 'Close Chat' : 'Open Chat'}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageCircle className="w-6 h-6" />
        )}
      </button>
    </div>
  );
};

export default ChatBubble;
