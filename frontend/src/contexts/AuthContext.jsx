import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const clearSession = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setUser(null);
  };

  // Always verify with backend — never trust localStorage alone
  const verifyAuth = async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      setUser(null);
      setLoading(false);
      return false;
    }

    try {
      const response = await authService.verify();
      setUser(response.data);
      setError(null);
      return true;
    } catch (err) {
      // Any failure (network, 401, 403) = force logout
      clearSession();
      setError(null);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // On mount: verify immediately
  useEffect(() => {
    verifyAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Periodic session validation every 5 minutes
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      const token = localStorage.getItem('accessToken');
      if (token) verifyAuth();
    }, 5 * 60 * 1000);

    return () => clearInterval(intervalRef.current);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = async (email, password) => {
    // Require network before attempting login
    if (!navigator.onLine) {
      const err = new Error('No internet connection. Please connect and try again.');
      setError(err.message);
      throw err;
    }

    try {
      const response = await authService.login({ email: email.trim(), password });
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token || '');

      // Immediately verify with backend — do NOT trust the token alone
      const verifyRes = await authService.verify();
      setUser(verifyRes.data);
      setError(null);
      return response.data;
    } catch (err) {
      clearSession();
      const msg = err.response?.data?.detail || err.message || 'Login failed';
      setError(msg);
      throw err;
    }
  };

  const register = async (data) => {
    if (!navigator.onLine) {
      const err = new Error('No internet connection. Please connect and try again.');
      setError(err.message);
      throw err;
    }

    try {
      const response = await authService.register({ ...data, email: data.email.trim() });
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token || '');

      const verifyRes = await authService.verify();
      setUser(verifyRes.data);
      setError(null);
      return response.data;
    } catch (err) {
      clearSession();
      const msg = err.response?.data?.detail || err.message || 'Registration failed';
      setError(msg);
      throw err;
    }
  };

  const logout = () => {
    clearSession();
    clearInterval(intervalRef.current);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        login,
        register,
        logout,
        verifyAuth,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
