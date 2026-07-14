import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { useNetwork } from '../contexts/NetworkContext';
import api from '../services/api';
import {
  Mic, MicOff, Volume2, Loader, AlertCircle,
  CheckCircle, Play, Square, RotateCcw, MessageSquare,
} from 'lucide-react';

const PHASES = { SETUP: 'SETUP', ACTIVE: 'ACTIVE', ENDED: 'ENDED' };

const getErrorMessage = (err) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => item?.msg || item).join(', ');
  if (detail && typeof detail === 'object') {
    if (typeof detail.msg === 'string') return detail.msg;
    if (typeof detail.error === 'string') return detail.error;
  }
  return err?.message || 'Something went wrong.';
};

export const VoiceInterview = () => {
  const navigate = useNavigate();
  const { fullyOnline } = useNetwork();
  const [phase, setPhase] = useState(PHASES.SETUP);
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [transcript, setTranscript] = useState([]);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [speechAnalysis, setSpeechAnalysis] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('Technical');
  const [interviewType, setInterviewType] = useState('TECHNICAL');
  const [questionIndex, setQuestionIndex] = useState(0);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioRef = useRef(null);

  const playQuestion = async (text, idx, activeSessionId = sessionId) => {
    try {
      if (recording || !activeSessionId) return;
      const res = await api.post(
        '/voice/tts',
        { text, session_id: activeSessionId, index: idx },
        { responseType: 'blob', timeout: 60000 }
      );
      const url = URL.createObjectURL(new Blob([res.data], { type: res.data.type || 'audio/mpeg' }));
      if (audioRef.current) { audioRef.current.src = url; audioRef.current.play(); }
    } catch { /* TTS optional — question shown as text */ }
  };

  const handleStart = async () => {
    if (!fullyOnline) { setError('No internet connection.'); return; }
    const token = localStorage.getItem('accessToken');
    if (!token) {
      setError('Your session has expired. Please sign in again.');
      navigate('/login');
      return;
    }
    setError('');
    try {
      const res = await api.post('/voice/start', { interview_type: interviewType, category });
      setSessionId(res.data.session_id);
      setCurrentQuestion(res.data.first_question);
      setTranscript([{ role: 'ai', text: res.data.first_question }]);
      setPhase(PHASES.ACTIVE);
      setTimeout(() => playQuestion(res.data.first_question, 0, res.data.session_id), 500);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch { setError('Microphone access denied.'); }
  };

  const stopRecording = () => {
    if (!mediaRecorderRef.current) return;
    mediaRecorderRef.current.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      await submitAudio(blob);
    };
    mediaRecorderRef.current.stop();
    mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
    setRecording(false);
  };

  const submitAudio = async (blob) => {
    setProcessing(true); setError('');
    try {
      if (!sessionId) {
        throw new Error('Voice interview session has not started yet.');
      }

      const formData = new FormData();
      const audioFile = new File([blob], 'answer.webm', { type: blob.type || 'audio/webm' });
      formData.append('audio', audioFile, audioFile.name);

      const res = await api.post(`/voice/stt/${sessionId}`, formData, {
        timeout: 120000,
      });
      const { transcript: text, speech_analysis, next_question } = res.data;

      setTranscript(prev => [
        ...prev,
        { role: 'candidate', text },
        { role: 'ai', text: next_question },
      ]);
      setSpeechAnalysis(speech_analysis);
      setCurrentQuestion(next_question);
      setQuestionIndex(prev => prev + 1);
      setTimeout(() => playQuestion(next_question, questionIndex + 1, sessionId), 300);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally { setProcessing(false); }
  };

  const handleEnd = async () => {
    setProcessing(true);
    try {
      const res = await api.post(`/voice/end/${sessionId}`);
      setSummary(res.data);
      setPhase(PHASES.ENDED);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally { setProcessing(false); }
  };

  // ── Setup ──
  if (phase === PHASES.SETUP) return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-lg">
          <div className="mb-8 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-rose-500/20 bg-rose-500/10 px-4 py-1.5 text-sm text-rose-300 mb-3">
              <Mic size={14} /> Voice AI Interview
            </div>
            <h1 className="text-3xl font-bold text-white">Voice Interview</h1>
            <p className="mt-2 text-slate-400">Speak your answers. AI listens, evaluates, and responds.</p>
          </div>

          {error && <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4"><AlertCircle size={18} className="text-red-400 shrink-0" /><p className="text-sm text-red-300">{error}</p></div>}

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">Interview Type</label>
              <div className="grid grid-cols-2 gap-2">
                {['TECHNICAL', 'HR'].map(t => (
                  <button key={t} onClick={() => setInterviewType(t)}
                    className={`rounded-xl border py-2.5 text-sm font-semibold transition-all ${interviewType === t ? 'border-rose-500/50 bg-rose-500/10 text-rose-300' : 'border-slate-700 bg-slate-800 text-slate-400 hover:border-slate-600'}`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">Category</label>
              <select value={category} onChange={e => setCategory(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white focus:border-rose-500 focus:outline-none">
                {['Technical', 'Java', 'Python', 'React', 'SQL', 'Behavioral', 'Leadership'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-300">
              ⚠️ Allow microphone access when prompted. Speak clearly for best results.
            </div>
            <button onClick={handleStart} disabled={!fullyOnline}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 py-3.5 font-semibold text-white disabled:opacity-50 hover:from-rose-500 hover:to-pink-500 transition">
              <Mic size={18} /> Start Voice Interview
            </button>
          </div>
        </div>
      </div>
    </>
  );

  // ── Active Interview ──
  if (phase === PHASES.ACTIVE) return (
    <>
      <Navbar />
      <audio ref={audioRef} className="hidden" />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
              <span className="text-sm font-semibold text-white">Voice Interview Active</span>
            </div>
            <button onClick={handleEnd} disabled={processing}
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs text-slate-300 hover:border-red-500/40 hover:text-red-300 transition">
              <Square size={12} /> End Interview
            </button>
          </div>

          {error && <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4"><AlertCircle size={18} className="text-red-400 shrink-0" /><p className="text-sm text-red-300">{error}</p></div>}

          {/* Current Question */}
          <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 mb-5">
            <div className="flex items-center gap-2 mb-3">
              <Volume2 size={16} className="text-rose-400" />
              <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">AI Question</span>
            </div>
            <p className="text-lg text-white leading-relaxed">{currentQuestion}</p>
          </div>

          {/* Record Button */}
          <div className="flex flex-col items-center gap-4 mb-6">
            {processing ? (
              <div className="flex flex-col items-center gap-2">
                <Loader size={40} className="animate-spin text-rose-400" />
                <p className="text-sm text-slate-400">Processing your answer...</p>
              </div>
            ) : recording ? (
              <button onClick={stopRecording}
                className="flex h-20 w-20 items-center justify-center rounded-full bg-red-600 shadow-lg shadow-red-500/30 hover:bg-red-500 transition animate-pulse">
                <MicOff size={32} className="text-white" />
              </button>
            ) : (
              <button onClick={startRecording}
                className="flex h-20 w-20 items-center justify-center rounded-full bg-rose-600 shadow-lg shadow-rose-500/30 hover:bg-rose-500 transition">
                <Mic size={32} className="text-white" />
              </button>
            )}
            <p className="text-xs text-slate-500">
              {recording ? 'Recording... Click to stop' : 'Click to start recording your answer'}
            </p>
          </div>

          {/* Speech Analysis */}
          {speechAnalysis && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 mb-4">
              <h3 className="text-xs font-semibold text-slate-400 mb-3 uppercase tracking-wider">Last Answer Analysis</h3>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div><p className="text-lg font-bold text-white">{speechAnalysis.words_per_minute}</p><p className="text-xs text-slate-500">WPM</p></div>
                <div><p className={`text-lg font-bold ${speechAnalysis.speaking_speed === 'Good' ? 'text-emerald-400' : 'text-amber-400'}`}>{speechAnalysis.speaking_speed}</p><p className="text-xs text-slate-500">Speed</p></div>
                <div><p className="text-lg font-bold text-rose-400">{speechAnalysis.filler_word_count}</p><p className="text-xs text-slate-500">Fillers</p></div>
              </div>
            </div>
          )}

          {/* Transcript */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 max-h-64 overflow-y-auto">
            <h3 className="text-xs font-semibold text-slate-400 mb-3 flex items-center gap-1"><MessageSquare size={12} /> Transcript</h3>
            <div className="space-y-2">
              {transcript.map((t, i) => (
                <div key={i} className={`flex gap-2 ${t.role === 'ai' ? '' : 'flex-row-reverse'}`}>
                  <div className={`max-w-[80%] rounded-xl px-3 py-2 text-xs ${t.role === 'ai' ? 'bg-slate-800 text-slate-300' : 'bg-rose-500/20 text-rose-200'}`}>
                    {t.text}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );

  // ── Summary ──
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-slate-950 py-8 px-4">
        <div className="mx-auto max-w-2xl text-center">
          <CheckCircle size={48} className="text-emerald-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Voice Interview Complete</h1>
          {summary && (
            <div className="space-y-4 mt-6">
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                  <p className="text-3xl font-black text-rose-400">{Math.round(summary.communication_score || 0)}</p>
                  <p className="text-xs text-slate-500 mt-1">Comm Score</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                  <p className="text-3xl font-black text-amber-400">{summary.filler_word_count || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">Filler Words</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
                  <p className="text-3xl font-black text-blue-400">{summary.total_turns || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">Answers</p>
                </div>
              </div>
              <button onClick={() => setPhase(PHASES.SETUP)}
                className="flex items-center gap-2 mx-auto rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300 hover:border-slate-600 transition">
                <RotateCcw size={14} /> Start New Session
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default VoiceInterview;
