import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { interviewService } from '../services/api';
import { useInterview } from '../contexts/InterviewContext';
import { Navbar } from '../components/Navbar';
import {
  Play, Loader, AlertCircle, Building2, Code2,
  Users, Shuffle, ChevronRight, Sparkles, Target,
  Brain, FileText, Zap,
} from 'lucide-react';

// ── Data ──────────────────────────────────────────────────────────

const INTERVIEW_TYPES = [
  {
    id: 'TECHNICAL',
    label: 'Technical',
    icon: Code2,
    color: 'from-blue-500 to-cyan-500',
    border: 'border-blue-500/40',
    bg: 'bg-blue-500/10',
    text: 'text-blue-300',
    desc: 'DSA, System Design, Core CS',
  },
  {
    id: 'HR',
    label: 'HR / Behavioral',
    icon: Users,
    color: 'from-emerald-500 to-teal-500',
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-300',
    desc: 'Soft skills, Leadership, Culture fit',
  },
  {
    id: 'MIXED',
    label: 'Mixed',
    icon: Shuffle,
    color: 'from-violet-500 to-purple-500',
    border: 'border-violet-500/40',
    bg: 'bg-violet-500/10',
    text: 'text-violet-300',
    desc: 'Technical + HR combined round',
  },
  {
    id: 'COMPANY',
    label: 'Company Specific',
    icon: Building2,
    color: 'from-amber-500 to-orange-500',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/10',
    text: 'text-amber-300',
    desc: 'Tailored to a specific company style',
  },
];

const COMPANIES = [
  { id: 'Google',     logo: '🔵', style: 'Algorithmic, System Design, Googleyness' },
  { id: 'Amazon',     logo: '🟠', style: 'Leadership Principles, Bar Raiser, LP stories' },
  { id: 'Microsoft',  logo: '🟦', style: 'Problem solving, Growth mindset, Culture' },
  { id: 'Meta',       logo: '🔷', style: 'Coding, System Design, Behavioral' },
  { id: 'Accenture',  logo: '🟣', style: 'Consulting, Client scenarios, Teamwork' },
  { id: 'TCS',        logo: '🔹', style: 'Core Java, SQL, HR, Aptitude' },
  { id: 'Infosys',    logo: '🟢', style: 'Technical fundamentals, HR, Puzzles' },
  { id: 'Wipro',      logo: '⚫', style: 'Aptitude, Technical, Communication' },
  { id: 'Deloitte',   logo: '🔶', style: 'Case studies, Consulting, Behavioral' },
  { id: 'Cognizant',  logo: '🔴', style: 'Technical, HR, Situational' },
  { id: 'HCL',        logo: '🟡', style: 'Core CS, Networking, HR' },
  { id: 'Capgemini',  logo: '🔵', style: 'Aptitude, Technical, Group Discussion' },
];

const CATEGORIES = {
  TECHNICAL: ['Java', 'Python', 'React', 'JavaScript', 'SQL', 'Data Structures', 'Spring Boot', 'System Design', 'Node.js', 'C++'],
  HR: ['Behavioral', 'Leadership', 'Teamwork', 'Communication', 'Conflict Resolution', 'Career Goals'],
  MIXED: ['Java', 'Python', 'React', 'SQL', 'Behavioral', 'Leadership', 'System Design'],
  COMPANY: ['Full Stack', 'Backend', 'Frontend', 'Data Science', 'DevOps', 'Mobile', 'QA'],
};

const DIFFICULTIES = [
  { id: 'EASY',   label: 'Easy',   color: 'text-emerald-400', border: 'border-emerald-500/40', bg: 'bg-emerald-500/10', desc: 'Fresher / Entry level' },
  { id: 'MEDIUM', label: 'Medium', color: 'text-amber-400',   border: 'border-amber-500/40',   bg: 'bg-amber-500/10',   desc: '1–3 years experience' },
  { id: 'HARD',   label: 'Hard',   color: 'text-red-400',     border: 'border-red-500/40',     bg: 'bg-red-500/10',     desc: 'Senior / Lead level' },
];

// ── Component ─────────────────────────────────────────────────────

