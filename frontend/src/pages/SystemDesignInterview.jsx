import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { useNetwork } from '../contexts/NetworkContext';
import api from '../services/api';
import {
  Server, Loader, AlertCircle, ChevronRight,
  CheckCircle, Send, BarChart3, ArrowLeft,
} from 'lucide-react';

const TOPICS = [
  { id: 'URL Shortener',        icon: '🔗', desc: 'Design bit.ly / TinyURL' },
  { id: 'WhatsApp',             icon: '💬', desc: 'Real-time messaging at scale' },
  { id: 'Uber',                 icon: '🚗', desc: 'Ride-sharing platform' },
  { id: 'YouTube',              icon: '▶️',  desc: 'Video streaming & CDN' },
  { id: 'Netflix',              icon: '🎬', desc: 'Streaming + recommendations' },
  { id: 'Instagram',            icon: '📸', desc: 'Photo sharing social network' },
  { id: 'Food Delivery',        icon: '🍕', desc: 'Swiggy / Zomato clone' },
  { id: 'Chat Application',     icon: '💭', desc: 'Scalable chat system' },
  { id: 'Inventory Management', icon: '📦', desc: 'E-commerce inventory' },
  { id: 'Microservices',        icon: '⚙️',  desc: 'Microservices architecture' },
];

const PHASES = { SELECT: 'SELECT', INTERVIEW: 'INTERVIEW', REPORT: 'REPORT' };

