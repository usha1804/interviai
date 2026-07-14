import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNetwork } from '../contexts/NetworkContext';

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, verifyAuth } = useAuth();
  const { isOnline, backendReachable } = useNetwork();
  const [verifying, setVerifying] = useState(true);
  const [verified, setVerified] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      setVerifying(true);
      const ok = await verifyAuth();
      if (!cancelled) {
        setVerified(ok);
        setVerifying(false);
      }
    };

    check();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading || verifying) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4" />
          <p className="text-slate-400">Verifying session...</p>
        </div>
      </div>
    );
  }

  // No internet
  if (!isOnline) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-4">🔴</div>
          <h2 className="text-xl font-bold text-white mb-2">No Internet Connection</h2>
          <p className="text-slate-400 mb-6">
            InterviAI requires an active internet connection. Please connect and try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary px-6 py-2"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Backend unreachable
  if (backendReachable === false) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-white mb-2">Server Unreachable</h2>
          <p className="text-slate-400 mb-6">
            Cannot connect to the InterviAI server. Please try again shortly.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary px-6 py-2"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!verified || !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