export const StartInterview = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setCurrentSession, resetInterview } = useInterview();

  const defaultType = location.state?.type || 'TECHNICAL';
  const [interviewType, setInterviewType] = useState(defaultType);
  const [category, setCategory] = useState(CATEGORIES[defaultType][0]);
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [company, setCompany] = useState(COMPANIES[0].id);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTypeChange = (type) => {
    setInterviewType(type);
    setCategory(CATEGORIES[type][0]);
    setError('');
  };

  const selectedType = INTERVIEW_TYPES.find((t) => t.id === interviewType);
  const selectedDiff = DIFFICULTIES.find((d) => d.id === difficulty);
  const selectedCompany = COMPANIES.find((c) => c.id === company);

  const handleStart = async () => {
    setLoading(true);
    setError('');
    try {
      resetInterview();
      const payload = {
        interview_type: interviewType === 'COMPANY' ? 'TECHNICAL' : interviewType,
        category,
        difficulty,
      };
      if (interviewType === 'COMPANY') {
        payload.session_metadata = { company, company_mode: true };
      }
      const res = await interviewService.startInterview(payload);
      // Attach company info to session for question generation
      const sessionData = { ...res.data, company: interviewType === 'COMPANY' ? company : null };
      setCurrentSession(sessionData);
      navigate('/interview/session');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start interview. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-10 px-4">
        <div className="mx-auto max-w-3xl">

          {/* Header */}
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300 mb-4">
              <Sparkles size={14} />
              AI-Powered Interview Simulator
            </div>
            <h1 className="text-3xl font-bold text-white">Configure Your Session</h1>
            <p className="mt-2 text-slate-400">Choose your interview type, topic, and difficulty to begin.</p>
          </div>

          {error && (
            <div className="mb-6 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <AlertCircle className="shrink-0 text-red-400" size={18} />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {/* Step 1 — Interview Type */}
          <Section step="1" title="Interview Type" icon={Brain}>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {INTERVIEW_TYPES.map((type) => {
                const Icon = type.icon;
                const active = interviewType === type.id;
                return (
                  <button
                    key={type.id}
                    onClick={() => handleTypeChange(type.id)}
                    className={`group flex flex-col items-center gap-2 rounded-xl border p-4 text-center transition-all duration-200 ${
                      active
                        ? `${type.border} ${type.bg}`
                        : 'border-slate-700 bg-slate-900 hover:border-slate-600 hover:bg-slate-800'
                    }`}
                  >
                    <div className={`rounded-lg bg-gradient-to-br p-2 text-white ${type.color}`}>
                      <Icon size={18} />
                    </div>
                    <span className={`text-sm font-semibold ${active ? type.text : 'text-slate-300'}`}>
                      {type.label}
                    </span>
                    <span className="text-[11px] text-slate-500 leading-tight">{type.desc}</span>
                  </button>
                );
              })}
            </div>
          </Section>

          {/* Step 2 — Company Selector (only for COMPANY mode) */}
          {interviewType === 'COMPANY' && (
            <Section step="2" title="Select Company" icon={Building2}>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {COMPANIES.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setCompany(c.id)}
                    className={`flex items-start gap-3 rounded-xl border p-3 text-left transition-all ${
                      company === c.id
                        ? 'border-amber-500/50 bg-amber-500/10'
                        : 'border-slate-700 bg-slate-900 hover:border-slate-600 hover:bg-slate-800'
                    }`}
                  >
                    <span className="text-xl">{c.logo}</span>
                    <div>
                      <p className={`text-sm font-semibold ${company === c.id ? 'text-amber-300' : 'text-slate-200'}`}>
                        {c.id}
                      </p>
                      <p className="text-[10px] text-slate-500 leading-tight mt-0.5">{c.style}</p>
                    </div>
                  </button>
                ))}
              </div>
            </Section>
          )}

          {/* Step 3 — Category */}
          <Section step={interviewType === 'COMPANY' ? '3' : '2'} title="Topic / Category" icon={Target}>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES[interviewType].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`rounded-full border px-4 py-1.5 text-xs font-medium transition-all ${
                    category === cat
                      ? 'border-indigo-500/60 bg-indigo-500/20 text-indigo-300'
                      : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </Section>

          {/* Step 4 — Difficulty */}
          <Section step={interviewType === 'COMPANY' ? '4' : '3'} title="Difficulty Level" icon={Zap}>
            <div className="grid grid-cols-3 gap-3">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setDifficulty(d.id)}
                  className={`rounded-xl border p-4 text-center transition-all ${
                    difficulty === d.id
                      ? `${d.border} ${d.bg}`
                      : 'border-slate-700 bg-slate-900 hover:border-slate-600 hover:bg-slate-800'
                  }`}
                >
                  <p className={`text-sm font-bold ${difficulty === d.id ? d.color : 'text-slate-300'}`}>
                    {d.label}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-500">{d.desc}</p>
                </button>
              ))}
            </div>
          </Section>

          {/* Summary + Start */}
          <div className="mt-6 rounded-2xl border border-slate-700 bg-slate-900 p-5">
            <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">Session Summary</p>
            <div className="flex flex-wrap gap-3 mb-6">
              <Tag label="Type" value={interviewType === 'COMPANY' ? `${company} Interview` : selectedType?.label} color={selectedType?.text} />
              <Tag label="Topic" value={category} color="text-slate-300" />
              <Tag label="Difficulty" value={selectedDiff?.label} color={selectedDiff?.color} />
              {interviewType === 'COMPANY' && (
                <Tag label="Style" value={selectedCompany?.style} color="text-amber-300" />
              )}
            </div>

            <button
              onClick={handleStart}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 py-4 text-base font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50"
            >
              {loading ? (
                <><Loader size={20} className="animate-spin" /> Starting Session...</>
              ) : (
                <><Play size={20} /> Start Interview <ChevronRight size={18} /></>
              )}
            </button>

            <button
              onClick={() => navigate('/dashboard')}
              className="mt-3 w-full py-2.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// ── Sub-components ────────────────────────────────────────────────

function Section({ step, title, icon: Icon, children }) {
  return (
    <div className="mb-5 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-500/20 text-xs font-bold text-indigo-400">
          {step}
        </div>
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-slate-400" />
          <span className="text-sm font-semibold text-slate-200">{title}</span>
        </div>
      </div>
      {children}
    </div>
  );
}

function Tag({ label, value, color }) {
  return (
    <div className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5">
      <span className="text-xs text-slate-500">{label}:</span>
      <span className={`text-xs font-semibold ${color}`}>{value}</span>
    </div>
  );
}

export default StartInterview;
