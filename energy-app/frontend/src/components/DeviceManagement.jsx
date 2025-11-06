import React, { useEffect, useState } from 'react';
import { getDevices, createDevice, deleteDevice, getUsers, assignDevice, createDeviceUser } from '../services/api';

function DeviceManagement() {
  const [devices, setDevices] = useState([]);
  const [users, setUsers] = useState([]);
  const [name, setName] = useState('');
  const [maxConsumption, setMaxConsumption] = useState('');
  const [selectedUser, setSelectedUser] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadDevices();
    loadUsers();
  }, []);

  const loadDevices = async () => {
    try {
      const response = await getDevices();
      setDevices(response.data);
    } catch (err) {
      setError('Failed to load devices');
    }
  };

  const loadUsers = async () => {
    try {
      const response = await getUsers();
      setUsers(response.data);
    } catch (err) {
      setError('Failed to load users');
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = {
        name,
        max_consumption: parseFloat(maxConsumption),
        device_user_id: selectedUser || null
      };
      
      if (selectedUser) {
        const user = users.find(u => u.id === selectedUser);
        if (user) {
          try {
            await createDeviceUser({ id: user.id, username: user.username, role: user.role });
          } catch (err) {
            // Device user might already exist
          }
        }
      }
      
      await createDevice(payload);
      setName('');
      setMaxConsumption('');
      setSelectedUser('');
      loadDevices();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create device');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this device?')) return;
    try {
      await deleteDevice(id);
      loadDevices();
    } catch (err) {
      setError('Failed to delete device');
    }
  };

  const handleAssign = async (deviceId, userId) => {
    try {
      const user = users.find(u => u.id === userId);
      if (user) {
        await createDeviceUser({ id: user.id, username: user.username, role: user.role });
      }
      await assignDevice(deviceId, userId);
      loadDevices();
    } catch (err) {
      setError('Failed to assign device');
    }
  };

  return (
    <div>
      <h2>Device Management</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleCreate} style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h3>Create Device</h3>
        <input
          type="text"
          placeholder="Device Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ marginRight: '10px', padding: '8px' }}
        />
        <input
          type="number"
          step="0.1"
          placeholder="Max Consumption"
          value={maxConsumption}
          onChange={(e) => setMaxConsumption(e.target.value)}
          required
          style={{ marginRight: '10px', padding: '8px' }}
        />
        <select value={selectedUser} onChange={(e) => setSelectedUser(e.target.value)} style={{ marginRight: '10px', padding: '8px' }}>
          <option value="">Unassigned</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.username} ({user.role})
            </option>
          ))}
        </select>
        <button type="submit" style={{ padding: '8px 20px', background: '#28a745', color: 'white', border: 'none', borderRadius: '5px' }}>
          Create
        </button>
      </form>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f8f9fa' }}>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>ID</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Name</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Max Consumption</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Assigned To</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{device.id}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{device.name}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{device.max_consumption}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>
                {device.device_user_id ? (
                  users.find(u => u.id === device.device_user_id)?.username || device.device_user_id
                ) : (
                  'Unassigned'
                )}
              </td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>
                <select
                  onChange={(e) => e.target.value && handleAssign(device.id, e.target.value)}
                  style={{ marginRight: '10px', padding: '5px' }}
                  defaultValue=""
                >
                  <option value="">Assign to...</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.username}
                    </option>
                  ))}
                </select>
                <button onClick={() => handleDelete(device.id)} style={{ padding: '5px 15px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '3px' }}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DeviceManagement;