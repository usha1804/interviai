import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowUpRight, Search } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { analyticsService } from '../services/api';

const dateLabel = (value) => value
  ? new Date(value).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
    })
  : 'Date unavailable';

export const InterviewHistory = () => {
  const [sessions, setSessions] = useState([]);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    analyticsService.getHistory(0, 100)
      .then(({ data }) => {
        if (active) setSessions(data.interviews || []);
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'Interview history could not be loaded.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const filteredSessions = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return sessions.filter((session) => {
      const matchesQuery = !normalizedQuery || (session.interview_type || '').toLowerCase().includes(normalizedQuery);
      const matchesStatus = statusFilter === 'all' || (session.status || '').toLowerCase() === statusFilter;
      return matchesQuery && matchesStatus;
    });
  }, [sessions, query, statusFilter]);

  return (
    <div className="pb-8">
      <PageHeader
        eyebrow="Insights"
        title="Interview history"
        description="Review completed sessions and see how your practice is progressing."
      />

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-900/[0.02]">
        <div className="flex flex-col gap-3 border-b border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
          <label className="flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 sm:w-72">
            <Search aria-hidden="true" className="h-4 w-4 text-slate-400" />
            <input
              aria-label="Search interview types"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search interviews"
              className="min-w-0 flex-1 border-0 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
            />
          </label>
          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700"
          >
            <option value="all">All statuses</option>
            <option value="completed">Completed</option>
            <option value="in_progress">In progress</option>
            <option value="abandoned">Abandoned</option>
          </select>
        </div>

        {error && (
          <div role="alert" className="m-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
          </div>
        )}

        {loading ? (
          <div className="space-y-3 p-5" aria-label="Loading interview history">
            {[1, 2, 3].map((item) => <div key={item} className="h-12 animate-pulse rounded-lg bg-slate-100" />)}
          </div>
        ) : !error && filteredSessions.length === 0 ? (
          <div className="px-5 py-14 text-center">
            <h3 className="text-sm font-semibold text-slate-900">{sessions.length ? 'No matching interviews' : 'No interviews yet'}</h3>
            <p className="mt-1 text-sm text-slate-500">
              {sessions.length ? 'Try another search or status filter.' : 'Your completed and in-progress sessions will appear here.'}
            </p>
            {!sessions.length && (
              <Link to="/interview/new" className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
                Start an interview <ArrowUpRight className="h-4 w-4" />
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] text-left">
              <thead className="bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-5 py-3">Interview</th>
                  <th scope="col" className="px-5 py-3">Date</th>
                  <th scope="col" className="px-5 py-3">Duration</th>
                  <th scope="col" className="px-5 py-3">Score</th>
                  <th scope="col" className="px-5 py-3">Status</th>
                  <th scope="col" className="px-5 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredSessions.map((session) => (
                  <tr key={session.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-4 font-medium text-slate-900">{session.interview_type || 'Interview'}</td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">{dateLabel(session.started_at)}</td>
                    <td className="px-5 py-4 text-slate-600">{session.duration_minutes ? `${session.duration_minutes} min` : '—'}</td>
                    <td className="px-5 py-4 font-medium tabular-nums text-slate-700">{session.overall_score == null ? '—' : Number(session.overall_score).toFixed(1)}</td>
                    <td className="px-5 py-4">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">
                        {(session.status || 'unknown').toLowerCase().replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      {session.status === 'COMPLETED' && (
                        <Link to={`/interviews/report/${session.id}`} className="font-medium text-indigo-700 hover:text-indigo-900">
                          View report
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};
