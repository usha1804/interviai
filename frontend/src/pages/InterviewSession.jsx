import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from '../components/Navbar';
import { interviewService } from '../services/api';
import { useInterview } from '../contexts/InterviewContext';
import { useNetwork } from '../contexts/NetworkContext';
import { AlertCircle, Loader, Send, SkipForward, WifiOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useProctor } from '../hooks/useProctor.jsx';

const MAX_QUESTIONS = 5;

function pickCategory(interviewType, company) {
  if (interviewType === 'HR') return 'Behavioral';
  if (company) return `${company} Interview`;
  if (interviewType === 'MIXED') {
    const mixed = ['Java', 'Python', 'SQL', 'React', 'Behavioral'];
    return mixed[Math.floor(Math.random() * mixed.length)];
  }
  return 'Technical';
}

export const InterviewSession = () => {
  const navigate = useNavigate();
  const { currentSession, currentQuestion, setCurrentQuestion, addAnswer } = useInterview();
  const { fullyOnline, isOnline } = useNetwork();

  const sessionType = currentSession?.interview_type || 'TECHNICAL';
  const company = currentSession?.company || currentSession?.session_metadata?.company || null;
  const sessionKey = currentSession ? `interview_${currentSession.id}` : 'interview_pending';
  const { ProctorOverlay, stopProctor } = useProctor(sessionKey, sessionType);

  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentQuestionNumber, setCurrentQuestionNumber] = useState(1);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (!currentSession) { navigate('/interview/new'); return; }
    if (currentQuestion || fetchedRef.current) return;

    fetchedRef.current = true;
    const fetchQuestion = async () => {
      setSessionLoading(true);
      setError('');
      try {
        const cat = pickCategory(currentSession.interview_type, company);
        const res = await interviewService.generateQuestion(currentSession.id, cat, 'MEDIUM');
        setCurrentQuestion(res.data);
      } catch (err) {
        const msg = err.isNetworkError
          ? 'No internet connection. Please reconnect to load questions.'
          : err.response?.data?.detail || err.message || 'Unknown error';
        setError(`Failed to load question: ${msg}`);
        fetchedRef.current = false;
      } finally {
        setSessionLoading(false);
      }
    };
    fetchQuestion();
  }, [currentSession]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmitAnswer = async (e) => {
    e.preventDefault();
    if (!answer.trim() || answer.trim().length < 10) {
      setError('Answer must be at least 10 characters');
      return;
    }
    if (!fullyOnline) {
      setError('No internet connection. Please reconnect to submit your answer.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await interviewService.submitAnswer({
        question_id: currentQuestion.id,
        user_answer: answer,
      });
      addAnswer(res.data);
      await stopProctor();
      navigate('/interview/feedback', {
        state: { answer: res.data, isLastQuestion: currentQuestionNumber >= MAX_QUESTIONS },
      });
    } catch (err) {
      setError(
        err.isNetworkError
          ? 'Connection lost. Please reconnect and try again.'
          : err.response?.data?.detail || 'Failed to submit answer'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSkipQuestion = async () => {
    if (!fullyOnline) { setError('No internet connection. Cannot load next question.'); return; }
    setError('');
    try {
      const cat = pickCategory(currentSession.interview_type, company);
      const res = await interviewService.generateQuestion(currentSession.id, cat, 'MEDIUM');
      setCurrentQuestion(res.data);
      setAnswer('');
      setCurrentQuestionNumber((prev) => Math.min(prev + 1, MAX_QUESTIONS));
    } catch (err) {
      setError('Failed to load next question');
    }
  };

  if (sessionLoading) {
    return (
      <>
        <Navbar />
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto" />
            <p className="text-slate-400 mt-4">Generating question with AI...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <ProctorOverlay />

      {/* Offline overlay — pauses interview */}
      {!fullyOnline && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center">
          <div className="bg-slate-900 border border-red-700 rounded-2xl p-8 max-w-sm text-center shadow-2xl">
            <WifiOff size={48} className="text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Connection Lost</h2>
            <p className="text-slate-400 mb-2">
              {!isOnline
                ? 'No internet connection detected.'
                : 'Cannot reach the server.'}
            </p>
            <p className="text-slate-500 text-sm mb-6">
              Interview is paused. Reconnect to continue — your progress is saved.
            </p>
            <div className="animate-pulse text-yellow-400 text-sm font-medium">
              ⏳ Waiting for connection...
            </div>
          </div>
        </div>
      )}

      <div className="min-h-screen bg-dark">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium">
                Question {currentQuestionNumber} of {MAX_QUESTIONS}
              </span>
              <span className="text-sm text-slate-400">
                {Math.round((currentQuestionNumber / MAX_QUESTIONS) * 100)}%
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-indigo-500 to-pink-500 h-2 rounded-full transition-all"
                style={{ width: `${(currentQuestionNumber / MAX_QUESTIONS) * 100}%` }}
              />
            </div>
          </div>

          {/* Session Info */}
          <div className="flex gap-3 mb-6 flex-wrap">
            <span className="px-3 py-1 bg-indigo-500/20 border border-indigo-500/40 rounded-full text-xs text-indigo-300 font-medium">
              {currentSession?.interview_type}
            </span>
            {company && (
              <span className="px-3 py-1 bg-amber-500/20 border border-amber-500/40 rounded-full text-xs text-amber-300 font-medium">
                🏢 {company}
              </span>
            )}
            <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-400">
              {currentQuestion?.category}
            </span>
            <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-400">
              {currentQuestion?.difficulty}
            </span>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg flex gap-3 items-start">
              <AlertCircle className="text-red-500 shrink-0 mt-0.5" size={18} />
              <div>
                <p className="text-red-300 text-sm">{error}</p>
                {error.includes('Failed to load') && (
                  <button
                    onClick={() => { fetchedRef.current = false; setError(''); }}
                    className="text-indigo-400 text-xs mt-1 hover:underline"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Question */}
          <div className="card mb-8">
            <h2 className="text-lg font-semibold text-slate-400 mb-3">
              Question {currentQuestionNumber}
            </h2>
            <p className="text-xl text-white leading-relaxed">
              {currentQuestion?.question_text || 'Loading question...'}
            </p>
          </div>

          {/* Answer Form */}
          <div className="card mb-6">
            <form onSubmit={handleSubmitAnswer} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Your Answer</label>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer here... (minimum 10 characters)"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 resize-none transition-colors"
                  rows={7}
                  disabled={!fullyOnline}
                />
                <p className="text-xs text-slate-500 mt-1">{answer.length} characters</p>
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  disabled={loading || answer.trim().length < 10 || !fullyOnline}
                  className="flex-1 btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <><Loader size={18} className="animate-spin" /> Evaluating...</>
                  ) : (
                    <><Send size={18} /> Submit Answer</>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleSkipQuestion}
                  disabled={loading || !fullyOnline}
                  className="btn-secondary py-3 px-6 flex items-center gap-2"
                >
                  <SkipForward size={18} /> Skip
                </button>
              </div>
            </form>
          </div>

          {/* Tips */}
          <div className="card bg-slate-800/50 text-sm">
            <h3 className="font-semibold mb-2">💡 Tips</h3>
            <ul className="text-slate-400 space-y-1">
              <li>• Be specific and provide real examples from experience</li>
              <li>• Explain your reasoning and thought process</li>
              <li>• For HR questions, use the STAR method</li>
              <li>• Be concise but comprehensive</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
};
