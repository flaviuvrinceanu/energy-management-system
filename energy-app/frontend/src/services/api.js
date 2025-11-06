import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:80';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (username, password, role) =>
  api.post('/auth/register', { username, password, role });

export const login = (username, password) =>
  api.post('/auth/login', { username, password });

// Users
export const getUsers = () => api.get('/users');
export const createUser = (username, password, role) =>
  api.post('/users', { username, password, role });  // Make sure it matches UserIn DTO
export const deleteUser = (id) => api.delete(`/users/${id}`);

// Devices
export const getDevices = () => api.get('/devices');
export const createDevice = (data) => api.post('/devices', data);
export const deleteDevice = (id) => api.delete(`/devices/${id}`);
export const assignDevice = (deviceId, userId) => api.post(`/devices/${deviceId}/assign/${userId}`);

// My Devices
export const getMyDevices = () => api.get('/devices/mine');

// Device Users
export const createDeviceUser = (data) => api.post('/device-users', data);

export default api;