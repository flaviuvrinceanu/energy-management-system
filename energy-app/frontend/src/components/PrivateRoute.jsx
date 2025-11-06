import React from 'react';
import { Navigate } from 'react-router-dom';
import {jwtDecode} from 'jwt-decode';

function PrivateRoute({ children, role }) {
  const token = localStorage.getItem('token');

  if (!token) {
    return <Navigate to="/login" />;
  }

  try {
    const decoded = jwtDecode(token);
    const userRole = decoded.role;

    if (role && userRole !== role) {
      return <Navigate to={userRole === 'admin' ? '/admin' : '/client'} />;
    }

    return children;
  } catch (err) {
    localStorage.removeItem('token');
    return <Navigate to="/login" />;
  }
}

export default PrivateRoute;