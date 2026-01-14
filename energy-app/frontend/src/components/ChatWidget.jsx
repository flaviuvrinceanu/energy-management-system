import React, { useState, useEffect, useRef } from 'react';

function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !ws) {
      connectWebSocket();
    }
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [isOpen]);

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const wsUrl = `ws://localhost:8006/ws/chat?token=${token}`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('Chat WebSocket connected');
      setIsConnected(true);
      addSystemMessage('Connected to support chat');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'pong') return;
      
      if (data.type === 'bot_reply') {
        addBotMessage(data.message);
      } else if (data.type === 'admin_reply') {
        addAdminMessage(data.message);
      } else if (data.type === 'error') {
        addSystemMessage(`Error: ${data.message}`);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      addSystemMessage('Connection error');
      setIsConnected(false);
    };

    websocket.onclose = () => {
      console.log('Chat WebSocket disconnected');
      setIsConnected(false);
      addSystemMessage('Disconnected from chat');
    };

    setWs(websocket);
  };

  const addSystemMessage = (text) => {
    setMessages(prev => [...prev, { type: 'system', text, timestamp: new Date() }]);
  };

  const addBotMessage = (text) => {
    setMessages(prev => [...prev, { type: 'bot', text, timestamp: new Date() }]);
  };

  const addAdminMessage = (text) => {
    setMessages(prev => [...prev, { type: 'admin', text, timestamp: new Date() }]);
  };

  const addUserMessage = (text) => {
    setMessages(prev => [...prev, { type: 'user', text, timestamp: new Date() }]);
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !ws || !isConnected) return;

    const message = {
      message: inputMessage,
      timestamp: new Date().toISOString()
    };

    ws.send(JSON.stringify(message));
    addUserMessage(inputMessage);
    setInputMessage('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {}
      {!isOpen && (
        <button
          onClick={toggleChat}
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            background: '#007bff',
            color: 'white',
            border: 'none',
            fontSize: '24px',
            cursor: 'pointer',
            boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
            zIndex: 1000
          }}
        >
          💬
        </button>
      )}

      {}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '350px',
            height: '500px',
            background: 'white',
            borderRadius: '10px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000
          }}
        >
          {}
          <div
            style={{
              background: '#007bff',
              color: 'white',
              padding: '15px',
              borderRadius: '10px 10px 0 0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div>
              <h3 style={{ margin: 0 }}>Support Chat</h3>
              <small style={{ opacity: 0.8 }}>
                {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
              </small>
            </div>
            <button
              onClick={toggleChat}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'white',
                fontSize: '24px',
                cursor: 'pointer'
              }}
            >
              ×
            </button>
          </div>

          {}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '15px',
              background: '#f8f9fa'
            }}
          >
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: '10px',
                  display: 'flex',
                  justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div
                  style={{
                    maxWidth: '70%',
                    padding: '10px',
                    borderRadius: '10px',
                    background: msg.type === 'user' 
                      ? '#007bff' 
                      : msg.type === 'system' 
                      ? '#6c757d' 
                      : msg.type === 'admin'
                      ? '#28a745'
                      : '#e9ecef',
                    color: msg.type === 'user' || msg.type === 'system' || msg.type === 'admin'
                      ? 'white' 
                      : 'black'
                  }}
                >
                  {msg.type === 'admin' && (
                    <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>
                      Admin
                    </div>
                  )}
                  <div style={{ fontSize: '14px' }}>{msg.text}</div>
                  <div style={{ fontSize: '10px', marginTop: '5px', opacity: 0.7 }}>
                    {msg.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {}
          <div
            style={{
              padding: '15px',
              borderTop: '1px solid #dee2e6',
              background: 'white',
              borderRadius: '0 0 10px 10px'
            }}
          >
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type a message..."
                disabled={!isConnected}
                style={{
                  flex: 1,
                  padding: '10px',
                  border: '1px solid #dee2e6',
                  borderRadius: '5px',
                  fontSize: '14px'
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!isConnected || !inputMessage.trim()}
                style={{
                  padding: '10px 20px',
                  background: isConnected ? '#007bff' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: isConnected ? 'pointer' : 'not-allowed',
                  fontSize: '14px'
                }}
              >
                Send
              </button>
            </div>
            <div style={{ marginTop: '10px', fontSize: '12px', color: '#6c757d' }}>
              Try: "hello", "how do I add a device?", "what is overconsumption?"
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default ChatWidget;
