import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userId] = useState('user_' + Math.random().toString(36).substr(2, 9));
  const [taskId, setTaskId] = useState(null);
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

      setTaskId(response.data.task_id);
      
      // Add processing message
      setMessages(prev => [...prev, {
        type: 'system',
        content: '🔄 Processing your request...',
        timestamp: new Date()
      }]);

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

  const getStatusColor = () => {
    switch (status.state) {
      case 'processing': return '#3b82f6';
      case 'completed': return '#10b981';
      case 'interrupted': return '#ef4444';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusText = () => {
    if (status.state === 'processing') {
      return `Processing${status.node ? ` - ${status.node}` : ''}...`;
    }
    return status.state || 'Ready';
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <div className="header-content">
            <h1>🌍 AI Travel Assistant</h1>
            <p className="subtitle">Multi-Agent Travel Planning with LangGraph</p>
          </div>
          <div className="status-bar" style={{ borderLeftColor: getStatusColor() }}>
            <div className="status-info">
              <span className="status-label">Status:</span>
              <span className="status-value">{getStatusText()}</span>
            </div>
            {taskId && (
              <div className="task-info">
                <span className="task-label">Task ID:</span>
                <span className="task-value">{taskId.substring(0, 8)}...</span>
              </div>
            )}
          </div>
        </header>

        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <h2>👋 Welcome to AI Travel Assistant!</h2>
                <p>I can help you search for flights and hotels. Try asking:</p>
                <div className="examples">
                  <div className="example">💺 "Find flights from NYC to LAX"</div>
                  <div className="example">🏨 "Show me hotels in Paris"</div>
                  <div className="example">✈️ "I need flights and hotels for Miami"</div>
                </div>
                <div className="features">
                  <h3>Features:</h3>
                  <ul>
                    <li>🤖 Multi-agent system (Flight & Hotel agents)</li>
                    <li>⚡ Real-time status updates</li>
                    <li>🛑 Interrupt long-running searches</li>
                    <li>💾 Partial result preservation</li>
                  </ul>
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`message message-${msg.type}`}>
                <div className="message-header">
                  <span className="message-sender">
                    {msg.type === 'user' ? '👤 You' : 
                     msg.type === 'assistant' ? '🤖 Assistant' :
                     msg.type === 'system' ? '⚙️ System' : '❌ Error'}
                  </span>
                  <span className="message-time">
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="message-content">
                  {msg.content}
                </div>
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about flights, hotels, or travel plans..."
              disabled={isProcessing}
              rows="2"
            />
            <div className="button-group">
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isProcessing}
                className="send-button"
              >
                {isProcessing ? '⏳ Processing...' : '📤 Send'}
              </button>
              {isProcessing && (
                <button
                  onClick={interruptTask}
                  className="interrupt-button"
                >
                  🛑 Interrupt
                </button>
              )}
            </div>
          </div>
        </div>

        <footer className="footer">
          <div className="footer-content">
            <div className="agent-status">
              <div className="agent-card">
                <span className="agent-icon">✈️</span>
                <span className="agent-name">Flight Agent</span>
                <span className={`agent-indicator ${status.node === 'flight_node' ? 'active' : ''}`}></span>
              </div>
              <div className="agent-card">
                <span className="agent-icon">🏨</span>
                <span className="agent-name">Hotel Agent</span>
                <span className={`agent-indicator ${status.node === 'hotel_node' ? 'active' : ''}`}></span>
              </div>
              <div className="agent-card">
                <span className="agent-icon">🎯</span>
                <span className="agent-name">Coordinator</span>
                <span className={`agent-indicator ${status.node === 'router' ? 'active' : ''}`}></span>
              </div>
            </div>
            <div className="tech-stack">
              Powered by LangGraph • FastAPI • React
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
