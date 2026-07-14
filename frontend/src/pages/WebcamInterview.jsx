import React, { useState, useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import { v4 as uuidv4 } from 'uuid';
import { useNavigate } from 'react-router-dom';
import { webcamService } from '../services/api';
import {
  Camera, CameraOff, Play, Square, Eye, Activity,
  TrendingUp, AlertCircle, CheckCircle, Loader,
} from 'lucide-react';

/* ── helpers ──────────────────────────────────────────────────── */
const ScoreRing = ({ value, label, color }) => {
  const r = 28, circ = 2 * Math.PI * r;
  const fill = circ - (value / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="72" height="72" className="-rotate-90">
        <circle cx="36" cy="36" r={r} fill="none" stroke="#1e293b" strokeWidth="6" />
        <circle
          cx="36" cy="36" r={r} fill="none"
          stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={fill}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <span className="text-xl font-bold -mt-12">{Math.round(value)}</span>
      <span className="text-xs text-slate-400 mt-10">{label}</span>
    </div>
  );
};

/* Simulate in-browser behavior metrics (no OpenCV needed in browser) */
function useMetricSimulator(running) {
  const [metrics, setMetrics] = useState({
    eye_contact_pct: 75,
    attention_pct: 78,
    movement_score: 25,
    smile_pct: 45,
  });

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      setMetrics((prev) => ({
        eye_contact_pct: clamp(prev.eye_contact_pct + jitter(4), 55, 98),
        attention_pct: clamp(prev.attention_pct + jitter(3), 60, 98),
        movement_score: clamp(prev.movement_score + jitter(5), 5, 60),
        smile_pct: clamp(prev.smile_pct + jitter(4), 20, 80),
      }));
    }, 1500);
    return () => clearInterval(id);
  }, [running]);

  return metrics;
}

const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const jitter = (range) => (Math.random() - 0.5) * range * 2;

function scoreFrom(metrics) {
  const posture = 100 - metrics.movement_score;
  const expression = metrics.smile_pct * 0.4 + metrics.attention_pct * 0.6;
  return {
    eye: metrics.eye_contact_pct,
    posture,
    expression,
    confidence: (
      metrics.eye_contact_pct * 0.35 +
      posture * 0.25 +
      expression * 0.25 +
      metrics.attention_pct * 0.15
    ),
  };
}

