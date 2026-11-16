import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

const routeNames = {
  '/dashboard': 'Dashboard',
  '/interviews': 'Interviews',
  '/interviews/ai': 'AI Interview',
  '/interviews/company': 'Company Interview',
  '/interviews/adaptive': 'Adaptive Interview',
  '/interviews/voice': 'Voice Interview',
  '/practice': 'Practice',
  '/practice/coding': 'Coding Practice',
  '/practice/system-design': 'System Design',
  '/practice/technical': 'Technical Questions',
  '/career-tools': 'Career Tools',
  '/career-tools/resume-analyzer': 'Resume Analyzer',
  '/career-tools/job-description': 'Job Description Analyzer',
  '/career-tools/github': 'GitHub Portfolio Analyzer',
  '/career-coach': 'AI Career Coach',
  '/history': 'Interview History',
  '/analytics': 'Analytics',
  '/recruiter': 'Recruiter Dashboard',
  '/settings': 'Settings',
  '/interview/new': 'Start Interview',
  '/interview/session': 'Interview Session',
  '/interview/feedback': 'Interview Feedback',
  '/resume/upload': 'Resume Upload',
  '/resume/interview': 'Resume Interview',
  '/coding': 'Coding Interview',
  '/system-design': 'System Design Interview',
  '/voice-interview': 'Voice Interview',
  '/ats': 'ATS Analyzer',
  '/github': 'GitHub Analyzer',
  '/webcam': 'Webcam Interview',
  '/company-selection': 'Company Selection',
};

export const AppLayout = ({ children, pageTitle, breadcrumbs }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const computedBreadcrumbs = useMemo(() => {
    if (breadcrumbs?.length) return breadcrumbs;

    const segments = location.pathname.split('/').filter(Boolean);
    const crumbPath = [];
    const generated = segments.map((segment, index) => {
      const path = `/${segments.slice(0, index + 1).join('/')}`;
      const label = routeNames[path] || segment.replace(/-/g, ' ');
      crumbPath.push({ label, path });
      return { label, path };
    });

    return generated.length ? generated : [{ label: 'Dashboard', path: '/dashboard' }];
  }, [breadcrumbs, location.pathname]);

  const resolvedTitle = pageTitle || routeNames[location.pathname] || 'Dashboard';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="flex min-h-screen">
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
          user={user}
          onLogout={handleLogout}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar
            breadcrumbs={computedBreadcrumbs}
            title={resolvedTitle}
            onMenuClick={() => setSidebarOpen(true)}
            user={user}
            onLogout={handleLogout}
          />

          <main className="app-main flex-1 px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto w-full max-w-7xl">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
};
