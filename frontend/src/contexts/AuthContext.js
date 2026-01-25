import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

// Create ONE axios instance with baseURL (WITHOUT /api suffix)
const API = axios.create({
  baseURL: BACKEND_URL,
  withCredentials: true
});

// Add request interceptor to attach JWT token
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const fetchCurrentUser = useCallback(async () => {
    try {
      // Check if token exists before calling /me
      const token = localStorage.getItem('token');
      if (!token) {
        setUser(null);
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      const response = await API.get('/api/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Try to fetch user on mount if token exists
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (username, password) => {
    // Await POST /api/auth/login
    const response = await API.post('/api/auth/login', { username, password });
    const { access_token, user: userData } = response.data;
    
    // Store token FIRST using localStorage
    localStorage.setItem('token', access_token);
    
    // THEN set user and isAuthenticated
    setUser(userData);
    setIsAuthenticated(true);
    
    return userData;
  };

  const logout = async () => {
    try {
      // Call backend logout to clear cookies
      await API.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('token');
    }
  };

  const register = async (userData) => {
    await API.post('/auth/register', userData);
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
      isAuthenticated,
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
