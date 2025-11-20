import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

const API_BASE = 'http://localhost:8000';

// Typing indicator component with animations
const TypingIndicator = () => (
  <motion.div 
    className="message message-assistant"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
  >
    <div className="message-header">
      <span className="message-sender">🤖 Assistant</span>
    </div>
    <div className="message-content typing-indicator">
      <motion.span
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
      />
      <motion.span
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
      />
      <motion.span
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
      />
    </div>
  </motion.div>
);

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userId] = useState('user_' + Math.random().toString(36).substr(2, 9));
  const [status, setStatus] = useState({ state: 'idle' });
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Poll status when processing
  useEffect(() => {
    let interval;
    if (isProcessing) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API_BASE}/status/${userId}`);
          setStatus(response.data);
          
          // If completed or error, stop processing
          if (response.data.state === 'completed' || response.data.state === 'error') {
            setIsProcessing(false);
            if (response.data.response) {
              setMessages(prev => [...prev, {
                type: 'assistant',
                content: response.data.response,
                timestamp: new Date()
              }]);
            }
          }
        } catch (error) {
          console.error('Status poll error:', error);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isProcessing, userId]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);
    setStatus({ state: 'processing' });

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        user_id: userId,
        message: input
      });

      // Task ID available in response.data.task_id if needed

    } catch (error) {
      console.error('Send message error:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date()
      }]);
      setIsProcessing(false);
    }
  };

  const interruptTask = async () => {
    if (!isProcessing) return;

    try {
      await axios.post(`${API_BASE}/interrupt`, { user_id: userId });
      
      setMessages(prev => [...prev, {
        type: 'system',
        content: '⚠️ Task interrupted by user',
        timestamp: new Date()
      }]);
      
      setIsProcessing(false);
      setStatus({ state: 'interrupted' });
    } catch (error) {
      console.error('Interrupt error:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleExampleClick = (exampleText) => {
    const cleanText = exampleText.replace(/^[^\s]+\s/, ''); // Remove emoji
    setInput(cleanText);
  };

  return (
    <div className="App">
      <div className="container">
        <div className="chat-container">
          <div className="messages">
            <AnimatePresence mode="popLayout">
              {messages.length === 0 && (
                <motion.div 
                  className="welcome-message"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.5 }}
                >
                  <motion.h2
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    AI Travel Assistant
                  </motion.h2>
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    I can help you search for flights and hotels. Try asking:
                  </motion.p>
                  <div className="examples">
                    {[
                      { icon: "💺", text: "Find flights from NYC to LAX" },
                      { icon: "🏨", text: "Show me hotels in Paris" },
                      { icon: "✈️", text: "I need flights and hotels for Miami" }
                    ].map((example, idx) => (
                      <motion.div
                        key={idx}
                        className="example"
                        onClick={() => handleExampleClick(`${example.icon} ${example.text}`)}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + idx * 0.1 }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {example.icon} {example.text}
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}

              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  className={`message message-${msg.type}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  layout
                >
                  <div className="message-header">
                    <motion.span 
                      className="message-sender"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.1 }}
                    >
                      {msg.type === 'user' ? 'You' : 
                       msg.type === 'assistant' ? 'Assistant' :
                       msg.type === 'system' ? 'System' : 'Error'}
                    </motion.span>
                    <span className="message-time">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <motion.div 
                    className="message-content"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.15 }}
                  >
                    {msg.content}
                  </motion.div>
                </motion.div>
              ))}

              {isProcessing && <TypingIndicator />}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>

          <motion.div 
            className="input-container"
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="input-area">
              <div className="input-wrapper">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Message..."
                  disabled={isProcessing}
                  rows="1"
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isProcessing}
                  className="send-button"
                  title="Send message"
                >
                  {isProcessing ? '⏳' : '↑'}
                </button>
              </div>
              <AnimatePresence>
                {isProcessing && (
                  <motion.button
                    onClick={interruptTask}
                    className="interrupt-button-small"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    Stop
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default Chat;
