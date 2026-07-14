import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { useAuth } from '../contexts/AuthContext';
import { analyticsService } from '../services/api';
import {
  Play, Award, TrendingUp, BarChart3, FileText,
  Code2, Building2, ArrowRight, Sparkles,
  CalendarDays, Target, Zap, ChevronRight,
  Brain, Users, Mic, Server, Github, FileSearch,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const fmt = (v) => (typeof v === 'number' && isFinite(v) ? v.toFixed(1) : '—');

const QUICK_ACTIONS = [
  {
    title: 'Technical Interview',
    desc: 'Java, Python, React, System Design',
    to: '/interview/new',
    state: { type: 'TECHNICAL' },
    icon: Brain,
    gradient: 'from-blue-600 to-cyan-500',
    glow: 'shadow-blue-500/20',
    badge: 'Most Popular',
  },
  {
    title: 'HR / Behavioral',
    desc: 'Leadership, Teamwork, Soft Skills',
    to: '/interview/new',
    state: { type: 'HR' },
    icon: Users,
    gradient: 'from-emerald-600 to-teal-500',
    glow: 'shadow-emerald-500/20',
  },
  {
    title: 'Company Specific',
    desc: 'Google, Amazon, TCS, Infosys & more',
    to: '/company-selection',
    state: { type: 'COMPANY' },
    icon: Building2,
    gradient: 'from-amber-500 to-orange-500',
    glow: 'shadow-amber-500/20',
    badge: 'New',
  },
  {
    title: 'Resume Interview',
    desc: 'Questions from your uploaded resume',
    to: '/resume/upload',
    icon: FileText,
    gradient: 'from-pink-600 to-rose-500',
    glow: 'shadow-pink-500/20',
  },
  {
    title: 'Coding Round',
    desc: 'LeetCode-style problems with AI review',
    to: '/coding',
    icon: Code2,
    gradient: 'from-violet-600 to-purple-500',
    glow: 'shadow-violet-500/20',
  },
  {
    title: 'ATS Resume Analyzer',
    desc: 'Check resume score vs job description',
    to: '/ats',
    icon: FileSearch,
    gradient: 'from-teal-600 to-cyan-500',
    glow: 'shadow-teal-500/20',
    badge: 'New',
  },
  {
    title: 'System Design',
    desc: 'Design YouTube, Uber, WhatsApp & more',
    to: '/system-design',
    icon: Server,
    gradient: 'from-violet-700 to-indigo-600',
    glow: 'shadow-violet-500/20',
    badge: 'New',
  },
  {
    title: 'Voice Interview',
    desc: 'Speak your answers — AI listens & evaluates',
    to: '/voice-interview',
    icon: Mic,
    gradient: 'from-rose-600 to-pink-500',
    glow: 'shadow-rose-500/20',
    badge: 'New',
  },
  {
    title: 'GitHub Analyzer',
    desc: 'AI assessment of your coding portfolio',
    to: '/github',
    icon: Github,
    gradient: 'from-slate-600 to-slate-500',
    glow: 'shadow-slate-500/20',
    badge: 'New',
  },
];

const COMPANIES_PREVIEW = ['Google', 'Amazon', 'Microsoft', 'TCS', 'Infosys', 'Deloitte'];

export const Dashboard = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [aRes, hRes] = await Promise.all([
          analyticsService.getDashboard(),
          analyticsService.getHistory(0, 5),
        ]);
        setAnalytics(aRes.data);
        setHistory(hRes.data.interviews || []);
      } catch {
        setError('Unable to load dashboard data.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const stats = [
    { label: 'Total Sessions',   value: analytics?.total_interviews ?? 0,          icon: Target,    color: 'text-blue-400',    bg: 'bg-blue-500/10',    border: 'border-blue-500/20' },
    { label: 'Average Score',    value: fmt(analytics?.average_score),              icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
    { label: 'Best Score',       value: fmt(analytics?.best_score),                 icon: Award,     color: 'text-amber-400',   bg: 'bg-amber-500/10',   border: 'border-amber-500/20' },
    { label: 'Technical Score',  value: fmt(analytics?.technical_score),            icon: BarChart3, color: 'text-violet-400',  bg: 'bg-violet-500/10',  border: 'border-violet-500/20' },
  ];

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="flex min-h-screen items-center justify-center bg-slate-950">
          <div className="text-center">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-indigo-500" />
            <p className="mt-4 text-sm text-slate-500">Loading dashboard...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">

          {/* ── Hero Banner ── */}
          <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950 p-6 md:p-8">
            {/* decorative glow */}
            <div className="pointer-events-none absolute -top-20 -right-20 h-64 w-64 rounded-full bg-indigo-600/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-10 -left-10 h-48 w-48 rounded-full bg-violet-600/10 blur-3xl" />

            <div className="relative flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-500/25 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
                  <Sparkles size={12} />
                  AI-Powered Interview Platform
                </div>
                <h1 className="text-2xl font-bold text-white md:text-3xl">
                  Welcome back, <span className="text-indigo-400">{user?.name?.split(' ')[0] || 'there'}</span> 👋
                </h1>
                <p className="mt-2 max-w-xl text-sm text-slate-400">
                  {analytics?.total_interviews === 0
                    ? 'Start your first session and get AI-powered feedback instantly.'
                    : `${analytics?.total_interviews} sessions completed. Keep pushing — every round makes you sharper.`}
                </p>
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-slate-700/60 bg-slate-800/50 px-4 py-2.5 text-sm text-slate-400 self-start md:self-auto">
                <CalendarDays size={15} />
                {new Date().toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric' })}
              </div>
            </div>
          </div>

          {/* ── Stats ── */}
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            {stats.map((s) => {
              const Icon = s.icon;
              return (
                <div key={s.label} className={`rounded-2xl border ${s.border} ${s.bg} p-5`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-xs text-slate-500 font-medium">{s.label}</p>
                      <p className="mt-2 text-3xl font-bold text-white">{s.value}</p>
                    </div>
                    <div className={`rounded-xl bg-slate-800/80 p-2 ${s.color}`}>
                      <Icon size={18} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ── Main Grid ── */}
          <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">

            {/* Left — Quick Actions */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">Start a Session</h2>
                  <p className="text-xs text-slate-500 mt-0.5">Pick the round that fits your goal today</p>
                </div>
                <Link
                  to="/interview/new"
                  className="flex items-center gap-1 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-medium text-indigo-400 hover:bg-indigo-500/20 transition"
                >
                  <Zap size={12} /> Quick Start
                </Link>
              </div>

              <div className="space-y-2.5">
                {QUICK_ACTIONS.map((action) => {
                  const Icon = action.icon;
                  return (
                    <Link
                      key={action.title}
                      to={action.to}
                      state={action.state}
                      className="group flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 transition-all hover:border-slate-600 hover:bg-slate-800/80 hover:-translate-y-0.5"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`rounded-xl bg-gradient-to-br p-2.5 text-white shadow-lg ${action.gradient} ${action.glow}`}>
                          <Icon size={16} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-semibold text-white">{action.title}</p>
                            {action.badge && (
                              <span className="rounded-full bg-indigo-500/20 border border-indigo-500/30 px-2 py-0.5 text-[10px] font-semibold text-indigo-300">
                                {action.badge}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500">{action.desc}</p>
                        </div>
                      </div>
                      <ChevronRight size={15} className="text-slate-600 transition group-hover:text-slate-300 group-hover:translate-x-0.5" />
                    </Link>
                  );
                })}
              </div>

              {/* Company preview strip */}
              <div className="mt-5 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Building2 size={14} className="text-amber-400" />
                  <span className="text-xs font-semibold text-amber-300">Company-Specific Mode</span>
                </div>
                <p className="text-xs text-slate-500 mb-3">
                  Practice with questions tailored to each company's interview style and culture.
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {COMPANIES_PREVIEW.map((c) => (
                    <Link
                      key={c}
                      to="/interview/new"
                      state={{ type: 'COMPANY', company: c }}
                      className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] text-slate-300 hover:border-amber-500/40 hover:text-amber-300 transition"
                    >
                      {c}
                    </Link>
                  ))}
                  <Link
                    to="/interview/new"
                    state={{ type: 'COMPANY' }}
                    className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] text-amber-400 hover:bg-amber-500/20 transition"
                  >
                    +6 more →
                  </Link>
                </div>
              </div>
            </div>

            {/* Right — Recent Sessions */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">Recent Sessions</h2>
                  <p className="text-xs text-slate-500 mt-0.5">Your latest interview activity</p>
                </div>
                <Link
                  to="/analytics"
                  className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition"
                >
                  All analytics <ArrowRight size={12} />
                </Link>
              </div>

              {error ? (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">{error}</div>
              ) : history.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950/40 py-12 text-center">
                  <Play size={32} className="text-slate-700 mb-3" />
                  <p className="text-sm text-slate-500">No sessions yet.</p>
                  <p className="text-xs text-slate-600 mt-1">Start a practice round to track your progress.</p>
                  <Link
                    to="/interview/new"
                    className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition"
                  >
                    Start Now
                  </Link>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {history.map((s) => {
                    const score = s.overall_score;
                    const scoreColor =
                      score >= 8 ? 'text-emerald-400' :
                      score >= 5 ? 'text-amber-400' : 'text-red-400';
                    return (
                      <div
                        key={s.id}
                        className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                            <Brain size={14} className="text-indigo-400" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white">{s.interview_type}</p>
                            <p className="text-xs text-slate-500">
                              {new Date(s.started_at).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                              {s.duration_minutes ? ` · ${s.duration_minutes}m` : ''}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-bold ${scoreColor}`}>
                            {score != null ? score.toFixed(1) : '—'}
                          </p>
                          <p className="text-[10px] text-slate-600 uppercase tracking-wide">{s.status}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Analytics shortcut */}
              <Link
                to="/analytics"
                className="mt-4 flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/50 py-3 text-sm font-medium text-slate-300 hover:border-indigo-500/40 hover:text-indigo-300 transition"
              >
                <BarChart3 size={15} /> View Full Analytics
              </Link>
            </div>
          </div>

        </div>
      </div>
    </>
  );
};

export default Dashboard;
