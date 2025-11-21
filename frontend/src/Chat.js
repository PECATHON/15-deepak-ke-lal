import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { IoSend, IoMic, IoStop, IoRefresh, IoSparkles } from 'react-icons/io5';
import ReactMarkdown from 'react-markdown';
import EnhancedMessageRenderer from './EnhancedMessageRenderer';
import './App.css';
import './EnhancedChat.css';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

// Typing indicator: single horizontal line with three animated dots
const TypingIndicator = React.forwardRef((props, ref) => (
  <motion.div
    ref={ref}
    className="message message-assistant"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
  >
    <div className="message-header">
      <span className="message-sender">🤖 ava</span>
    </div>
    <div className="message-content typing-indicator">
      <div className="typing-dots" aria-label="ava is thinking">
        {[0,1,2].map(i => (
          <motion.span
            key={i}
            className="typing-dot"
            initial={{ y: 0, opacity: 0.6 }}
            animate={{ y: [0, -6, 0], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.18 }}
          />
        ))}
      </div>
    </div>
  </motion.div>
));

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userId] = useState('user_' + Math.random().toString(36).substr(2, 9));
  const [status, setStatus] = useState({ state: 'idle' });
  const [isProcessing, setIsProcessing] = useState(false);
  const [partialResults, setPartialResults] = useState(null);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/${userId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message:', data);
        
        // Handle different message types
        if (data.type === 'response' && data.response) {
          // Agent response completed
          setMessages(prev => [...prev, {
            type: 'assistant', // logical type retained
            content: data.response,
            timestamp: new Date()
          }]);
          setIsProcessing(false);
          setPartialResults(null);
          setStatus({ state: 'completed' });
        }
        else if (data.type === 'status_update') {
          // Status update from backend
          setStatus({ state: data.status, agent: data.current_agent });
          if (data.partial_results) {
            setPartialResults(data.partial_results);
          }
        }
        else {
          // Legacy format support
          if (data.status) {
            setStatus({ state: data.status });
          }
          
          if (data.progress) {
            setPartialResults(data.progress);
          }
          
          if (data.status === 'completed' && data.response) {
            setMessages(prev => [...prev, {
              type: 'assistant', // logical type retained
              content: data.response,
              timestamp: new Date()
            }]);
            setIsProcessing(false);
            setPartialResults(null);
          }
          
          if (data.status === 'interrupted') {
            setMessages(prev => [...prev, {
              type: 'system',
              content: '⚠️ Task interrupted - partial results saved',
              timestamp: new Date()
            }]);
            setIsProcessing(false);
          }
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [userId]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsProcessing(true);
    setStatus({ state: 'processing' });
    setPartialResults(null);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        user_id: userId,
        message: currentInput
      });

      // If response is immediate (no WebSocket update), add it
      if (response.data.response && response.data.status === 'completed') {
        setMessages(prev => [...prev, {
          type: 'assistant', // logical type retained
          content: response.data.response,
          timestamp: new Date()
        }]);
        setIsProcessing(false);
      }
      
      // WebSocket will handle async updates

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
                    Chat & Go (ava)
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
                      { icon: "✈️", text: "Find round-trip flights from Delhi to Dubai departing Jan 15 returning Jan 20" },
                      { icon: "🏨", text: "Show me hotels in Paris with prices and images" },
                      { icon: "🎫", text: "Book flight FL001 for John Doe with window seat" },
                      { icon: "⚙️", text: "Update my preferences: Business class, 5-star hotels, budget 15000" }
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
                       msg.type === 'assistant' ? 'ava' :
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
                    <EnhancedMessageRenderer content={msg.content} />
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
                <motion.textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about flights, hotels, or travel plans..."
                  disabled={isProcessing}
                  rows="1"
                  className="chat-input"
                  initial={{ scale: 0.98 }}
                  whileFocus={{ scale: 1 }}
                  transition={{ duration: 0.2 }}
                />
                <div className="input-actions">
                  <motion.button
                    onClick={sendMessage}
                    disabled={!input.trim() || isProcessing}
                    className="send-button"
                    title="Send message"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {isProcessing ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <IoRefresh size={18} />
                      </motion.div>
                    ) : (
                      <IoSend size={18} />
                    )}
                  </motion.button>
                </div>
              </div>
              
              <div className="input-footer">
                <AnimatePresence>
                  {isProcessing && (
                    <motion.button
                      onClick={interruptTask}
                      className="interrupt-button"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <IoStop size={14} />
                      Stop Generation
                    </motion.button>
                  )}
                </AnimatePresence>
                
                <motion.div
                  className="status-indicator"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: status.state === 'idle' ? 0 : 1 }}
                >
                  <motion.div
                    className="status-icon"
                    animate={{ rotate: status.state === 'thinking' || status.state === 'searching' ? 360 : 0 }}
                    transition={{
                      duration: 2,
                      repeat: status.state === 'thinking' || status.state === 'searching' ? Infinity : 0,
                      ease: "linear"
                    }}
                  >
                    <IoSparkles size={12} />
                  </motion.div>
                  <div className="status-content">
                    <div className="status-main">
                      <span className="status-text">
                        {status.state === 'idle' ? 'Ready' : 
                         status.state === 'processing' ? 'Processing your request...' :
                         status.state === 'thinking' ? 'Analyzing your query...' :
                         status.state === 'searching' ? 'Searching for results...' :
                         status.state === 'completed' ? 'Search completed!' :
                         status.state}
                      </span>
                    </div>
                    {status.agent && status.state !== 'idle' && (
                      <motion.div
                        className="agent-info"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className="agent-badge">
                          {status.agent}
                        </div>
                        <div className="agent-description">
                          {status.agent === 'Flight Search Agent' ? 'Finding the best flights for you' :
                           status.agent === 'Hotel Search Agent' ? 'Searching for accommodation options' :
                           status.agent === 'Multi-Service Agent' ? 'Searching flights and hotels' :
                           status.agent === 'Booking Agent' ? 'Processing your booking request' :
                           status.agent === 'Travel Assistant AI' ? 'Understanding your travel needs' :
                           status.agent === 'ReAct Agent' ? 'Planning your travel itinerary' :
                           'Working on your request'}
                        </div>
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default Chat;
