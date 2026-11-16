import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, Award, BarChart3, BrainCircuit, Briefcase, CheckCircle2,
  ChevronRight, Code2, FileText, Mic, Play, Sparkles, Target, Users,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { analyticsService } from '../services/api';

const startOptions = [
  { title: 'Technical interview', detail: 'Practice role-specific technical questions.', to: '/interviews/ai', icon: BrainCircuit },
  { title: 'Behavioral interview', detail: 'Build clear, confident interview stories.', to: '/interview/new', state: { type: 'HR' }, icon: Users },
  { title: 'Company interview', detail: 'Prepare for a company and role.', to: '/interviews/company', icon: Briefcase },
  { title: 'Resume interview', detail: 'Practice questions based on your resume.', to: '/resume/upload', icon: FileText },
  { title: 'Coding practice', detail: 'Work through a coding interview round.', to: '/practice/coding', icon: Code2 },
  { title: 'Voice interview', detail: 'Practice speaking your answers aloud.', to: '/interviews/voice', icon: Mic },
];

const recommendations = [
  { title: 'Adaptive interview', detail: 'Let question difficulty respond to your answers.', to: '/interviews/adaptive', icon: Sparkles },
  { title: 'System design', detail: 'Practice architecture and trade-off discussions.', to: '/practice/system-design', icon: BarChart3 },
  { title: 'Technical questions', detail: 'Review fundamentals across core technologies.', to: '/practice/technical', icon: Target },
];

const formatScore = (score) =>
  typeof score === 'number' && Number.isFinite(score) ? score.toFixed(1) : '—';

const formatDate = (date) =>
  date
    ? new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Date unavailable';

export const Dashboard = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const fetchDashboard = async () => {
      try {
        const [analyticsResult, historyResult] = await Promise.allSettled([
          analyticsService.getDashboard(),
          analyticsService.getHistory(0, 5),
        ]);
        if (!active) return;
        const failures = [];
        if (analyticsResult.status === 'fulfilled') {
          setAnalytics(analyticsResult.value.data);
        } else {
          failures.push('Statistics are unavailable.');
        }
        if (historyResult.status === 'fulfilled') {
          setHistory(historyResult.value.data.interviews || []);
          setHistoryLoaded(true);
        } else {
          failures.push('Recent interviews are unavailable.');
        }
        if (failures.length) setError(failures.join(' '));
      } catch (requestError) {
        if (active) {
          setError(requestError.response?.data?.detail || 'Dashboard data could not be loaded. Please try again.');
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchDashboard();
    return () => { active = false; };
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there';

  const stats = [
    { label: 'Total interviews', value: analytics ? analytics.total_interviews ?? 0 : '—', icon: Target },
    { label: 'Average score', value: formatScore(analytics?.average_score), icon: BarChart3 },
    { label: 'Best score', value: formatScore(analytics?.best_score), icon: Award },
    { label: 'Technical score', value: formatScore(analytics?.technical_score), icon: CheckCircle2 },
  ];

  if (loading) {
    return (
      <div className="space-y-6" aria-label="Loading dashboard">
        <div className="h-44 animate-pulse rounded-2xl bg-slate-200" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => <div key={stat.label} className="h-28 animate-pulse rounded-xl bg-white ring-1 ring-slate-200" />)}
        </div>
        <div className="h-72 animate-pulse rounded-2xl bg-white ring-1 ring-slate-200" />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-8">
      {error && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="flex flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-900/[0.03] sm:flex-row sm:items-center sm:justify-between sm:p-8">
        <div>
          <p className="text-sm font-medium text-indigo-700">{greeting}, {firstName}</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Your preparation, in one place.</h2>
          <p className="mt-2 text-sm text-slate-500">Your AI-powered interview preparation workspace.</p>
        </div>
        <Link
          to="/interview/new"
          className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700"
        >
          <Play className="h-4 w-4" /> Start new interview
        </Link>
      </section>

      <section aria-label="Interview statistics" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02]">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-slate-500">{label}</p>
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
                <Icon className="h-4 w-4" />
              </span>
            </div>
            <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
          </div>
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Start your preparation</h2>
              <p className="mt-1 text-sm text-slate-500">Choose a session that fits your next goal.</p>
            </div>
            <Link to="/interviews" className="inline-flex items-center gap-1 text-sm font-medium text-indigo-700 hover:text-indigo-800">
              All interviews <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {startOptions.map(({ title, detail, to, state, icon: Icon }) => (
              <Link
                key={title}
                to={to}
                state={state}
                className="group flex min-h-24 items-start gap-3 rounded-xl border border-slate-200 p-4 transition hover:border-indigo-200 hover:bg-indigo-50/40"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700 transition group-hover:bg-indigo-100 group-hover:text-indigo-700">
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-slate-900">{title}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500">{detail}</span>
                </span>
                <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-600" />
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Recommended practice</h2>
            <p className="mt-1 text-sm text-slate-500">Explore more ways to build confidence.</p>
          </div>
          <div className="divide-y divide-slate-100">
            {recommendations.map(({ title, detail, to, icon: Icon }) => (
              <Link key={title} to={to} className="group flex items-center gap-3 py-4 first:pt-1 last:pb-1">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700 group-hover:bg-indigo-50 group-hover:text-indigo-700">
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-slate-900">{title}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500">{detail}</span>
                </span>
                <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 group-hover:text-indigo-600" />
              </Link>
            ))}
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Recent activity</h2>
            <p className="mt-1 text-sm text-slate-500">Your latest interview sessions.</p>
          </div>
          <Link to="/history" className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-indigo-700 hover:text-indigo-800">
            View history <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {!historyLoaded ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-5 py-8 text-center text-sm text-slate-500">
            Recent interview activity could not be loaded.
          </div>
        ) : history.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <span className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-white text-slate-500 ring-1 ring-slate-200">
              <Play className="h-4 w-4" />
            </span>
            <h3 className="mt-3 text-sm font-semibold text-slate-900">Your first interview starts here</h3>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">Complete a practice session to see your activity and feedback here.</p>
            <Link to="/interview/new" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
              Start an interview <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {history.slice(0, 5).map((session) => (
              <div key={session.id} className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
                    <BrainCircuit className="h-4 w-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{session.interview_type || 'Interview'}</p>
                    <p className="mt-0.5 text-xs text-slate-500">{formatDate(session.started_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-semibold tabular-nums text-slate-700">
                    {session.overall_score == null ? '—' : formatScore(session.overall_score)}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">
                    {(session.status || 'unknown').toLowerCase().replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
