import React, { useEffect } from 'react';
import { useChatbot } from '../../context/ChatbotContext';
import ChatBubble from './ChatBubble';
import ChatWindow from './ChatWindow';

const Chatbot = () => {
  const { loadHistory } = useChatbot();

  // Load conversation history when component mounts
  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return (
    <>
      <ChatBubble />
      <ChatWindow />
    </>
  );
};

export default Chatbot;
