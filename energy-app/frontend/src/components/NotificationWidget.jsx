import React, { useEffect, useState, useRef } from 'react';

function NotificationWidget() {
  const [notifications, setNotifications] = useState([]);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const wsRef = useRef(null);
  const pingRef = useRef(null);
  const connectedRef = useRef(false);

  
  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === 'token') {
        setToken(e.newValue);
      }
    };

    
    const poll = setInterval(() => {
      const current = localStorage.getItem('token');
      setToken(prev => (prev === current ? prev : current));
    }, 1000);

    window.addEventListener('storage', onStorage);
    return () => {
      window.removeEventListener('storage', onStorage);
      clearInterval(poll);
    };
  }, []);

  useEffect(() => {
    
    connectedRef.current = false;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (pingRef.current) {
      clearInterval(pingRef.current);
      pingRef.current = null;
    }

    if (!token) return;

    
    if (!connectedRef.current) {
      connectedRef.current = true;
      connectWebSocket();
    }

    return () => {
      connectedRef.current = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (pingRef.current) {
        clearInterval(pingRef.current);
        pingRef.current = null;
      }
    };
  }, [token]);

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsUrl = `ws://localhost:8006/ws/notifications?token=${token}`;
    const websocket = new WebSocket(wsUrl);
    wsRef.current = websocket;

    websocket.onopen = () => {
      console.log('Notifications WebSocket connected');
    };

    websocket.onmessage = (event) => {
      if (event.data === 'pong') return;
      
      const data = JSON.parse(event.data);
      if (data.type === 'overconsumption') {
        addNotification(data);
      }
    };

    websocket.onerror = (error) => {
      console.error('Notifications WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('Notifications WebSocket disconnected');
      connectedRef.current = false;
    };

   
    pingRef.current = setInterval(() => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send('ping');
      }
    }, 30000);
  };

  const addNotification = (data) => {
    
    const uniqueId = (typeof crypto !== 'undefined' && crypto.randomUUID)
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

    const notification = {
      id: uniqueId,
      ...data,
      timestamp: new Date()
    };

   
    setNotifications(prev => {
      const sig = `${data.device_id}-${data.hour_timestamp}-${data.total_kwh}`;
      const now = Date.now();
      const hasRecentDuplicate = prev.some(n => {
        const nSig = `${n.device_id}-${n.hour_timestamp}-${n.total_kwh}`;
        const nTs = n.timestamp instanceof Date ? n.timestamp.getTime() : new Date(n.timestamp).getTime();
        return nSig === sig && (now - nTs) < 2000;
      });
      if (hasRecentDuplicate) return prev;
      return [notification, ...prev].slice(0, 5); 
    });
    
   
    if (Notification.permission === 'granted') {
      new Notification('Overconsumption Alert!', {
        body: `Device ${data.device_id} exceeded limit: ${data.total_kwh.toFixed(2)} kWh / ${data.max_consumption.toFixed(2)} kWh`,
        icon: '/favicon.ico'
      });
    }
  };

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const requestNotificationPermission = () => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  };

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  if (notifications.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        width: '320px',
        zIndex: 2000,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}
    >
      {notifications.map((notif) => (
        <div
          key={notif.id}
          style={{
            background: '#dc3545',
            color: 'white',
            padding: '15px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            animation: 'slideIn 0.3s ease-out'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 'bold', marginBottom: '5px', fontSize: '16px' }}>
                ⚠️ Overconsumption Alert
              </div>
              <div style={{ fontSize: '14px', marginBottom: '8px' }}>
                <strong>Device:</strong> {notif.device_id}
              </div>
              <div style={{ fontSize: '13px', opacity: 0.9 }}>
                Consumption: <strong>{notif.total_kwh?.toFixed(2)} kWh</strong>
              </div>
              <div style={{ fontSize: '13px', opacity: 0.9 }}>
                Limit: <strong>{notif.max_consumption?.toFixed(2)} kWh</strong>
              </div>
              <div style={{ fontSize: '11px', marginTop: '5px', opacity: 0.7 }}>
                {notif.timestamp.toLocaleTimeString()}
              </div>
            </div>
            <button
              onClick={() => dismissNotification(notif.id)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'white',
                fontSize: '20px',
                cursor: 'pointer',
                padding: '0',
                marginLeft: '10px'
              }}
            >
              ×
            </button>
          </div>
        </div>
      ))}
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(400px);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
}

export default NotificationWidget;
