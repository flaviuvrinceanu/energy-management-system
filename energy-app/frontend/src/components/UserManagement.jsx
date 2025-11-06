import React, { useEffect, useState } from 'react';
import { getUsers, createUser, deleteUser, updateUser } from '../services/api';

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'client' });
  const [editingId, setEditingId] = useState(null);
  const [editUsername, setEditUsername] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await getUsers();
      console.log('Users response:', response.data); 
      
      setUsers(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch users';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      await createUser(newUser.username, newUser.password, newUser.role);
      setNewUser({ username: '', password: '', role: 'client' });
      await fetchUsers(); 
    } catch (err) {
      console.error('Create user error:', err.response?.data); 
      if (err.response?.data?.detail && Array.isArray(err.response.data.detail)) {
        const errors = err.response.data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
        setError(errors);
      } else {
        const errorMsg = err.response?.data?.detail || 'Failed to create user';
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    }
  };

  const handleEdit = (user) => {
    setEditingId(user.id);
    setEditUsername(user.username);
  };

  const handleUpdate = async (id) => {
    try {
      await updateUser(id, { username: editUsername });
      setEditingId(null);
      await fetchUsers();
    } catch (err) {
      setError('Failed to update user');
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditUsername('');
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this user?')) return;
    try {
      await deleteUser(id);
      await fetchUsers();
    } catch (err) {
      setError('Failed to delete user');
    }
  };

  return (
    <div>
      <h2>User Management</h2>
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{String(error)}</div>}
      
      <form onSubmit={handleCreateUser} style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h3>Create User</h3>
        <input
          type="text"
          placeholder="Username"
          value={newUser.username}
          onChange={(e) => setNewUser({...newUser, username: e.target.value})}
          required
          style={{ marginRight: '10px', padding: '8px' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={newUser.password}
          onChange={(e) => setNewUser({...newUser, password: e.target.value})}
          style={{ marginRight: '10px', padding: '8px' }}
        />
        <select
          value={newUser.role}
          onChange={(e) => setNewUser({...newUser, role: e.target.value})}
          style={{ marginRight: '10px', padding: '8px' }}
        >
          <option value="client">Client</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" style={{ padding: '8px 20px', background: '#28a745', color: 'white', border: 'none', borderRadius: '5px' }}>
          Create
        </button>
      </form>
      
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f8f9fa' }}>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>ID</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Username</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Role</th>
            <th style={{ border: '1px solid #dee2e6', padding: '10px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{user.id}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>
                {editingId === user.id ? (
                  <input
                    value={editUsername}
                    onChange={(e) => setEditUsername(e.target.value)}
                    style={{ padding: '5px', width: '90%' }}
                  />
                ) : (
                  user.username
                )}
              </td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>{user.role}</td>
              <td style={{ border: '1px solid #dee2e6', padding: '10px' }}>
                {editingId === user.id ? (
                  <>
                    <button onClick={() => handleUpdate(user.id)} style={{ padding: '5px 15px', marginRight: '5px', background: '#28a745', color: 'white', border: 'none', borderRadius: '3px' }}>
                      Save
                    </button>
                    <button onClick={handleCancelEdit} style={{ padding: '5px 15px', marginRight: '5px', background: '#6c757d', color: 'white', border: 'none', borderRadius: '3px' }}>
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button onClick={() => handleEdit(user)} style={{ padding: '5px 15px', marginRight: '5px', background: '#ffc107', color: 'black', border: 'none', borderRadius: '3px' }}>
                      Edit
                    </button>
                    <button onClick={() => handleDelete(user.id)} style={{ padding: '5px 15px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '3px' }}>
                      Delete
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default UserManagement;