import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import UserManagement from './UserManagement';
import DeviceManagement from './DeviceManagement';

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('users');
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Admin Dashboard</h1>
        <button onClick={handleLogout} style={{ padding: '10px 20px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '5px' }}>
          Logout
        </button>
      </div>
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('users')}
          style={{
            marginRight: '10px',
            padding: '10px 20px',
            background: activeTab === 'users' ? '#007bff' : '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '5px'
          }}
        >
          Manage Users
        </button>
        <button
          onClick={() => setActiveTab('devices')}
          style={{
            padding: '10px 20px',
            background: activeTab === 'devices' ? '#007bff' : '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '5px'
          }}
        >
          Manage Devices
        </button>
      </div>
      {activeTab === 'users' ? <UserManagement /> : <DeviceManagement />}
    </div>
  );
}

export default AdminDashboard;