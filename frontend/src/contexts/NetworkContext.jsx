import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const NetworkContext = createContext();

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const NetworkProvider = ({ children }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [backendReachable, setBackendReachable] = useState(null); // null = unknown
  const [showBanner, setShowBanner] = useState(false);

  const checkBackend = useCallback(async () => {
    try {
      await axios.get(`${API_URL}/health`, { timeout: 5000 });
      setBackendReachable(true);
      return true;
    } catch {
      setBackendReachable(false);
      return false;
    }
  }, []);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      checkBackend();
    };
    const handleOffline = () => {
      setIsOnline(false);
      setBackendReachable(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check
    checkBackend();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkBackend]);

  // Show banner whenever status changes
  useEffect(() => {
    setShowBanner(true);
    const t = setTimeout(() => setShowBanner(false), 4000);
    return () => clearTimeout(t);
  }, [isOnline, backendReachable]);

  const fullyOnline = isOnline && backendReachable === true;

  return (
    <NetworkContext.Provider value={{ isOnline, backendReachable, fullyOnline, checkBackend }}>
      {/* Network status banner */}
      {showBanner && (
        <div
          className={`fixed top-0 left-0 right-0 z-[9999] py-2 px-4 text-center text-sm font-semibold transition-all ${
            fullyOnline
              ? 'bg-green-600 text-white'
              : 'bg-red-600 text-white'
          }`}
        >
          {fullyOnline
            ? '✅ Connected — Server reachable'
            : !isOnline
            ? '🔴 No Internet Connection — Please connect to continue'
            : '🔴 Server Unreachable — Cannot connect to backend'}
        </div>
      )}

      {/* Persistent offline bar (always visible when offline) */}
      {!fullyOnline && !showBanner && (
        <div className="fixed top-0 left-0 right-0 z-[9999] py-1.5 px-4 text-center text-xs font-semibold bg-red-700 text-white">
          {!isOnline ? '🔴 No Internet Connection' : '🔴 Server Unreachable'}
        </div>
      )}

      {children}
    </NetworkContext.Provider>
  );
};

export const useNetwork = () => {
  const ctx = useContext(NetworkContext);
  if (!ctx) throw new Error('useNetwork must be used within NetworkProvider');
  return ctx;
};
