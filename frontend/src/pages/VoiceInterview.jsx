import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNetwork } from '../contexts/NetworkContext';
import { voiceService } from '../services/api';
import {
  AlertCircle, CheckCircle, Loader, MessageSquare, Mic, MicOff,
  Play, RotateCcw, Square, Volume2,
} from 'lucide-react';

const PHASES = { SETUP: 'SETUP', ACTIVE: 'ACTIVE', ENDED: 'ENDED' };
const TOTAL_QUESTIONS = 5;
const ACTIVE_SESSION_KEY = 'activeVoiceInterviewSessionId';

const getErrorMessage = (err) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => item?.msg || item).join(', ');
  return err?.message || 'Something went wrong.';
};

const getSupportedMimeType = () => {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
  return candidates.find(type => MediaRecorder.isTypeSupported?.(type)) || '';
};

const getAudioExtension = (mimeType) => {
  if (mimeType.includes('ogg')) return 'ogg';
  if (mimeType.includes('mp4')) return 'mp4';
  if (mimeType.includes('wav')) return 'wav';
  return 'webm';
};

export const VoiceInterview = () => {
  const navigate = useNavigate();
  const { fullyOnline } = useNetwork();
  const [phase, setPhase] = useState(PHASES.SETUP);
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [currentQuestionId, setCurrentQuestionId] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [recordingUrl, setRecordingUrl] = useState('');
  const [microphoneState, setMicrophoneState] = useState('not requested');
  const [speechAnalysis, setSpeechAnalysis] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('Technical');
  const [interviewType, setInterviewType] = useState('TECHNICAL');
  const [questionNumber, setQuestionNumber] = useState(1);
  const [interviewReadyToFinish, setInterviewReadyToFinish] = useState(false);
  const [needsEvaluationRetry, setNeedsEvaluationRetry] = useState(false);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const recordingStartedAtRef = useRef(0);
  const submitLockRef = useRef(false);
  const cancelRecordingRef = useRef(false);
  const audioRef = useRef(null);

  useEffect(() => {
    if (!recordedAudio) {
      setRecordingUrl('');
      return undefined;
    }
    const url = URL.createObjectURL(recordedAudio);
    setRecordingUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [recordedAudio]);

  useEffect(() => () => {
    if (timerRef.current) clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach(track => track.stop());
    if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop();
  }, []);

  useEffect(() => {
    const savedSessionId = localStorage.getItem(ACTIVE_SESSION_KEY);
    if (!savedSessionId || !localStorage.getItem('accessToken')) return undefined;
    let cancelled = false;
    setProcessing(true);
    voiceService.getSession(savedSessionId).then(({ data }) => {
      if (cancelled) return;
      setSessionId(data.session_id);
      setTranscript(data.transcript || []);
      setCurrentQuestion(data.current_question || '');
      setCurrentQuestionId(data.current_question_id || null);
      setQuestionNumber(data.question_number || 1);
      setNeedsEvaluationRetry(Boolean(data.evaluation_pending));
      setInterviewReadyToFinish(
        !data.completed && !data.current_question && !data.evaluation_pending
        && (data.transcript || []).filter(turn => turn.role === 'candidate').length >= TOTAL_QUESTIONS,
      );
      if (data.completed) {
        setSummary(data.summary);
        setPhase(PHASES.ENDED);
        localStorage.removeItem(ACTIVE_SESSION_KEY);
      } else {
        setPhase(PHASES.ACTIVE);
        if (data.current_question) {
          setTimeout(() => playQuestion(data.current_question, data.question_number || 1, data.session_id), 300);
        }
      }
    }).catch(err => {
      if (cancelled) return;
      localStorage.removeItem(ACTIVE_SESSION_KEY);
      if (err?.response?.status !== 404) setError(`Could not restore the saved interview: ${getErrorMessage(err)}`);
    }).finally(() => {
      if (!cancelled) setProcessing(false);
    });
    return () => { cancelled = true; };
  }, []);

  const releaseMicrophone = () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
  };

  const playQuestion = async (text, index, activeSessionId = sessionId) => {
    if (!text || !activeSessionId || !audioRef.current) return;
    try {
      const response = await voiceService.tts({ text, session_id: activeSessionId, index });
      const url = URL.createObjectURL(new Blob([response.data], { type: response.data.type || 'audio/mpeg' }));
      audioRef.current.src = url;
      audioRef.current.onended = () => URL.revokeObjectURL(url);
      await audioRef.current.play();
    } catch {
      // The question remains available as text when optional TTS is unavailable.
    }
  };

  const handleStart = async () => {
    if (!fullyOnline) {
      setError('No internet connection.');
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('This browser does not support microphone recording. Please use a current version of Chrome, Edge, or Firefox.');
      return;
    }
    if (!localStorage.getItem('accessToken')) {
      setError('Your session has expired. Please sign in again.');
      navigate('/login');
      return;
    }

    setError('');
    setProcessing(true);
    try {
      setMicrophoneState('requesting permission');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setMicrophoneState('permission granted');

      const response = await voiceService.start({ interview_type: interviewType, category });
      const firstQuestion = response.data.first_question;
      if (!firstQuestion?.trim()) throw new Error('The server did not return a valid interview question.');
      setSessionId(response.data.session_id);
      setCurrentQuestionId(response.data.current_question_id);
      localStorage.setItem(ACTIVE_SESSION_KEY, String(response.data.session_id));
      setCurrentQuestion(firstQuestion);
      setTranscript([{
        role: 'ai',
        text: firstQuestion,
        question_id: response.data.current_question_id,
        question_number: response.data.question_number || 1,
      }]);
      setQuestionNumber(response.data.question_number || 1);
      setPhase(PHASES.ACTIVE);
      setTimeout(() => playQuestion(firstQuestion, 0, response.data.session_id), 300);
    } catch (err) {
      releaseMicrophone();
      setMicrophoneState('permission unavailable');
      if (err?.name === 'NotAllowedError' || err?.name === 'SecurityError') {
        setError('Microphone access was denied. Allow microphone access in your browser settings, then try again.');
      } else if (err?.name === 'NotFoundError' || err?.name === 'DevicesNotFoundError') {
        setError('No microphone was found. Connect a microphone and try again.');
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setProcessing(false);
    }
  };

  const startRecording = async () => {
    if (processing || recording) return;
    setError('');
    if (typeof MediaRecorder === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setError('This browser does not support audio recording.');
      return;
    }
    try {
      const stream = streamRef.current || await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = getSupportedMimeType();
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      chunksRef.current = [];
      cancelRecordingRef.current = false;
      recorder.ondataavailable = event => {
        if (event.data?.size) chunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        if (timerRef.current) clearInterval(timerRef.current);
        setError('Recording failed. Check your microphone and try again.');
        releaseMicrophone();
        setRecording(false);
      };
      recorder.onstop = () => {
        if (timerRef.current) clearInterval(timerRef.current);
        const type = recorder.mimeType || mimeType || chunksRef.current[0]?.type || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type });
        chunksRef.current = [];
        releaseMicrophone();
        if (!cancelRecordingRef.current) {
          if (blob.size) setRecordedAudio(blob);
          else setError('No audio was recorded. Please try again.');
        }
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      recordingStartedAtRef.current = Date.now();
      setRecordingSeconds(0);
      timerRef.current = setInterval(
        () => setRecordingSeconds(Math.floor((Date.now() - recordingStartedAtRef.current) / 1000)),
        500,
      );
      setRecording(true);
      setMicrophoneState('recording');
    } catch (err) {
      releaseMicrophone();
      if (err?.name === 'NotAllowedError' || err?.name === 'SecurityError') {
        setError('Microphone access was denied. Allow microphone access to record your answer.');
      } else if (err?.name === 'NotFoundError' || err?.name === 'DevicesNotFoundError') {
        setError('No microphone was found. Connect a microphone and try again.');
      } else {
        setError(`Could not start recording: ${getErrorMessage(err)}`);
      }
    }
  };

  const stopRecording = (cancel = false) => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== 'recording') return;
    cancelRecordingRef.current = cancel;
    recorder.stop();
    setRecording(false);
    setMicrophoneState('permission granted');
  };

  const applyQuestionResponse = (data) => {
    if (data.transcript) {
      setTranscript(prev => {
        if (data.answered_question_id && prev.some(turn => turn.role === 'candidate' && turn.question_id === data.answered_question_id)) {
          return prev;
        }
        return [...prev, {
          role: 'candidate',
          text: data.transcript,
          question_id: data.answered_question_id,
        }];
      });
    }
    if (data.speech_analysis) setSpeechAnalysis(data.speech_analysis);
    if (data.completed) {
      setCurrentQuestion('');
      setCurrentQuestionId(null);
      setInterviewReadyToFinish(true);
      return;
    }
    if (data.next_question) {
      setCurrentQuestion(data.next_question);
      setCurrentQuestionId(data.current_question_id);
      setQuestionNumber(data.question_number || questionNumber + 1);
      setInterviewReadyToFinish(false);
      setTranscript(prev => {
        if (prev.some(turn => turn.role === 'ai' && turn.question_id === data.current_question_id)) return prev;
        return [...prev, {
          role: 'ai',
          text: data.next_question,
          question_id: data.current_question_id,
          question_number: data.question_number || questionNumber + 1,
        }];
      });
      setTimeout(() => playQuestion(data.next_question, data.question_number || questionNumber + 1), 300);
    } else if (data.next_question_error) {
      setCurrentQuestion('');
      setCurrentQuestionId(null);
      setError(data.next_question_error);
    }
  };

  const refreshSessionAfterConflict = async (submittedQuestionId) => {
    const { data } = await voiceService.getSession(sessionId);
    setTranscript(data.transcript || []);
    setCurrentQuestion(data.current_question || '');
    setCurrentQuestionId(data.current_question_id || null);
    setQuestionNumber(data.question_number || 1);
    setNeedsEvaluationRetry(Boolean(data.evaluation_pending));
    const alreadySaved = (data.transcript || []).some(
      turn => turn.role === 'candidate' && turn.question_id === submittedQuestionId,
    );
    if (alreadySaved) {
      setRecordedAudio(null);
      setError('This answer was already saved. The current question has been restored.');
    } else {
      setError('This question is already being processed. Wait briefly, then retry if needed.');
    }
  };

  const submitAudio = async () => {
    if (submitLockRef.current || processing) return;
    if (!recordedAudio?.size) {
      setError('No audio recorded. Record an answer before submitting.');
      return;
    }
    if (!sessionId) {
      setError('Voice interview session has not started yet.');
      return;
    }
    submitLockRef.current = true;
    setProcessing(true);
    setError('');
    try {
      const type = recordedAudio.type || 'audio/webm';
      const formData = new FormData();
      formData.append('audio', recordedAudio, `answer.${getAudioExtension(type)}`);
      formData.append('question_id', currentQuestionId);
      const response = await voiceService.stt(sessionId, formData);
      setSpeechAnalysis(response.data.speech_analysis);
      setNeedsEvaluationRetry(false);
      setRecordedAudio(null);
      applyQuestionResponse(response.data);
    } catch (err) {
      if ([429, 503].includes(err?.response?.status) && err?.response?.data?.detail?.includes('transcript was saved')) {
        setNeedsEvaluationRetry(true);
      }
      if (err?.response?.status === 409 && currentQuestionId) {
        try {
          await refreshSessionAfterConflict(currentQuestionId);
        } catch {
          setError(getErrorMessage(err));
        }
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setProcessing(false);
      submitLockRef.current = false;
    }
  };

  const retryEvaluation = async () => {
    if (!sessionId || processing) return;
    setProcessing(true);
    setError('');
    try {
      const response = await voiceService.retryEvaluation(sessionId);
      setNeedsEvaluationRetry(false);
      setRecordedAudio(null);
      applyQuestionResponse(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setProcessing(false);
    }
  };

  const retryNextQuestion = async () => {
    if (!sessionId || processing) return;
    setProcessing(true);
    setError('');
    try {
      const response = await voiceService.next(sessionId);
      applyQuestionResponse(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setProcessing(false);
    }
  };

  const handleEnd = async () => {
    if (!sessionId || processing) return;
    setProcessing(true);
    setError('');
    try {
      const response = await voiceService.end(sessionId);
      setSummary(response.data);
      setPhase(PHASES.ENDED);
      localStorage.removeItem(ACTIVE_SESSION_KEY);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setProcessing(false);
    }
  };

  const reset = () => {
    releaseMicrophone();
    setPhase(PHASES.SETUP);
    setSessionId(null);
    setCurrentQuestion('');
    setCurrentQuestionId(null);
    setTranscript([]);
    setRecordedAudio(null);
    setSpeechAnalysis(null);
    setSummary(null);
    setQuestionNumber(1);
    setInterviewReadyToFinish(false);
    setNeedsEvaluationRetry(false);
    setError('');
    localStorage.removeItem(ACTIVE_SESSION_KEY);
  };

  if (phase === PHASES.SETUP) return (
    <div className="min-h-screen bg-slate-950 px-4 py-8">
      <div className="mx-auto max-w-lg">
        <header className="mb-8 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-rose-500/20 bg-rose-500/10 px-4 py-1.5 text-sm text-rose-300">
            <Mic size={14} /> Voice AI Interview
          </div>
          <h1 className="text-3xl font-bold text-white">Voice Interview</h1>
          <p className="mt-2 text-slate-400">Speak your answers. AI transcribes and evaluates them.</p>
        </header>
        {error && <ErrorBanner message={error} />}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Interview Type</label>
            <div className="grid grid-cols-2 gap-2">
              {['TECHNICAL', 'HR'].map(type => (
                <button key={type} onClick={() => setInterviewType(type)}
                  className={`rounded-xl border py-2.5 text-sm font-semibold ${interviewType === type ? 'border-rose-500/50 bg-rose-500/10 text-rose-300' : 'border-slate-700 bg-slate-800 text-slate-400'}`}>
                  {type}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-300">Category</label>
            <select value={category} onChange={event => setCategory(event.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white">
              {['Technical', 'Java', 'Python', 'React', 'SQL', 'Behavioral', 'Leadership'].map(value => <option key={value}>{value}</option>)}
            </select>
          </div>
          <p className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-300">
            Microphone access is requested when you start. Starting the interview does not upload an audio file.
          </p>
          <button onClick={handleStart} disabled={!fullyOnline || processing}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 py-3.5 font-semibold text-white disabled:opacity-50">
            {processing ? <Loader size={18} className="animate-spin" /> : <Mic size={18} />}
            {processing ? 'Starting interview...' : 'Start Voice Interview'}
          </button>
          <p className="text-center text-xs text-slate-500">Microphone: {microphoneState}</p>
        </div>
      </div>
    </div>
  );

  if (phase === PHASES.ACTIVE) return (
    <div className="min-h-screen bg-slate-950 px-4 py-8">
      <audio ref={audioRef} className="hidden" />
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-white">Voice Interview</p>
            <p className="text-xs text-slate-400">Question {Math.min(questionNumber, TOTAL_QUESTIONS)} of {TOTAL_QUESTIONS}</p>
          </div>
          <button onClick={handleEnd} disabled={processing || recording} className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs text-slate-300 disabled:opacity-50">
            <Square size={12} /> Finish Interview
          </button>
        </div>
        <div className="mb-6 h-2 overflow-hidden rounded-full bg-slate-800">
          <div className="h-full bg-rose-500 transition-all" style={{ width: `${Math.min((questionNumber / TOTAL_QUESTIONS) * 100, 100)}%` }} />
        </div>
        {error && <ErrorBanner message={error} />}

        {currentQuestion && <section className="mb-5 rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6">
          <div className="mb-3 flex items-center gap-2">
            <Volume2 size={16} className="text-rose-400" />
            <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">AI Question</span>
          </div>
          <p className="text-lg leading-relaxed text-white">{currentQuestion}</p>
        </section>}

        {interviewReadyToFinish ? (
          <button onClick={handleEnd} disabled={processing} className="mb-6 w-full rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white disabled:opacity-50">
            {processing ? 'Preparing report...' : 'Finish Interview and View Report'}
          </button>
        ) : (
          <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <span className={`text-sm font-medium ${recording ? 'text-red-400' : 'text-slate-400'}`}>
                {recording ? `● Recording · ${Math.floor(recordingSeconds / 60)}:${String(recordingSeconds % 60).padStart(2, '0')}` : 'Microphone ready'}
              </span>
              <span className="text-xs text-slate-500">Permission: {microphoneState}</span>
            </div>
            <div className="flex flex-wrap justify-center gap-3">
              {!recording ? (
                <button onClick={startRecording} disabled={processing} className="flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-3 font-semibold text-white disabled:opacity-50">
                  <Mic size={18} /> Start Recording
                </button>
              ) : <>
                <button onClick={() => stopRecording(false)} className="flex items-center gap-2 rounded-xl bg-red-600 px-5 py-3 font-semibold text-white">
                  <Square size={16} /> Stop Recording
                </button>
                <button onClick={() => stopRecording(true)} className="rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300">Cancel recording</button>
              </>}
              {recordedAudio && !recording && <>
                <button onClick={startRecording} disabled={processing} className="flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-200 disabled:opacity-50">
                  <RotateCcw size={16} /> Re-record
                </button>
                <button onClick={submitAudio} disabled={processing || needsEvaluationRetry} className="flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 font-semibold text-white disabled:opacity-50">
                  {processing ? <Loader size={16} className="animate-spin" /> : <Play size={16} />} Submit Answer
                </button>
              </>}
            </div>
            {recordingUrl && <div className="mt-4">
              <p className="mb-2 text-xs text-slate-400">Preview recording before submitting</p>
              <audio className="w-full" controls src={recordingUrl}>Audio playback is not supported by this browser.</audio>
            </div>}
            {needsEvaluationRetry && <button onClick={retryEvaluation} disabled={processing} className="mt-4 w-full rounded-xl border border-amber-500/40 px-4 py-3 text-sm text-amber-300 disabled:opacity-50">
              Retry AI evaluation (transcript already saved)
            </button>}
            {!currentQuestion && !interviewReadyToFinish && <button onClick={retryNextQuestion} disabled={processing} className="mt-4 w-full rounded-xl border border-rose-500/40 px-4 py-3 text-sm text-rose-300 disabled:opacity-50">Retry loading next question</button>}
          </section>
        )}

        {speechAnalysis && <section className="mb-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Last Answer Analysis</h3>
          <div className="grid grid-cols-3 gap-3 text-center">
            <Metric value={speechAnalysis.words_per_minute} label="WPM" />
            <Metric value={speechAnalysis.speaking_speed} label="Speed" />
            <Metric value={speechAnalysis.filler_word_count} label="Fillers" />
          </div>
        </section>}
        <section className="max-h-64 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="mb-3 flex items-center gap-1 text-xs font-semibold text-slate-400"><MessageSquare size={12} /> Transcript</h3>
          <div className="space-y-2">{transcript.map((turn, index) => (
            <div key={`${turn.role}-${index}`} className={`flex gap-2 ${turn.role === 'ai' ? '' : 'flex-row-reverse'}`}>
              <div className={`max-w-[80%] rounded-xl px-3 py-2 text-xs ${turn.role === 'ai' ? 'bg-slate-800 text-slate-300' : 'bg-rose-500/20 text-rose-200'}`}>{turn.text}</div>
            </div>
          ))}</div>
        </section>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8">
      <div className="mx-auto max-w-2xl text-center">
        <CheckCircle size={48} className="mx-auto mb-4 text-emerald-400" />
        <h1 className="mb-2 text-2xl font-bold text-white">Voice Interview Complete</h1>
        {summary && <div className="mt-6 space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <Metric value={Math.round(summary.communication_score || 0)} label="Communication" />
            <Metric value={summary.filler_word_count || 0} label="Filler Words" />
            <Metric value={summary.total_turns || 0} label="Answers" />
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-left">
            <h2 className="mb-3 text-sm font-semibold text-white">Interview Transcript and Evaluations</h2>
            <div className="space-y-3">{summary.transcript.filter(turn => turn.role === 'candidate').map((turn, index) => (
              <article key={index} className="rounded-xl bg-slate-800/70 p-3">
                <p className="text-xs text-slate-400">Question {turn.question_number}: {turn.question}</p>
                <p className="mt-2 text-sm text-white">{turn.text}</p>
                {turn.evaluation && <p className="mt-2 text-xs text-emerald-300">{turn.evaluation.feedback || `Score: ${turn.evaluation.score ?? 'Evaluated'}`}</p>}
              </article>
            ))}</div>
          </div>
          <button onClick={reset} className="mx-auto flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm text-slate-300">
            <RotateCcw size={14} /> Start New Session
          </button>
        </div>}
      </div>
    </div>
  );
};

const ErrorBanner = ({ message }) => (
  <div className="mb-4 flex gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
    <AlertCircle size={18} className="shrink-0 text-red-400" />
    <p className="text-sm text-red-300">{message}</p>
  </div>
);

const Metric = ({ value, label }) => (
  <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
    <p className="text-xl font-bold text-rose-400">{value}</p>
    <p className="mt-1 text-xs text-slate-500">{label}</p>
  </div>
);

export default VoiceInterview;
