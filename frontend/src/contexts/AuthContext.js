import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios to send cookies with requests
axios.defaults.withCredentials = true;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [csrfToken, setCsrfToken] = useState(null);

  // Function to get CSRF token from cookie
  const getCsrfTokenFromCookie = () => {
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    for (let i = 0; i < cookieArray.length; i++) {
      let cookie = cookieArray[i].trim();
      if (cookie.indexOf(name) === 0) {
        return cookie.substring(name.length, cookie.length);
      }
    }
    return null;
  };

  // Setup axios interceptor to add CSRF token to state-changing requests
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        // Add CSRF token header for state-changing methods
        if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase())) {
          // Get token from state or cookie
          const token = csrfToken || getCsrfTokenFromCookie();
          if (token) {
            config.headers['X-CSRF-Token'] = token;
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Cleanup interceptor on unmount
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
    };
  }, [csrfToken]);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      setIsAuthenticated(true);
      
      // Try to get CSRF token from cookie if not in state
      if (!csrfToken) {
        const tokenFromCookie = getCsrfTokenFromCookie();
        if (tokenFromCookie) {
          setCsrfToken(tokenFromCookie);
        }
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
      setIsAuthenticated(false);
      setCsrfToken(null);
    } finally {
      setLoading(false);
    }
  }, [csrfToken]);

  useEffect(() => {
    // Try to fetch user on mount (will use cookie if exists)
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (username, password) => {
    const response = await axios.post(`${API}/auth/login`, { username, password });
    const { user: userData, csrf_token } = response.data;
    setUser(userData);
    setIsAuthenticated(true);
    setCsrfToken(csrf_token);
    return userData;
  };

  const logout = async () => {
    try {
      // Call backend logout to clear cookies
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setCsrfToken(null);
    }
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
      isAuthenticated,
      login, 
      logout, 
      register, 
      loading,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      csrfToken
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
