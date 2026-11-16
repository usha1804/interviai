import React, { useState } from 'react';
import { ChevronDown, ChevronRight, LogOut, Menu, Search, Settings, UserCircle2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const searchableRoutes = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'AI Interview', path: '/interviews/ai' },
  { label: 'Company Interview', path: '/interviews/company' },
  { label: 'Adaptive Interview', path: '/interviews/adaptive' },
  { label: 'Voice Interview', path: '/interviews/voice' },
  { label: 'Coding Practice', path: '/practice/coding' },
  { label: 'System Design', path: '/practice/system-design' },
  { label: 'Technical Questions', path: '/practice/technical' },
  { label: 'Resume Analyzer', path: '/career-tools/resume-analyzer' },
  { label: 'Job Description', path: '/career-tools/job-description' },
  { label: 'GitHub Analyzer', path: '/career-tools/github' },
  { label: 'Interview History', path: '/history' },
  { label: 'Analytics', path: '/analytics' },
  { label: 'Settings', path: '/settings' },
];

export const Topbar = ({ breadcrumbs = [], title, onMenuClick, user, onLogout }) => {
  const [query, setQuery] = useState('');
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleSearch = (event) => {
    event.preventDefault();
    const match = searchableRoutes.find((route) =>
      route.label.toLowerCase().includes(query.trim().toLowerCase())
    );
    if (match) {
      navigate(match.path);
      setQuery('');
      setMobileSearchOpen(false);
    }
  };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex min-h-[72px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 lg:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="min-w-0">
            <nav aria-label="Breadcrumb" className="mb-0.5 hidden items-center gap-1.5 text-xs text-slate-500 sm:flex">
              {breadcrumbs.length > 0 ? breadcrumbs.map((crumb, index) => (
                <React.Fragment key={`${crumb.label}-${index}`}>
                  {index > 0 && <ChevronRight className="h-3 w-3 text-slate-300" />}
                  {index === breadcrumbs.length - 1 ? (
                    <span aria-current="page" className="truncate text-slate-600">{crumb.label}</span>
                  ) : (
                    <Link className="truncate hover:text-indigo-700" to={crumb.path}>{crumb.label}</Link>
                  )}
                </React.Fragment>
              )) : <span>Overview</span>}
            </nav>
            <h1 className="truncate text-lg font-semibold tracking-tight text-slate-900 sm:text-xl">{title}</h1>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={() => setMobileSearchOpen((open) => !open)}
            aria-label={mobileSearchOpen ? 'Close search' : 'Search pages'}
            aria-expanded={mobileSearchOpen}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 md:hidden"
          >
            <Search className="h-4 w-4" />
          </button>
          <form onSubmit={handleSearch} role="search" className="hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 md:flex">
            <Search aria-hidden="true" className="h-4 w-4 text-slate-400" />
            <input
              aria-label="Search pages"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search pages"
              className="w-28 border-0 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400 xl:w-40"
            />
            <kbd className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] text-slate-400">↵</kbd>
          </form>

          <div className="relative">
            <button
              type="button"
              onClick={() => setAccountMenuOpen((open) => !open)}
              aria-expanded={accountMenuOpen}
              aria-label="Open account menu"
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-1.5 text-left hover:bg-slate-50 sm:pl-2"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
                {user?.name?.charAt(0)?.toUpperCase() || <UserCircle2 className="h-4 w-4" />}
              </span>
              <span className="hidden max-w-32 truncate text-sm font-medium text-slate-700 sm:block">{user?.name || 'Account'}</span>
              <ChevronDown className="hidden h-4 w-4 text-slate-400 sm:block" />
            </button>

            {accountMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg shadow-slate-900/10">
                <div className="border-b border-slate-100 px-3 py-2">
                  <p className="truncate text-sm font-medium text-slate-900">{user?.name || 'Account'}</p>
                  <p className="truncate text-xs text-slate-500">{user?.email}</p>
                </div>
                <Link
                  to="/settings"
                  onClick={() => setAccountMenuOpen(false)}
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                >
                  <Settings className="h-4 w-4" /> Account settings
                </Link>
                <button
                  type="button"
                  onClick={onLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-red-50 hover:text-red-700"
                >
                  <LogOut className="h-4 w-4" /> Sign out
                </button>
              </div>
            )}
          </div>
        </div>
        {mobileSearchOpen && (
          <form onSubmit={handleSearch} role="search" className="border-t border-slate-100 px-4 py-3 md:hidden">
            <label className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3">
              <Search aria-hidden="true" className="h-4 w-4 text-slate-400" />
              <input
                autoFocus
                aria-label="Search pages"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search pages"
                className="min-w-0 flex-1 border-0 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
              />
            </label>
          </form>
        )}
      </div>
    </header>
  );
};
