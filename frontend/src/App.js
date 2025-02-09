import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('chat');
  const [status, setStatus] = useState('idle');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

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
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { type: 'agent', content: data.response }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Failed to get response from agent. Please ensure the server is running.' 
      }]);
    }

    setStatus('idle');
  };

  const toggleMode = async () => {
    const newMode = mode === 'chat' ? 'auto' : 'chat';
    setMode(newMode);
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
        throw new Error('Failed to switch mode');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { 
        type: 'system', 
        content: data.status 
      }]);
      setStatus(newMode === 'auto' ? 'running' : 'idle');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Failed to switch mode. Please try again.' 
      }]);
      setMode(mode); // Revert mode
      setStatus('idle');
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
              disabled={status === 'thinking'}
            >
              {mode === 'chat' ? 'Switch to Auto Mode' : 'Switch to Chat Mode'}
            </button>
            <span className={`status-indicator ${status}`}>
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
              placeholder="Type your message..."
              disabled={mode === 'auto' || status === 'thinking'}
            />
            <button 
              type="submit" 
              disabled={mode === 'auto' || status === 'thinking'}
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
