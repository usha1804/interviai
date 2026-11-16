import React, { useEffect, useRef, useState } from 'react';
import { useNetwork } from '../contexts/NetworkContext';
import { atsService, resumeService } from '../services/api';
import {
  AlertCircle, ArrowRight, CheckCircle, Download, FileSearch, FileText,
  Loader, RefreshCw, Target, Upload, Zap,
} from 'lucide-react';

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const ALLOWED_EXTENSIONS = ['pdf', 'docx'];

const ScoreRing = ({ score, label, color }) => {
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(Math.max(Number(score) || 0, 0), 100);
  const dash = (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-1" aria-label={`${label}: ${Math.round(percentage)}%`}>
      <div className="relative">
        <svg width="82" height="82" className="-rotate-90" aria-hidden="true">
          <circle cx="41" cy="41" r={radius} fill="none" stroke="#1e293b" strokeWidth="7" />
          <circle
            cx="41" cy="41" r={radius} fill="none" stroke={color} strokeWidth="7"
            strokeDasharray={`${dash} ${circumference}`} strokeLinecap="round"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-white">
          {Math.round(percentage)}
        </span>
      </div>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
};

export const ATSAnalyzer = () => {
  const { fullyOnline } = useNetwork();
  const uploadRef = useRef(null);
  const [resume, setResume] = useState(null);
  const [resumeLoading, setResumeLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    resumeService.getLatest()
      .then(({ data }) => {
        if (active) setResume(data);
      })
      .catch((err) => {
        if (!active) return;
        if (err.response?.status !== 404) {
          setError(err.response?.data?.detail || 'Could not load your latest resume.');
        }
      })
      .finally(() => {
        if (active) setResumeLoading(false);
      });
    return () => { active = false; };
  }, []);

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError('Upload a PDF or DOCX resume.');
      return;
    }
    if (file.size === 0) {
      setError('The selected file is empty.');
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('Resume files must be 5 MB or smaller.');
      return;
    }

    setUploading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await resumeService.upload(formData);
      if (data.extraction_status !== 'completed' || !data.resume_text?.trim()) {
        throw new Error('The uploaded resume did not contain extractable text. Try a searchable PDF or DOCX.');
      }
      setResume(data);
      setResult(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Resume upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!resume?.resume_text?.trim()) {
      setError('Upload a resume with extractable text before analyzing.');
      return;
    }
    if (!jdText.trim()) {
      setError('Please paste a job description.');
      return;
    }
    if (!fullyOnline) {
      setError('No internet connection. Reconnect and try again.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    try {
      const { data } = await atsService.analyze({
        resume_id: resume.id,
        jd_text: jdText.trim(),
      });
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!result?.report_id) return;
    try {
      const { data } = await atsService.downloadPdf(result.report_id);
      const url = URL.createObjectURL(new Blob([data], { type: 'application/pdf' }));
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `ats_report_${result.report_id}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'PDF download failed.');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300">
            <FileSearch size={14} /> ATS Resume Analyzer
          </div>
          <h1 className="text-3xl font-bold text-white">Check Your Resume Score</h1>
          <p className="mt-2 text-slate-400">Compare your uploaded resume with a specific job description.</p>
        </header>

        {error && (
          <div role="alert" className="mb-5 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
            <AlertCircle size={18} className="shrink-0 text-red-400" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <div className="rounded-xl bg-indigo-500/10 p-3 text-indigo-300">
                <FileText size={22} />
              </div>
              <div className="min-w-0">
                <h2 className="font-semibold text-white">Your resume</h2>
                {resumeLoading ? (
                  <p className="mt-1 flex items-center gap-2 text-sm text-slate-400">
                    <Loader size={14} className="animate-spin" /> Loading your latest upload...
                  </p>
                ) : resume ? (
                  <>
                    <p className="truncate text-sm text-slate-300">{resume.file_name}</p>
                    <p className="mt-1 flex items-center gap-1.5 text-xs text-emerald-400">
                      <CheckCircle size={13} /> Text extracted and ready to analyze
                    </p>
                  </>
                ) : (
                  <p className="mt-1 text-sm text-slate-400">No resume with extracted text found.</p>
                )}
              </div>
            </div>
            <input
              ref={uploadRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={handleUpload}
            />
            <button
              type="button"
              onClick={() => uploadRef.current?.click()}
              disabled={resumeLoading || uploading}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-indigo-500/40 bg-indigo-500/10 px-4 py-3 text-sm font-semibold text-indigo-200 transition hover:bg-indigo-500/20 disabled:opacity-50"
            >
              {uploading ? <Loader size={17} className="animate-spin" /> : resume ? <RefreshCw size={17} /> : <Upload size={17} />}
              {uploading ? 'Uploading & extracting...' : resume ? 'Replace Resume' : 'Upload Resume'}
            </button>
          </div>
          {!resumeLoading && !resume && (
            <p className="mt-3 text-xs text-slate-500">PDF or DOCX, up to 5 MB. Scanned/image-only PDFs need OCR before upload.</p>
          )}
        </section>

        <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <label htmlFor="job-description" className="mb-2 block text-sm font-semibold text-slate-300">
            Job Description
          </label>
          <textarea
            id="job-description"
            value={jdText}
            onChange={(event) => setJdText(event.target.value)}
            placeholder="Paste the full job description here..."
            rows={8}
            className="w-full resize-y rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading || uploading || resumeLoading || !resume?.resume_text?.trim() || !jdText.trim() || !fullyOnline}
            className="mt-4 flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 font-semibold text-white transition hover:from-indigo-500 hover:to-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? <><Loader size={18} className="animate-spin" /> Analyzing Resume...</> : <><Zap size={18} /> Analyze Resume</>}
          </button>
          <p className="mt-3 text-xs text-slate-500">
            The score is an estimate based on keyword matching and AI-assisted review. It is not a guaranteed score from an actual ATS provider.
          </p>
        </section>

        {result && (
          <div className="space-y-5">
            <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-white">ATS Compatibility Estimate</h2>
                  <p className="mt-1 text-xs text-slate-400">For {resume?.file_name}</p>
                </div>
                {result.has_pdf && (
                  <button
                    type="button"
                    onClick={handleDownload}
                    className="inline-flex items-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-sm text-indigo-300 transition hover:bg-indigo-500/20"
                  >
                    <Download size={14} /> Download PDF
                  </button>
                )}
              </div>
              <div className="flex flex-wrap justify-around gap-6">
                <ScoreRing score={result.ats_score} label="ATS Match" color="#818cf8" />
                <ScoreRing score={result.keyword_match_pct} label="Keyword Match" color="#10b981" />
                <ScoreRing score={result.skills_match_pct} label="Skills Match" color="#f59e0b" />
                <ScoreRing score={result.experience_match_pct} label="Experience" color="#38bdf8" />
              </div>
              {result.ai_summary && (
                <p className="mt-6 rounded-xl border border-slate-700 bg-slate-800/50 p-4 text-sm leading-6 text-slate-300">
                  {result.ai_summary}
                </p>
              )}
            </section>

            <section className="grid gap-4 sm:grid-cols-3">
              <MetricCard title="Experience Match" score={result.experience_match_pct} />
              <MetricCard title="Education Match" score={result.education_match_pct} />
              <MetricCard title="Project Relevance" score={result.project_match_pct} />
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <AnalysisList title="Matched Skills" items={result.matching_skills} color="text-emerald-300" />
              <AnalysisList title="Missing Skills" items={result.missing_skills} color="text-amber-300" />
              <AnalysisList title="Missing Required Skills" items={result.missing_required_skills} color="text-rose-300" />
              <AnalysisList title="Missing Technologies" items={result.missing_technologies} color="text-orange-300" />
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <KeywordPanel
                title="Matched Keywords"
                items={result.matched_keywords}
                total={result.job_keywords?.length || 0}
                color="text-emerald-300"
                percentage={result.keyword_match_pct}
              />
              <AnalysisList title="Recommended Keywords" items={result.recommended_keywords} color="text-indigo-300" />
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <AnalysisList title="Resume Strengths" items={result.strengths} color="text-emerald-300" />
              <AnalysisList title="Areas to Improve" items={result.weaknesses} color="text-rose-300" />
              <AnalysisList title="Improvement Suggestions" items={result.improvements} color="text-sky-300" />
              <AnalysisList title="Formatting Suggestions" items={result.formatting_suggestions} color="text-violet-300" />
            </section>
          </div>
        )}
      </div>
    </div>
  );
};

function MetricCard({ title, score }) {
  const percentage = Math.round(Number(score) || 0);
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-slate-300">{title}</span>
        <span className="font-semibold text-white">{percentage}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }} />
      </div>
    </div>
  );
}

function AnalysisList({ title, items, color }) {
  const values = Array.isArray(items) ? items : [];
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className={`mb-3 flex items-center gap-2 text-sm font-semibold ${color}`}>
        <Target size={15} /> {title}
      </h3>
      {values.length ? (
        <ul className="space-y-2">
          {values.map((item, index) => (
            <li key={`${item}-${index}`} className="flex items-start gap-2 text-sm text-slate-300">
              <ArrowRight size={14} className="mt-0.5 shrink-0 text-slate-500" /> {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">No items identified.</p>
      )}
    </div>
  );
}

function KeywordPanel({ title, items, total, color, percentage }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className={`text-sm font-semibold ${color}`}>{title}</h3>
        <span className="text-xs text-slate-400">{items?.length || 0} / {total} ({Math.round(percentage || 0)}%)</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {(items || []).length ? items.map((item) => (
          <span key={item} className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200">
            {item}
          </span>
        )) : <p className="text-sm text-slate-500">No matching keywords found.</p>}
      </div>
    </div>
  );
}

export default ATSAnalyzer;
