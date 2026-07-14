import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import api from '../services/api';
import {
  Users, Search, Loader, AlertCircle, ChevronRight,
  Star, TrendingUp, Code2, FileText, Brain, X,
} from 'lucide-react';

const Badge = ({ value, label }) => {
  if (value == null) return <span className="text-xs text-slate-600">—</span>;
  const color = value >= 75 ? 'text-emerald-400' : value >= 50 ? 'text-amber-400' : 'text-red-400';
  return <span className={`text-sm font-bold ${color}`}>{Math.round(value)}<span className="text-xs text-slate-500 ml-0.5">{label}</span></span>;
};

const DecisionBadge = ({ rec }) => {
  const map = {
    STRONG_HIRE: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    HIRE: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    MAYBE: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    NO_HIRE: 'bg-red-500/20 text-red-300 border-red-500/30',
    STRONG_YES: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    YES: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    NO: 'bg-red-500/20 text-red-300 border-red-500/30',
  };
  if (!rec) return null;
  return <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${map[rec] || 'bg-slate-700 text-slate-300'}`}>{rec.replace('_', ' ')}</span>;
};

export const RecruiterDashboard = () => {
  const [candidates, setCandidates] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [decision, setDecision] = useState(null);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [note, setNote] = useState('');
  const [noteRating, setNoteRating] = useState(3);
  const [noteSaving, setNoteSaving] = useState(false);

  useEffect(() => { fetchCandidates(); }, []);

  const fetchCandidates = async (q = '') => {
    setLoading(true); setError('');
    try {
      const res = await api.get(`/recruiter/candidates?search=${q}`);
      setCandidates(res.data.candidates || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Access denied. Recruiter role required.');
    } finally { setLoading(false); }
  };

  const handleSearch = (e) => { setSearch(e.target.value); fetchCandidates(e.target.value); };

  const openProfile = async (id) => {
    setSelected(id); setProfile(null); setDecision(null); setProfileLoading(true);
    try {
      const res = await api.get(`/recruiter/candidate/${id}`);
      setProfile(res.data);
    } catch { setProfile(null); }
    finally { setProfileLoading(false); }
  };

  const generateDecision = async () => {
    setDecisionLoading(true);
    try {
      const res = await api.post(`/recruiter/hiring-decision/${selected}`);
      setDecision(res.data);
    } catch { } finally { setDecisionLoading(false); }
  };

  const saveNote = async () => {
    if (!note.trim()) return;
    setNoteSaving(true);
    try {
      await api.post('/recruiter/note', { candidate_id: selected, note, rating: noteRating });
      setNote('');
    } catch { } finally { setNoteSaving(false); }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-7xl">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs text-blue-300 mb-2">
                <Users size={12} /> Recruiter Dashboard
              </div>
              <h1 className="text-2xl font-bold text-white">Candidate Management</h1>
            </div>
          </div>

          {error && <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4"><AlertCircle size={18} className="text-red-400 shrink-0" /><p className="text-sm text-red-300">{error}</p></div>}

          <div className="grid gap-6 xl:grid-cols-[1fr_1.4fr]">
            {/* Candidate List */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <div className="relative mb-4">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input value={search} onChange={handleSearch} placeholder="Search candidates..."
                  className="w-full rounded-xl border border-slate-700 bg-slate-800 pl-9 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none" />
              </div>

              {loading ? (
                <div className="flex justify-center py-8"><Loader size={24} className="animate-spin text-slate-500" /></div>
              ) : candidates.length === 0 ? (
                <p className="text-center text-sm text-slate-500 py-8">No candidates found.</p>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {candidates.map(c => (
                    <button key={c.id} onClick={() => openProfile(c.id)}
                      className={`w-full flex items-center justify-between rounded-xl border p-3.5 text-left transition-all ${selected === c.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'}`}>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-white">{c.name}</p>
                          <DecisionBadge rec={c.hiring_recommendation} />
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">{c.email}</p>
                        <div className="flex gap-3 mt-1.5">
                          <Badge value={c.average_score != null ? c.average_score * 10 : null} label="%" />
                          <Badge value={c.ats_score} label=" ATS" />
                          <Badge value={c.github_score} label=" GH" />
                        </div>
                      </div>
                      <ChevronRight size={14} className="text-slate-600" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Candidate Profile */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              {!selected ? (
                <div className="flex flex-col items-center justify-center h-full py-16 text-center">
                  <Users size={40} className="text-slate-700 mb-3" />
                  <p className="text-slate-500 text-sm">Select a candidate to view their profile.</p>
                </div>
              ) : profileLoading ? (
                <div className="flex justify-center py-16"><Loader size={28} className="animate-spin text-slate-500" /></div>
              ) : profile ? (
                <div className="space-y-4 overflow-y-auto max-h-[700px]">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-lg font-bold text-white">{profile.user?.name}</h2>
                      <p className="text-sm text-slate-400">{profile.user?.email}</p>
                    </div>
                    {profile.enhanced_report && <DecisionBadge rec={profile.enhanced_report.hiring_recommendation} />}
                  </div>

                  {/* Score Grid */}
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    {[
                      { label: 'Interview', value: profile.enhanced_report?.overall_score, icon: Brain, color: 'text-indigo-400' },
                      { label: 'Technical', value: profile.enhanced_report?.technical_score, icon: Code2, color: 'text-blue-400' },
                      { label: 'ATS Score', value: profile.ats_report?.ats_score, icon: FileText, color: 'text-emerald-400' },
                      { label: 'GitHub', value: profile.github?.github_score, icon: TrendingUp, color: 'text-amber-400' },
                    ].map(s => {
                      const Icon = s.icon;
                      return (
                        <div key={s.label} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-center">
                          <Icon size={14} className={`mx-auto mb-1 ${s.color}`} />
                          <p className={`text-xl font-black ${s.color}`}>{s.value != null ? Math.round(s.value) : '—'}</p>
                          <p className="text-[10px] text-slate-500">{s.label}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* AI Summary */}
                  {profile.enhanced_report?.ai_summary && (
                    <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4">
                      <p className="text-xs text-slate-300">{profile.enhanced_report.ai_summary}</p>
                    </div>
                  )}

                  {/* Hiring Decision */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-slate-300">AI Hiring Decision</h3>
                      <button onClick={generateDecision} disabled={decisionLoading}
                        className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition">
                        {decisionLoading ? <Loader size={12} className="animate-spin" /> : <Brain size={12} />}
                        Generate
                      </button>
                    </div>
                    {decision && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <DecisionBadge rec={decision.decision} />
                          <span className="text-xs text-slate-400">Confidence: {decision.confidence}%</span>
                        </div>
                        <p className="text-xs text-slate-300">{decision.recommendation}</p>
                        <p className="text-xs text-slate-500">Suggested Level: {decision.suggested_role_level}</p>
                      </div>
                    )}
                  </div>

                  {/* Note */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <h3 className="text-sm font-semibold text-slate-300 mb-2">Add Note</h3>
                    <textarea value={note} onChange={e => setNote(e.target.value)} rows={3} placeholder="Write your notes..."
                      className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none" />
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex gap-1">
                        {[1,2,3,4,5].map(r => (
                          <button key={r} onClick={() => setNoteRating(r)}>
                            <Star size={14} className={r <= noteRating ? 'text-amber-400' : 'text-slate-600'} fill={r <= noteRating ? 'currentColor' : 'none'} />
                          </button>
                        ))}
                      </div>
                      <button onClick={saveNote} disabled={noteSaving || !note.trim()}
                        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50 transition">
                        {noteSaving ? 'Saving...' : 'Save Note'}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default RecruiterDashboard;
