import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyDevices } from '../services/api';
import EnergyChart from './EnergyChart';

function ClientDashboard() {
  const [devices, setDevices] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0,10));
  const [activeDevice, setActiveDevice] = useState(null);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const response = await getMyDevices();
      setDevices(response.data);
    } catch (err) {
      setError('Failed to load devices');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>My Devices</h1>
        <button onClick={handleLogout} style={{ padding: '10px 20px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '5px' }}>
          Logout
        </button>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table style={{ width: '100%', marginTop: '20px', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f8f9fa' }}>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>ID</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Name</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Max Consumption</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{device.id}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{device.name}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{device.max_consumption}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {devices.length === 0 && !error && <p style={{ marginTop: '20px' }}>No devices assigned to you.</p>}
      <input
        type="date"
        value={selectedDate}
        onChange={e => setSelectedDate(e.target.value)}
        style={{ marginTop: '20px', padding: '6px' }}
      />
      {devices.length > 0 && (
        <select
          value={activeDevice || ''}
          onChange={e => setActiveDevice(e.target.value)}
          style={{ marginLeft: '10px', padding: '6px' }}
        >
          <option value="">Select device</option>
          {devices.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      )}
      {activeDevice && <EnergyChart deviceId={activeDevice} date={selectedDate} />}
    </div>
  );
}

export default ClientDashboard;