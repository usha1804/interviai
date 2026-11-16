import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNetwork } from '../contexts/NetworkContext';
import { Mail, Lock, AlertCircle, Loader, WifiOff } from 'lucide-react';

const getLoginError = (err) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(item => {
      const location = Array.isArray(item?.loc) ? item.loc : [];
      const field = location.length ? location[location.length - 1] : null;
      const message = item?.msg || 'Invalid value';
      return field ? `${field}: ${message}` : message;
    }).join('; ');
  }
  return err?.message || 'Login failed';
};

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { fullyOnline, isOnline } = useNetwork();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setEmailError('');

    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setEmailError('Enter your email address.');
      return;
    }

    if (!isOnline) {
      setError('No internet connection. Please connect and try again.');
      return;
    }
    if (!fullyOnline) {
      setError('Server is unreachable. Please try again shortly.');
      return;
    }

    setLoading(true);
    try {
      await login(normalizedEmail, password);
      navigate('/dashboard');
    } catch (err) {
      if (err.isOffline || err.isNetworkError) {
        setError('No internet connection. Please connect and try again.');
      } else {
        const detail = err?.response?.data?.detail;
        const emailValidationError = Array.isArray(detail)
          ? detail.find(item => Array.isArray(item?.loc) && item.loc.includes('email'))
          : null;
        if (emailValidationError) {
          setEmailError('Enter a valid email address (for example, name@example.com).');
        } else {
          setError(getLoginError(err));
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">InterviAI</h1>
          <p className="text-slate-500">Welcome back</p>
        </div>

        {/* Offline warning */}
        {!isOnline && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3 items-center">
            <WifiOff className="text-red-600 shrink-0" size={20} />
            <p className="text-red-700 text-sm font-medium">
              No internet connection. Login requires an active connection.
            </p>
          </div>
        )}

        <div className="card">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
            <p className="text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 text-slate-500" size={20} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError('');
                  }}
                  onBlur={() => setEmail(value => value.trim())}
                  aria-invalid={Boolean(emailError)}
                  aria-describedby={emailError ? 'login-email-error' : undefined}
                  className={`w-full bg-white border rounded-lg pl-10 pr-4 py-2.5 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 ${emailError ? 'border-red-500' : 'border-slate-200'}`}
                  placeholder="Enter your email"
                  required
                />
              </div>
              {emailError && <p id="login-email-error" className="mt-2 text-sm text-red-600">{emailError}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 text-slate-500" size={20} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg pl-10 pr-4 py-2.5 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !isOnline}
              className="w-full btn-primary py-3 font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading && <Loader size={20} className="animate-spin" />}
              {!isOnline ? 'No Internet Connection' : loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-slate-500">
            <p>
              Don't have an account?{' '}
              <Link to="/signup" className="text-indigo-500 hover:text-indigo-400">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