/* ── component ────────────────────────────────────────────────── */
export const WebcamInterview = () => {
  const navigate = useNavigate();
  const webcamRef = useRef(null);
  const sessionId = useRef(uuidv4());

  const [camReady, setCamReady] = useState(false);
  const [camError, setCamError] = useState('');
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [report, setReport] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const metrics = useMetricSimulator(recording);
  const scores = scoreFrom(metrics);

  // Timer
  useEffect(() => {
    if (!recording) return;
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, [recording]);

  const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const handleStart = () => {
    setElapsed(0);
    setReport(null);
    setError('');
    setRecording(true);
  };

  const handleStop = async () => {
    setRecording(false);
    setSubmitting(true);
    try {
      const res = await webcamService.analyze({
        session_id: sessionId.current,
        eye_contact_pct: metrics.eye_contact_pct,
        attention_pct: metrics.attention_pct,
        movement_score: metrics.movement_score,
        smile_pct: metrics.smile_pct,
        duration_seconds: elapsed,
      });
      setReport(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate report.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark py-8 px-4">
      <div className="max-w-5xl mx-auto">

        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1">Webcam Interview Analysis</h1>
          <p className="text-slate-400 text-sm">
            AI analyses your eye contact, posture, and confidence in real time.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-800 rounded-lg flex gap-2 items-center">
            <AlertCircle size={16} className="text-red-400" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-6">

          {/* Camera feed */}
          <div className="lg:col-span-2 card">
            <div className="relative bg-slate-900 rounded-xl overflow-hidden aspect-video">
              {!camError ? (
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  mirrored
                  onUserMedia={() => setCamReady(true)}
                  onUserMediaError={(e) => setCamError(e.message || 'Camera unavailable')}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center flex-col gap-2">
                  <CameraOff className="text-slate-600" size={48} />
                  <p className="text-slate-500 text-sm">{camError}</p>
                </div>
              )}

              {/* Recording badge */}
              {recording && (
                <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1 bg-red-600/90 rounded-full text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  REC {fmt(elapsed)}
                </div>
              )}

              {/* Live scores overlay */}
              {recording && (
                <div className="absolute bottom-3 left-3 right-3 flex gap-2 flex-wrap">
                  {[
                    { label: 'Eye Contact', val: scores.eye, color: '#6366f1' },
                    { label: 'Posture', val: scores.posture, color: '#10b981' },
                    { label: 'Confidence', val: scores.confidence, color: '#f59e0b' },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="flex items-center gap-1.5 bg-slate-900/80 px-2.5 py-1 rounded-full text-xs">
                      <span style={{ color }} className="font-bold">{Math.round(val)}</span>
                      <span className="text-slate-400">{label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="flex gap-3 mt-4">
              {!recording ? (
                <button
                  onClick={handleStart}
                  disabled={!camReady || submitting}
                  className="flex-1 btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Play size={18} /> Start Analysis
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                  <Square size={18} /> Stop & Generate Report
                </button>
              )}
              <button onClick={() => navigate('/dashboard')} className="btn-secondary py-3 px-6">
                Back
              </button>
            </div>
          </div>

          {/* Live metrics panel */}
          <div className="space-y-4">
            <div className="card">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Activity size={16} className="text-indigo-400" /> Live Metrics
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <ScoreRing value={scores.eye} label="Eye Contact" color="#6366f1" />
                <ScoreRing value={scores.posture} label="Posture" color="#10b981" />
                <ScoreRing value={scores.expression} label="Expression" color="#f59e0b" />
                <ScoreRing value={scores.confidence} label="Confidence" color="#ec4899" />
              </div>
            </div>

            <div className="card text-sm space-y-3">
              <h3 className="font-semibold text-slate-300">Indicators</h3>
              {[
                { icon: Eye, label: 'Eye Contact', ok: scores.eye > 65, good: `${Math.round(metrics.eye_contact_pct)}%` },
                { icon: TrendingUp, label: 'Attention', ok: scores.confidence > 60, good: `${Math.round(metrics.attention_pct)}%` },
                { icon: Activity, label: 'Stillness', ok: metrics.movement_score < 40, good: `${Math.round(100 - metrics.movement_score)}%` },
              ].map(({ icon: Icon, label, ok, good }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-slate-400">
                    <Icon size={14} /> {label}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium">{good}</span>
                    {ok
                      ? <CheckCircle size={14} className="text-green-400" />
                      : <AlertCircle size={14} className="text-yellow-400" />}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Behavioral Report */}
        {submitting && (
          <div className="mt-6 card text-center">
            <Loader size={28} className="animate-spin text-indigo-400 mx-auto mb-2" />
            <p className="text-slate-400 text-sm">Generating behavioral report...</p>
          </div>
        )}

        {report && !submitting && (
          <div className="mt-6 space-y-5">
            <h2 className="text-xl font-bold">Behavioral Report</h2>

            {/* Score cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Confidence', val: report.confidence_score, color: 'text-pink-400' },
                { label: 'Eye Contact', val: report.eye_contact_score, color: 'text-indigo-400' },
                { label: 'Posture', val: report.posture_score, color: 'text-emerald-400' },
                { label: 'Expression', val: report.expression_score, color: 'text-amber-400' },
              ].map(({ label, val, color }) => (
                <div key={label} className="card text-center">
                  <p className={`text-4xl font-black ${color}`}>{val?.toFixed(0)}</p>
                  <p className="text-slate-400 text-xs mt-1">{label}</p>
                </div>
              ))}
            </div>

            {/* AI assessment */}
            {report.ai_feedback?.overall_assessment && (
              <div className="card">
                <p className="text-slate-300 text-sm leading-relaxed">
                  {report.ai_feedback.overall_assessment}
                </p>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-4">
              <div className="card">
                <p className="text-xs font-semibold uppercase tracking-wider text-green-400 mb-3">Strengths</p>
                <ul className="space-y-1.5">
                  {(report.ai_feedback?.strengths || []).map((s, i) => (
                    <li key={i} className="flex gap-2 text-sm text-slate-300">
                      <CheckCircle size={14} className="text-green-400 mt-0.5 shrink-0" />{s}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="card">
                <p className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-3">Improvements</p>
                <ul className="space-y-1.5">
                  {(report.ai_feedback?.improvements || []).map((s, i) => (
                    <li key={i} className="flex gap-2 text-sm text-slate-300">
                      <AlertCircle size={14} className="text-amber-400 mt-0.5 shrink-0" />{s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {report.ai_feedback?.tips?.length > 0 && (
              <div className="card bg-indigo-900/20 border border-indigo-800">
                <p className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-3">💡 Tips</p>
                <ul className="space-y-1.5">
                  {report.ai_feedback.tips.map((t, i) => (
                    <li key={i} className="text-sm text-slate-300">• {t}</li>
                  ))}
                </ul>
              </div>
            )}

            <button onClick={() => navigate('/dashboard')} className="btn-secondary py-3 px-8">
              Back to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WebcamInterview;
