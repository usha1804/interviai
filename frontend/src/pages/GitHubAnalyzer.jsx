import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { useNetwork } from '../contexts/NetworkContext';
import api from '../services/api';
import { Github, Loader, AlertCircle, Star, GitFork, Code2, Zap, ExternalLink } from 'lucide-react';

const ScoreBar = ({ label, score, color }) => (
  <div>
    <div className="flex justify-between text-xs mb-1">
      <span className="text-slate-400">{label}</span>
      <span className={`font-semibold ${color}`}>{Math.round(score || 0)}/100</span>
    </div>
    <div className="h-2 rounded-full bg-slate-800">
      <div className={`h-2 rounded-full transition-all ${color.replace('text-', 'bg-')}`}
        style={{ width: `${Math.min(score || 0, 100)}%` }} />
    </div>
  </div>
);

export const GitHubAnalyzer = () => {
  const { fullyOnline } = useNetwork();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!url.trim()) { setError('Please enter a GitHub URL.'); return; }
    if (!fullyOnline) { setError('No internet connection.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await api.post('/github/analyze', { github_url: url });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800 px-4 py-1.5 text-sm text-slate-300 mb-3">
              <Github size={14} /> GitHub Portfolio Analyzer
            </div>
            <h1 className="text-3xl font-bold text-white">Analyze Your GitHub Profile</h1>
            <p className="mt-2 text-slate-400">Get an AI-powered assessment of your coding portfolio.</p>
          </div>

          {error && (
            <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <AlertCircle size={18} className="text-red-400 shrink-0" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 mb-6">
            <label className="block text-sm font-semibold text-slate-300 mb-2">GitHub Profile URL</label>
            <div className="flex gap-3">
              <input
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://github.com/username"
                className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
              <button
                onClick={handleAnalyze}
                disabled={loading || !fullyOnline}
                className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-slate-700 to-slate-600 px-5 py-3 font-semibold text-white disabled:opacity-50 hover:from-slate-600 hover:to-slate-500 transition"
              >
                {loading ? <Loader size={18} className="animate-spin" /> : <Zap size={18} />}
                Analyze
              </button>
            </div>
          </div>

          {result && (
            <div className="space-y-5">
              {/* Header */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-white">{result.name || result.username}</h2>
                    <p className="text-slate-400 text-sm mt-1">{result.bio}</p>
                    <div className="flex gap-4 mt-3 text-sm text-slate-400">
                      <span className="flex items-center gap-1"><Star size={14} className="text-amber-400" />{result.total_stars} stars</span>
                      <span className="flex items-center gap-1"><GitFork size={14} className="text-blue-400" />{result.total_forks} forks</span>
                      <span>{result.public_repos} repos</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-black text-indigo-400">{Math.round(result.github_score || 0)}</div>
                    <div className="text-xs text-slate-500">GitHub Score</div>
                  </div>
                </div>
                <div className="space-y-3">
                  <ScoreBar label="Project Quality" score={result.project_quality_score} color="text-emerald-400" />
                  <ScoreBar label="Coding Activity" score={result.coding_activity_score} color="text-blue-400" />
                  <ScoreBar label="Open Source" score={result.open_source_score} color="text-violet-400" />
                </div>
              </div>

              {/* Languages */}
              {result.languages && Object.keys(result.languages).length > 0 && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2"><Code2 size={14} /> Languages</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(result.languages).sort((a, b) => b[1] - a[1]).map(([lang, count]) => (
                      <span key={lang} className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-300">
                        {lang} <span className="text-slate-500">({count})</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Repos */}
              {result.top_repos?.length > 0 && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-3">Top Repositories</h3>
                  <div className="space-y-2">
                    {result.top_repos.slice(0, 6).map((repo, i) => (
                      <div key={i} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-3">
                        <div>
                          <a href={repo.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                            {repo.name} <ExternalLink size={11} />
                          </a>
                          <p className="text-xs text-slate-500 mt-0.5">{repo.description?.slice(0, 60) || 'No description'}</p>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-400">
                          <span className="flex items-center gap-1"><Star size={11} className="text-amber-400" />{repo.stars}</span>
                          <span className="rounded-full bg-slate-800 px-2 py-0.5">{repo.language}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Summary + Recommendations */}
              {result.ai_summary && (
                <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 p-5">
                  <h3 className="text-sm font-semibold text-indigo-300 mb-2">AI Assessment</h3>
                  <p className="text-sm text-slate-300">{result.ai_summary}</p>
                  {result.recommendations?.length > 0 && (
                    <ul className="mt-3 space-y-1">
                      {result.recommendations.map((r, i) => (
                        <li key={i} className="text-xs text-slate-400">• {r}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default GitHubAnalyzer;
