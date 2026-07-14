import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { useNetwork } from '../contexts/NetworkContext';
import api from '../services/api';
import {
  FileSearch, Loader, AlertCircle, CheckCircle, XCircle,
  Download, Target, Zap, TrendingUp, ArrowRight,
} from 'lucide-react';

const ScoreRing = ({ score, label, color }) => {
  const r = 28, c = 2 * Math.PI * r;
  const pct = Math.min(Math.max(score || 0, 0), 100);
  const dash = (pct / 100) * c;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="72" height="72" className="-rotate-90">
        <circle cx="36" cy="36" r={r} fill="none" stroke="#1e293b" strokeWidth="6" />
        <circle cx="36" cy="36" r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={`${dash} ${c}`} strokeLinecap="round" />
      </svg>
      <span className="text-lg font-bold text-white -mt-12">{Math.round(pct)}</span>
      <span className="text-xs text-slate-400 mt-8">{label}</span>
    </div>
  );
};

export const ATSAnalyzer = () => {
  const { fullyOnline } = useNetwork();
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!jdText.trim()) { setError('Please paste a job description.'); return; }
    if (!fullyOnline) { setError('No internet connection.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await api.post('/ats/analyze', { jd_text: jdText });
      setResult(res.data);
      setReportId(res.data.report_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const res = await api.get(`/ats/report/${reportId}/pdf`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const a = document.createElement('a'); a.href = url; a.download = `ats_report_${reportId}.pdf`; a.click();
    } catch { setError('PDF download failed.'); }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300 mb-3">
              <FileSearch size={14} /> ATS Resume Analyzer
            </div>
            <h1 className="text-3xl font-bold text-white">Check Your Resume Score</h1>
            <p className="mt-2 text-slate-400">Paste a job description to see how well your resume matches.</p>
          </div>

          {error && (
            <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <AlertCircle size={18} className="text-red-400 shrink-0" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 mb-6">
            <label className="block text-sm font-semibold text-slate-300 mb-2">Job Description</label>
            <textarea
              value={jdText}
              onChange={e => setJdText(e.target.value)}
              placeholder="Paste the full job description here..."
              rows={8}
              className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none resize-none"
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !fullyOnline}
              className="mt-4 flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 font-semibold text-white disabled:opacity-50 hover:from-indigo-500 hover:to-violet-500 transition"
            >
              {loading ? <><Loader size={18} className="animate-spin" /> Analyzing...</> : <><Zap size={18} /> Analyze Resume</>}
            </button>
          </div>

          {result && (
            <div className="space-y-5">
              {/* Score Cards */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-white">ATS Analysis Results</h2>
                  {reportId && (
                    <button onClick={handleDownload} className="flex items-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-sm text-indigo-300 hover:bg-indigo-500/20 transition">
                      <Download size={14} /> Download PDF
                    </button>
                  )}
                </div>
                <div className="flex justify-around flex-wrap gap-6">
                  <ScoreRing score={result.ats_score} label="ATS Score" color="#6366f1" />
                  <ScoreRing score={result.keyword_match_pct} label="Keyword Match" color="#10b981" />
                  <ScoreRing score={(result.matching_skills?.length || 0) * 10} label="Skills Match" color="#f59e0b" />
                </div>
                {result.ai_summary && (
                  <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/50 p-4">
                    <p className="text-sm text-slate-300">{result.ai_summary}</p>
                  </div>
                )}
              </div>

              {/* Skills Grid */}
              <div className="grid gap-4 md:grid-cols-2">
                <SkillList title="✅ Matching Skills" items={result.matching_skills} color="text-emerald-400" bg="bg-emerald-500/10" border="border-emerald-500/20" />
                <SkillList title="❌ Missing Skills" items={result.missing_skills} color="text-red-400" bg="bg-red-500/10" border="border-red-500/20" />
                <SkillList title="🔧 Missing Technologies" items={result.missing_technologies} color="text-amber-400" bg="bg-amber-500/10" border="border-amber-500/20" />
                <SkillList title="💡 Improvements" items={result.improvements} color="text-blue-400" bg="bg-blue-500/10" border="border-blue-500/20" />
              </div>

              {/* Formatting */}
              {result.formatting_suggestions?.length > 0 && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                  <h3 className="text-sm font-semibold text-slate-300 mb-3">📄 Formatting Suggestions</h3>
                  <ul className="space-y-2">
                    {result.formatting_suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                        <ArrowRight size={14} className="text-indigo-400 mt-0.5 shrink-0" />{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

function SkillList({ title, items, color, bg, border }) {
  if (!items?.length) return null;
  return (
    <div className={`rounded-2xl border ${border} ${bg} p-5`}>
      <h3 className={`text-sm font-semibold mb-3 ${color}`}>{title}</h3>
      <div className="flex flex-wrap gap-2">
        {items.map((s, i) => (
          <span key={i} className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-300">{s}</span>
        ))}
      </div>
    </div>
  );
}

export default ATSAnalyzer;
