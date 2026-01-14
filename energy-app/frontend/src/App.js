import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import AdminDashboard from './components/AdminDashboard';
import ClientDashboard from './components/ClientDashboard';
import PrivateRoute from './components/PrivateRoute';
import NotificationWidget from './components/NotificationWidget';

function App() {
  return (
    <Router>
      {}
      <NotificationWidget />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/admin"
          element={
            <PrivateRoute role="admin">
              <AdminDashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/client"
          element={
            <PrivateRoute role="client">
              <ClientDashboard />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

function Home() {
  return (
    <div style={{ textAlign: 'center', marginTop: '100px' }}>
      <h1>Energy Management System</h1>
      <div style={{ marginTop: '50px' }}>
        <a href="/login" style={{ margin: '20px', padding: '10px 30px', textDecoration: 'none', background: '#007bff', color: 'white', borderRadius: '5px' }}>
          Login
        </a>
        <a href="/register" style={{ margin: '20px', padding: '10px 30px', textDecoration: 'none', background: '#28a745', color: 'white', borderRadius: '5px' }}>
          Register
        </a>
      </div>
    </div>
  );
}

export default App;
