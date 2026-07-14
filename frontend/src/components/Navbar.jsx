import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Menu, LogOut, BarChart3, Home } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = React.useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-slate-900 border-b border-slate-700 backdrop-blur-lg bg-opacity-80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-pink-500 rounded-lg"></div>
            <span className="text-xl font-bold text-white">InterviAI</span>
          </Link>

          {isAuthenticated && (
            <div className="hidden md:flex items-center space-x-6">
              <Link to="/dashboard" className="text-slate-300 hover:text-white flex items-center gap-2">
                <Home size={18} />
                Dashboard
              </Link>
              <Link to="/analytics" className="text-slate-300 hover:text-white flex items-center gap-2">
                <BarChart3 size={18} />
                Analytics
              </Link>
              <div className="flex items-center space-x-4">
                <span className="text-slate-300">{user?.name}</span>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                >
                  <LogOut size={18} />
                  Logout
                </button>
              </div>
            </div>
          )}

          <button
            className="md:hidden text-white"
            onClick={() => setIsOpen(!isOpen)}
          >
            <Menu size={24} />
          </button>
        </div>

        {isOpen && isAuthenticated && (
          <div className="md:hidden pb-4 space-y-2">
            <Link
              to="/dashboard"
              className="block text-slate-300 hover:text-white py-2"
            >
              Dashboard
            </Link>
            <Link
              to="/analytics"
              className="block text-slate-300 hover:text-white py-2"
            >
              Analytics
            </Link>
            <button
              onClick={handleLogout}
              className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};
