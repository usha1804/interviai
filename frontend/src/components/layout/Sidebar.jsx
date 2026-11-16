import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  BarChart3,
  Briefcase,
  Building2,
  Code2,
  History,
  LayoutDashboard,
  LogOut,
  Mic,
  Settings,
  Users,
  X,
  BrainCircuit,
  FolderSearch,
  FileText,
  Github,
  Database,
  MessageSquare,
  Sparkles,
  Menu,
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, section: 'Overview' },
  {
    to: '/interviews',
    label: 'Interviews',
    icon: Mic,
    section: 'Interviews',
    children: [
      { to: '/interviews/ai', label: 'AI Interview', icon: BrainCircuit },
      { to: '/interviews/company', label: 'Company Interview', icon: Building2 },
      { to: '/interviews/adaptive', label: 'Adaptive Interview', icon: Sparkles },
      { to: '/interviews/voice', label: 'Voice Interview', icon: Mic },
    ],
  },
  {
    to: '/practice',
    label: 'Practice',
    icon: Code2,
    section: 'Practice',
    children: [
      { to: '/practice/coding', label: 'Coding Practice', icon: Code2 },
      { to: '/practice/system-design', label: 'System Design', icon: Database },
      { to: '/practice/technical', label: 'Technical Questions', icon: MessageSquare },
    ],
  },
  {
    to: '/career-tools',
    label: 'Career Tools',
    icon: FolderSearch,
    section: 'Career tools',
    children: [
      { to: '/career-tools/resume-analyzer', label: 'Resume Analyzer', icon: FileText },
      { to: '/career-tools/job-description', label: 'Job Description', icon: Briefcase },
      { to: '/career-tools/github', label: 'GitHub Analyzer', icon: Github },
      { to: '/career-coach', label: 'AI Career Coach', icon: BrainCircuit },
    ],
  },
  { to: '/history', label: 'Interview History', icon: History, section: 'Insights' },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
];

const bottomItems = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar = ({ isOpen, onClose, collapsed, onToggleCollapse, user, onLogout }) => {
  const isRecruiter = ['RECRUITER', 'ADMIN'].includes(user?.role?.toUpperCase());

  return (
    <>
      <aside className={`fixed inset-y-0 left-0 z-40 transition-all duration-200 lg:sticky lg:top-0 lg:h-screen ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} ${collapsed ? 'lg:w-20' : 'lg:w-64'} w-[280px] border-r border-slate-200 bg-white`}>
        <div className="flex h-full flex-col">
          <div className={`flex items-center justify-between border-b border-slate-200 px-4 py-4 ${collapsed ? 'lg:px-3' : ''}`}>
            <div className={`flex items-center gap-3 ${collapsed ? 'lg:justify-center lg:w-full' : ''}`}>
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div className={collapsed ? 'lg:hidden' : ''}><p className="text-base font-semibold tracking-tight text-slate-900">InterviAI</p><p className="text-[11px] text-slate-500">Interview workspace</p></div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
              aria-label="Close navigation"
            >
              <X className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onToggleCollapse}
              className="hidden rounded-lg border border-slate-200 p-2 text-slate-500 hover:bg-slate-100 lg:inline-flex"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <Menu className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-5">
            <nav className="space-y-1.5">
              {navItems.map((item) => (
                <div key={item.to} className="space-y-1">
                  {item.section && (
                    <p className={`px-3 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400 ${collapsed ? 'lg:hidden' : ''}`}>
                      {item.section}
                    </p>
                  )}
                  <NavLink
                    to={item.to}
                    end={item.to === '/dashboard'}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `group flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                        isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      } ${collapsed ? 'lg:justify-center lg:px-2' : ''}`
                    }
                    title={collapsed ? item.label : undefined}
                  >
                    <span className="flex items-center gap-3">
                      <item.icon className="h-4 w-4 shrink-0" />
                      <span className={collapsed ? 'lg:hidden' : ''}>{item.label}</span>
                    </span>
                  </NavLink>
                  {item.children && (
                    <div className={collapsed ? 'space-y-1' : 'ml-8 space-y-1 border-l border-slate-200 pl-3'}>
                      {item.children.map((child) => (
                        <NavLink
                          key={child.to}
                          onClick={onClose}
                          to={child.to}
                          className={({ isActive }) =>
                            `flex items-center gap-2 rounded-lg py-1.5 text-xs transition ${
                              isActive ? 'bg-slate-100 text-indigo-700' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'
                            } ${collapsed ? 'justify-center px-2' : 'px-2'}`
                          }
                          title={collapsed ? child.label : undefined}
                        >
                          <child.icon className="h-3.5 w-3.5 shrink-0" />
                          <span className={collapsed ? 'lg:hidden' : ''}>{child.label}</span>
                        </NavLink>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {isRecruiter && (
                <NavLink
                  to="/recruiter"
                  onClick={onClose}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                      isActive ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    } ${collapsed ? 'lg:justify-center lg:px-2' : ''}`
                  }
                  title={collapsed ? 'Recruiter Dashboard' : undefined}
                >
                  <Users className="h-4 w-4 shrink-0" />
                  <span className={collapsed ? 'lg:hidden' : ''}>Recruiter Dashboard</span>
                </NavLink>
              )}
            </nav>
          </div>

          <div className="border-t border-slate-200 p-3">
            <div className={`flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-2 ${collapsed ? 'lg:justify-center' : ''}`}>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
                <div className={`min-w-0 flex-1 ${collapsed ? 'lg:hidden' : ''}`}>
                  <p className="truncate text-sm font-medium text-slate-900">{user?.name || 'User'}</p>
                  <p className="truncate text-xs text-slate-500">{user?.email || ''}</p>
                </div>
            </div>

            <div className="mt-3 space-y-1">
              {bottomItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                      isActive ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    } ${collapsed ? 'lg:justify-center lg:px-2' : ''}`
                  }
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="h-4 w-4" />
                  <span className={collapsed ? 'lg:hidden' : ''}>{item.label}</span>
                </NavLink>
              ))}
              <button
                type="button"
                onClick={onLogout}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-slate-600 transition hover:bg-red-50 hover:text-red-700 ${collapsed ? 'lg:justify-center lg:px-2' : ''}`}
              >
                <LogOut className="h-4 w-4" />
                <span className={collapsed ? 'lg:hidden' : ''}>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </aside>

      {isOpen && <div className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-sm lg:hidden" onClick={onClose} aria-hidden="true" />}
    </>
  );
};
