import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('chat');
  const [status, setStatus] = useState('connecting');
  const [serverConnected, setServerConnected] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check server connection on mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await fetch('http://localhost:3001/status');
        if (response.ok) {
          const data = await response.json();
          setServerConnected(true);
          setStatus(data.mode === 'auto' ? 'running' : 'idle');
        } else {
          setServerConnected(false);
          setStatus('disconnected');
        }
      } catch (error) {
        setServerConnected(false);
        setStatus('disconnected');
      }
    };

    checkServer();
    const interval = setInterval(checkServer, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || !serverConnected) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setInput('');
    setStatus('thinking');

    try {
      const response = await fetch('http://localhost:3001/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to get response from agent');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { type: 'agent', content: data.response }]);
      setStatus('idle');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: error.message || 'Failed to get response from agent. Please ensure the server is running.' 
      }]);
      setStatus('error');
      setTimeout(() => setStatus(serverConnected ? 'idle' : 'disconnected'), 3000);
    }
  };

  const toggleMode = async () => {
    if (!serverConnected) return;

    const newMode = mode === 'chat' ? 'auto' : 'chat';
    setStatus('updating');

    try {
      const response = await fetch('http://localhost:3001/mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: newMode }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to switch mode');
      }

      const data = await response.json();
      setMode(newMode);
      setMessages(prev => [...prev, { 
        type: 'system', 
        content: data.status 
      }]);
      setStatus(newMode === 'auto' ? 'running' : 'idle');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: error.message || 'Failed to switch mode. Please try again.' 
      }]);
      setStatus('error');
      setTimeout(() => setStatus(serverConnected ? 'idle' : 'disconnected'), 3000);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'thinking': return '#ffd700';
      case 'running': return '#4caf50';
      case 'error': return '#f44336';
      case 'disconnected': return '#9e9e9e';
      default: return '#1a73e8';
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>AgentKit Interface</h1>
          <div className="mode-toggle">
            <button 
              onClick={toggleMode}
              className={`mode-button ${mode === 'auto' ? 'active' : ''}`}
              disabled={!serverConnected || status === 'thinking'}
            >
              {mode === 'chat' ? 'Switch to Auto Mode' : 'Switch to Chat Mode'}
            </button>
            <span 
              className={`status-indicator ${status}`}
              style={{ color: getStatusColor() }}
            >
              Status: {status}
            </span>
          </div>
        </header>

        <div className="chat-container">
          <div className="messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.type}`}>
                <span className="message-prefix">
                  {msg.type === 'user' ? 'You: ' : 
                   msg.type === 'agent' ? 'Agent: ' : 
                   msg.type === 'system' ? 'System: ' : ''}
                </span>
                {msg.content}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={serverConnected ? "Type your message..." : "Server disconnected..."}
              disabled={!serverConnected || mode === 'auto' || status === 'thinking'}
            />
            <button 
              type="submit" 
              disabled={!serverConnected || mode === 'auto' || status === 'thinking'}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
