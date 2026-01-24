import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      // Note: logout is defined below, this creates a safe dependency
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token, fetchCurrentUser]);

  const login = async (username, password) => {
    const response = await axios.post(`${API}/auth/login`, { username, password });
    const { access_token, user: userData } = response.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('token', access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    return userData;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const register = async (userData) => {
    await axios.post(`${API}/auth/register`, userData);
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    const userPermissions = user.permissions || [];
    return userPermissions.includes(permission);
  };

  const hasAnyPermission = (permissions) => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    const userPermissions = user.permissions || [];
    return permissions.some(perm => userPermissions.includes(perm));
  };

  const hasAllPermissions = (permissions) => {
    if (!user) return false;
    if (user.role === 'admin') return true;
    const userPermissions = user.permissions || [];
    return permissions.every(perm => userPermissions.includes(perm));
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      login, 
      logout, 
      register, 
      loading,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export { API };