export const SystemDesignInterview = () => {
  const { fullyOnline } = useNetwork();
  const [phase, setPhase] = useState(PHASES.SELECT);
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState('');
  const [evaluations, setEvaluations] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleStart = async () => {
    if (!topic) { setError('Select a topic.'); return; }
    setLoading(true); setError('');
    try {
      const res = await api.post('/system-design/start', { topic, difficulty });
      setSessionId(res.data.session_id);
      setQuestions(res.data.questions || []);
      setPhase(PHASES.INTERVIEW);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start session.');
    } finally { setLoading(false); }
  };

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) { setError('Please write your answer.'); return; }
    setSubmitting(true); setError('');
    try {
      const res = await api.post('/system-design/submit-answer', {
        session_id: sessionId,
        question_index: currentIdx,
        answer,
      });
      setEvaluations(prev => [...prev, { ...res.data.evaluation, question: questions[currentIdx]?.question }]);
      setAnswer('');
      if (currentIdx + 1 < questions.length) {
        setCurrentIdx(prev => prev + 1);
      } else {
        // End session
        const endRes = await api.post(`/system-design/end/${sessionId}`);
        setReport(endRes.data.report);
        setPhase(PHASES.REPORT);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed.');
    } finally { setSubmitting(false); }
  };

  // ── Topic Selection ──
  if (phase === PHASES.SELECT) return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-sm text-violet-300 mb-3">
              <Server size={14} /> System Design Interview
            </div>
            <h1 className="text-3xl font-bold text-white">System Design Round</h1>
            <p className="mt-2 text-slate-400">Choose a system to design. AI will ask progressive architecture questions.</p>
          </div>

          {error && <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4"><AlertCircle size={18} className="text-red-400 shrink-0" /><p className="text-sm text-red-300">{error}</p></div>}

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 mb-6">
            {TOPICS.map(t => (
              <button key={t.id} onClick={() => setTopic(t.id)}
                className={`flex flex-col items-center gap-2 rounded-xl border p-4 text-center transition-all ${topic === t.id ? 'border-violet-500/50 bg-violet-500/10' : 'border-slate-700 bg-slate-900 hover:border-slate-600'}`}>
                <span className="text-2xl">{t.icon}</span>
                <span className={`text-xs font-semibold ${topic === t.id ? 'text-violet-300' : 'text-slate-300'}`}>{t.id}</span>
                <span className="text-[10px] text-slate-500">{t.desc}</span>
              </button>
            ))}
          </div>

          <div className="flex gap-3 mb-6">
            {['EASY', 'MEDIUM', 'HARD'].map(d => (
              <button key={d} onClick={() => setDifficulty(d)}
                className={`rounded-xl border px-5 py-2.5 text-sm font-semibold transition-all ${difficulty === d ? 'border-violet-500/50 bg-violet-500/10 text-violet-300' : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-600'}`}>
                {d}
              </button>
            ))}
          </div>

          <button onClick={handleStart} disabled={loading || !topic || !fullyOnline}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 px-8 py-3.5 font-semibold text-white disabled:opacity-50 hover:from-violet-500 hover:to-purple-500 transition">
            {loading ? <><Loader size={18} className="animate-spin" /> Generating Questions...</> : <><Server size={18} /> Start System Design</>}
          </button>
        </div>
      </div>
    </>
  );

  // ── Interview Phase ──
  if (phase === PHASES.INTERVIEW) {
    const q = questions[currentIdx];
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-slate-950 py-8 px-4">
          <div className="mx-auto max-w-3xl">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Server size={14} className="text-violet-400" />
                <span className="font-semibold text-white">{topic}</span>
                <span>·</span><span>{difficulty}</span>
              </div>
              <span className="text-sm text-slate-500">Question {currentIdx + 1} / {questions.length}</span>
            </div>

            <div className="mb-2 h-1.5 rounded-full bg-slate-800">
              <div className="h-1.5 rounded-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all"
                style={{ width: `${((currentIdx) / questions.length) * 100}%` }} />
            </div>

            {error && <div className="my-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4"><AlertCircle size={18} className="text-red-400 shrink-0" /><p className="text-sm text-red-300">{error}</p></div>}

            <div className="mt-6 rounded-2xl border border-violet-500/20 bg-violet-500/5 p-6 mb-5">
              <p className="text-xs font-semibold text-violet-400 mb-2 uppercase tracking-wider">{q?.category}</p>
              <p className="text-lg text-white leading-relaxed">{q?.question}</p>
              {q?.follow_up && <p className="mt-3 text-sm text-slate-400 italic">Follow-up: {q.follow_up}</p>}
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <label className="block text-sm font-semibold text-slate-300 mb-2">Your Architecture Answer</label>
              <textarea value={answer} onChange={e => setAnswer(e.target.value)}
                placeholder="Describe your architecture, components, data flow, scaling strategy..."
                rows={8}
                className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-violet-500 focus:outline-none resize-none" />
              <button onClick={handleSubmitAnswer} disabled={submitting || !answer.trim() || !fullyOnline}
                className="mt-4 flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 px-6 py-3 font-semibold text-white disabled:opacity-50 transition hover:from-violet-500 hover:to-purple-500">
                {submitting ? <><Loader size={18} className="animate-spin" /> Evaluating...</> : <><Send size={18} /> {currentIdx + 1 < questions.length ? 'Submit & Next' : 'Submit & Finish'}</>}
              </button>
            </div>

            {evaluations.length > 0 && (
              <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">Previous Evaluations</h3>
                {evaluations.map((ev, i) => (
                  <div key={i} className="mb-3 rounded-xl border border-slate-700 bg-slate-800/50 p-4">
                    <p className="text-xs text-slate-500 mb-2">Q{i + 1}: {ev.question?.slice(0, 80)}...</p>
                    <div className="flex gap-4 text-xs">
                      <span className="text-blue-400">Arch: {ev.architecture_score}/10</span>
                      <span className="text-emerald-400">Scale: {ev.scalability_score}/10</span>
                      <span className="text-amber-400">Trade-offs: {ev.tradeoffs_score}/10</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </>
    );
  }

  // ── Report Phase ──
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-3xl">
          <div className="text-center mb-8">
            <CheckCircle size={48} className="text-emerald-400 mx-auto mb-3" />
            <h1 className="text-2xl font-bold text-white">System Design Complete</h1>
            <p className="text-slate-400 mt-1">Topic: {topic}</p>
          </div>

          {report && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { label: 'Overall', value: report.overall_score, color: 'text-indigo-400' },
                  { label: 'Architecture', value: report.architecture_score, color: 'text-blue-400' },
                  { label: 'Scalability', value: report.scalability_score, color: 'text-emerald-400' },
                  { label: 'Trade-offs', value: report.tradeoffs_score, color: 'text-amber-400' },
                ].map(s => (
                  <div key={s.label} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-center">
                    <p className={`text-3xl font-black ${s.color}`}>{Math.round(s.value || 0)}</p>
                    <p className="text-xs text-slate-500 mt-1">{s.label}</p>
                  </div>
                ))}
              </div>

              {report.ai_summary && (
                <div className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5">
                  <p className="text-sm text-slate-300">{report.ai_summary}</p>
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                {report.strengths?.length > 0 && (
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                    <h3 className="text-sm font-semibold text-emerald-400 mb-2">Strengths</h3>
                    {report.strengths.map((s, i) => <p key={i} className="text-xs text-slate-400">• {s}</p>)}
                  </div>
                )}
                {report.topics_to_study?.length > 0 && (
                  <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
                    <h3 className="text-sm font-semibold text-amber-400 mb-2">Study These Topics</h3>
                    {report.topics_to_study.map((t, i) => <p key={i} className="text-xs text-slate-400">• {t}</p>)}
                  </div>
                )}
              </div>

              <button onClick={() => { setPhase(PHASES.SELECT); setTopic(''); setQuestions([]); setEvaluations([]); setReport(null); setCurrentIdx(0); }}
                className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:border-slate-600 transition">
                <ArrowLeft size={14} /> Try Another Topic
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default SystemDesignInterview;
