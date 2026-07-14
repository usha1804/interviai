import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { analyticsService } from '../services/api';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

export const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [strengthsWeaknesses, setStrengthsWeaknesses] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const COLORS = ['#6366f1', '#ec4899', '#14b8a6', '#f59e0b'];

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, trendRes, categoryRes, swRes] = await Promise.all([
          analyticsService.getDashboard(),
          analyticsService.getPerformanceTrend(),
          analyticsService.getCategoryPerformance(),
          analyticsService.getStrengthsWeaknesses(),
        ]);

        setAnalytics(analyticsRes.data);
        setTrendData(trendRes.data.trend || []);
        setCategoryData(categoryRes.data.categories || []);
        setStrengthsWeaknesses(swRes.data);
      } catch (err) {
        setError('Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
            <p className="text-slate-400 mt-4">Loading analytics...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-dark">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold mb-8">Your Analytics</h1>

          {error && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg">
              <p className="text-red-300">{error}</p>
            </div>
          )}

          {/* Performance Trend */}
          <div className="card mb-8">
            <h2 className="text-xl font-bold mb-6">Performance Trend</h2>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
                  <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-slate-400">No data available yet</p>
            )}
          </div>

          {/* Category Performance */}
          <div className="grid lg:grid-cols-2 gap-8 mb-8">
            <div className="card">
              <h2 className="text-xl font-bold mb-6">Category Performance</h2>
              {categoryData.length > 0 ? (
                <div className="space-y-4">
                  {categoryData.map((cat, idx) => (
                    <div key={idx}>
                      <div className="flex justify-between mb-2">
                        <span className="font-medium">{cat.category}</span>
                        <span className="text-indigo-400">{cat.average_score.toFixed(1)}/10</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-pink-500 h-2 rounded-full"
                          style={{ width: `${(cat.average_score / 10) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-400">No category data available</p>
              )}
            </div>

            {/* Key Metrics */}
            <div className="card">
              <h2 className="text-xl font-bold mb-6">Key Metrics</h2>
              <div className="space-y-4">
                <div className="p-4 bg-slate-800 rounded-lg">
                  <p className="text-slate-400 text-sm">Total Interviews</p>
                  <p className="text-3xl font-bold">{analytics?.total_interviews}</p>
                </div>
                <div className="p-4 bg-slate-800 rounded-lg">
                  <p className="text-slate-400 text-sm">Average Score</p>
                  <p className="text-3xl font-bold">{analytics?.average_score?.toFixed(1)}</p>
                </div>
                <div className="p-4 bg-slate-800 rounded-lg">
                  <p className="text-slate-400 text-sm">Technical Score</p>
                  <p className="text-3xl font-bold">{analytics?.technical_score?.toFixed(1)}</p>
                </div>
                <div className="p-4 bg-slate-800 rounded-lg">
                  <p className="text-slate-400 text-sm">Communication Score</p>
                  <p className="text-3xl font-bold">{analytics?.communication_score?.toFixed(1)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="grid lg:grid-cols-2 gap-8">
            <div className="card">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <CheckCircle className="text-green-500" size={24} />
                Strengths
              </h2>
              <div className="space-y-2">
                {strengthsWeaknesses?.strengths?.length > 0 ? (
                  strengthsWeaknesses.strengths.map((strength, idx) => (
                    <div key={idx} className="p-3 bg-green-900/20 border border-green-800 rounded-lg">
                      <p className="text-green-300">✓ {strength}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400">Complete more interviews to identify strengths</p>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <AlertCircle className="text-yellow-500" size={24} />
                Areas for Improvement
              </h2>
              <div className="space-y-2">
                {strengthsWeaknesses?.weaknesses?.length > 0 ? (
                  strengthsWeaknesses.weaknesses.map((weakness, idx) => (
                    <div key={idx} className="p-3 bg-yellow-900/20 border border-yellow-800 rounded-lg">
                      <p className="text-yellow-300">⚠ {weakness}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400">Areas for improvement will appear after more interviews</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
