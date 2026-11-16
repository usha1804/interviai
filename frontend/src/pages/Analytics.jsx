import React, { useEffect, useState } from 'react';
import { AlertCircle, Award, BarChart3, CheckCircle2, TrendingUp } from 'lucide-react';
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { PageHeader } from '../components/PageHeader';
import { analyticsService } from '../services/api';

const metricCards = [
  { label: 'Interviews completed', key: 'total_interviews', icon: BarChart3, format: (value) => value ?? '—' },
  { label: 'Average score', key: 'average_score', icon: TrendingUp, format: (value) => typeof value === 'number' ? value.toFixed(1) : '—' },
  { label: 'Best score', key: 'best_score', icon: Award, format: (value) => typeof value === 'number' ? value.toFixed(1) : '—' },
  { label: 'Technical score', key: 'technical_score', icon: CheckCircle2, format: (value) => typeof value === 'number' ? value.toFixed(1) : '—' },
];

export const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [strengthsWeaknesses, setStrengthsWeaknesses] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const fetchData = async () => {
      const results = await Promise.allSettled([
        analyticsService.getDashboard(),
        analyticsService.getPerformanceTrend(),
        analyticsService.getCategoryPerformance(),
        analyticsService.getStrengthsWeaknesses(),
      ]);
      if (!active) return;
      const [metrics, trend, categories, strengths] = results;
      if (metrics.status === 'fulfilled') setAnalytics(metrics.value.data);
      if (trend.status === 'fulfilled') setTrendData(trend.value.data.trend || []);
      if (categories.status === 'fulfilled') setCategoryData(categories.value.data.categories || []);
      if (strengths.status === 'fulfilled') setStrengthsWeaknesses(strengths.value.data);
      if (results.some((result) => result.status === 'rejected')) {
        setError('Some analytics could not be loaded. Refresh the page to try again.');
      }
      setLoading(false);
    };
    fetchData();
    return () => { active = false; };
  }, []);

  if (loading) {
    return (
      <div className="space-y-5" aria-label="Loading analytics">
        <div className="h-24 animate-pulse rounded-xl bg-white ring-1 ring-slate-200" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {metricCards.map((metric) => <div key={metric.key} className="h-28 animate-pulse rounded-xl bg-white ring-1 ring-slate-200" />)}
        </div>
        <div className="h-72 animate-pulse rounded-xl bg-white ring-1 ring-slate-200" />
      </div>
    );
  }

  const chartData = trendData.map((item) => ({
    ...item,
    label: item.date ? new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '',
  }));
  const strengths = strengthsWeaknesses?.strengths || [];
  const areasToImprove = strengthsWeaknesses?.weaknesses || strengthsWeaknesses?.weak_areas || [];

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        eyebrow="Insights"
        title="Your performance"
        description="Track your progress using results from your interview sessions."
      />

      {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metricCards.map(({ label, key, icon: Icon, format }) => (
          <div key={key} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02]">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-slate-500">{label}</p>
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700"><Icon className="h-4 w-4" /></span>
            </div>
            <p className="mt-3 text-2xl font-semibold tabular-nums text-slate-900">{format(analytics?.[key])}</p>
          </div>
        ))}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
        <div className="mb-5">
          <h3 className="font-semibold text-slate-900">Performance trend</h3>
          <p className="mt-1 text-sm text-slate-500">Scores from completed interview sessions.</p>
        </div>
        {chartData.length ? (
          <div className="h-72 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 4, left: -18 }}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 10]} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ border: '1px solid #e2e8f0', borderRadius: 10, fontSize: 13 }} />
                <Line type="monotone" dataKey="score" name="Score" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 3, fill: '#4f46e5' }} activeDot={{ r: 5 }} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-12 text-center">
            <p className="text-sm font-medium text-slate-800">Not enough interview data yet</p>
            <p className="mt-1 text-sm text-slate-500">Complete an interview with a score to see your trend.</p>
          </div>
        )}
      </section>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
          <h3 className="font-semibold text-slate-900">Category performance</h3>
          <p className="mt-1 text-sm text-slate-500">Average answer scores by question category.</p>
          {categoryData.length ? (
            <div className="mt-5 space-y-4">
              {categoryData.map((category) => {
                const score = Number(category.average_score) || 0;
                return (
                  <div key={category.category}>
                    <div className="mb-1.5 flex justify-between gap-3 text-sm">
                      <span className="truncate font-medium text-slate-700">{category.category}</span>
                      <span className="shrink-0 tabular-nums text-slate-500">{score.toFixed(1)} / 10</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.min(Math.max(score * 10, 0), 100)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : <p className="mt-5 text-sm text-slate-500">Category insights will appear after you complete interviews.</p>}
        </section>

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
            <h3 className="font-semibold text-slate-900">Strengths</h3>
            {strengths.length ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-600">{strengths.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul>
            ) : <p className="mt-2 text-sm text-slate-500">Strengths will appear when enough interview data is available.</p>}
          </section>
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-900/[0.02] sm:p-6">
            <h3 className="font-semibold text-slate-900">Areas to practice</h3>
            {areasToImprove.length ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-600">{areasToImprove.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul>
            ) : <p className="mt-2 text-sm text-slate-500">Practice recommendations will appear when enough interview data is available.</p>}
          </section>
        </div>
      </div>
    </div>
  );
};
