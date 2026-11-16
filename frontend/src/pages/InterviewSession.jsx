import React, { useState, useEffect, useRef, useCallback } from 'react';
import { interviewService, reportService } from '../services/api';
import { useInterview } from '../contexts/InterviewContext';
import { useNetwork } from '../contexts/NetworkContext';
import { AlertCircle, Loader, Send, SkipForward, WifiOff, Building2, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useProctor } from '../hooks/useProctor.jsx';

export const InterviewSession = () => {
  const navigate = useNavigate();
  const { currentSession, currentQuestion, setCurrentQuestion, addAnswer } = useInterview();
  const { fullyOnline, isOnline } = useNetwork();

  const sessionType = currentSession?.interview_type || 'TECHNICAL';
  const company = currentSession?.company || currentSession?.session_metadata?.company || null;
  const sessionMetadata = currentSession?.session_metadata || {};
  const questionCount = Number(sessionMetadata.question_count || 5);
  const sessionKey = currentSession ? `interview_${currentSession.id}` : 'interview_pending';
  const { ProctorOverlay } = useProctor(
    sessionKey,
    sessionType,
    sessionMetadata.monitoring_enabled === true,
  );

  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(1);
  const [error, setError] = useState('');
  const currentQuestionNumber = currentQuestion?.question_number || currentQuestionIndex;
  const initializedSessionRef = useRef(null);
  const initialLoadLockRef = useRef(false);
  const advanceLockRef = useRef(false);
  const submitLockRef = useRef(false);
  const pendingAdvanceRef = useRef(null);

  const finishInterview = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      await interviewService.endInterview(currentSession.id);
      await reportService.generate(currentSession.id);
      navigate(`/interviews/report/${currentSession.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not finish the interview or generate its report. Please retry.');
    } finally {
      setLoading(false);
    }
  }, [currentSession, navigate]);

  const applyQuestionResponse = (rawQuestion) => {
    const response = rawQuestion?.data && typeof rawQuestion.data === 'object'
      ? rawQuestion.data
      : rawQuestion;
    const nestedQuestion = response?.question && typeof response.question === 'object'
      ? response.question
      : response;
    const questionText = typeof response?.question_text === 'string'
      ? response.question_text
      : typeof response?.question === 'string'
        ? response.question
        : nestedQuestion?.question_text;
    const question = {
      ...nestedQuestion,
      ...response,
      id: response?.id ?? response?.question_id ?? nestedQuestion?.id ?? nestedQuestion?.question_id,
      question_text: questionText,
    };
    if (!question.id) throw new Error('The server response did not include a question ID.');
    if (typeof question.question_text !== 'string' || !question.question_text.trim()) {
      throw new Error('The server response did not include question text.');
    }
    setCurrentQuestion(question);
    setCurrentQuestionIndex(Number(question.question_number) || currentQuestionIndex);
    setAnswer('');
    setError('');
    return question;
  };

  const loadSessionQuestion = useCallback(async () => {
    if (!currentSession || initialLoadLockRef.current) return;
    initialLoadLockRef.current = true;
    setSessionLoading(true);
    setError('');
    try {
      const { data: session } = await interviewService.getSession(currentSession.id);
      if (session.status !== 'IN_PROGRESS') {
        navigate(`/interviews/report/${currentSession.id}`);
        return;
      }

      const { data: questions } = await interviewService.getQuestions(currentSession.id);
      const activeQuestion = questions.find((item) => !item.is_answered && !item.is_skipped);
      if (activeQuestion) {
        applyQuestionResponse(activeQuestion);
        return;
      }

      if (!questions.length) {
        const { data } = await interviewService.nextQuestion(currentSession.id);
        applyQuestionResponse(data);
        return;
      }

      const lastQuestion = questions[questions.length - 1];
      if (questions.length >= questionCount) {
        await finishInterview();
        return;
      }

      const { data } = await interviewService.nextQuestion(
        currentSession.id,
        lastQuestion.id,
        lastQuestion.is_skipped ? 'skip' : 'answered',
      );
      applyQuestionResponse(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load your next question.');
    } finally {
      setSessionLoading(false);
      initialLoadLockRef.current = false;
    }
  }, [currentSession, finishInterview, navigate, questionCount, setCurrentQuestion]);

  useEffect(() => {
    if (!currentSession) {
      navigate('/interview/new');
      return;
    }
    if (initializedSessionRef.current === currentSession.id) return;
    initializedSessionRef.current = currentSession.id;
    loadSessionQuestion();
  }, [currentSession, loadSessionQuestion, navigate]);

  const advanceQuestion = async (action, sourceQuestion = currentQuestion) => {
    if (!sourceQuestion || advanceLockRef.current) return false;
    advanceLockRef.current = true;
    setLoading(true);
    setError('');
    try {
      const { data } = await interviewService.nextQuestion(
        currentSession.id,
        sourceQuestion.id,
        action,
      );
      applyQuestionResponse(data);
      pendingAdvanceRef.current = null;
      return true;
    } catch (err) {
      pendingAdvanceRef.current = { action, question: sourceQuestion };
      setError(err.response?.data?.detail || err.message || 'The next question could not be loaded. Retry without leaving this question.');
      return false;
    } finally {
      setLoading(false);
      advanceLockRef.current = false;
    }
  };

  const retryLoading = () => {
    if (pendingAdvanceRef.current) {
      const pending = pendingAdvanceRef.current;
      advanceQuestion(pending.action, pending.question);
    } else {
      loadSessionQuestion();
    }
  };

  const handleSubmitAnswer = async (e) => {
    e.preventDefault();
    if (submitLockRef.current || !currentQuestion) return;
    if (!answer.trim() || answer.trim().length < 10) {
      setError('Answer must be at least 10 characters');
      return;
    }
    if (!fullyOnline) {
      setError('No internet connection. Please reconnect to submit your answer.');
      return;
    }

    submitLockRef.current = true;
    setSubmitting(true);
    setError('');
    try {
      const res = await interviewService.submitAnswer({
        question_id: currentQuestion.id,
        user_answer: answer,
      });
      addAnswer(res.data);
      navigate('/interview/feedback', {
        state: {
          answer: res.data,
          isLastQuestion: currentQuestionNumber >= questionCount,
          questionNumber: currentQuestionNumber,
          currentQuestionId: currentQuestion.id,
        },
      });
    } catch (err) {
      setError(
        err.isNetworkError
          ? 'Connection lost. Please reconnect and try again.'
          : err.response?.data?.detail || 'Failed to submit answer'
      );
    } finally {
      setSubmitting(false);
      submitLockRef.current = false;
    }
  };

  const handleSkipQuestion = async () => {
    if (!fullyOnline) { setError('No internet connection. Cannot load next question.'); return; }
    if (!currentQuestion || advanceLockRef.current) return;
    if (currentQuestionNumber >= questionCount) {
      advanceLockRef.current = true;
      setLoading(true);
      setError('');
      try {
        await interviewService.skipQuestion(currentSession.id, currentQuestion.id);
        await finishInterview();
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not skip the final question. Please retry.');
      } finally {
        setLoading(false);
        advanceLockRef.current = false;
      }
      return;
    }
    advanceQuestion('skip');
  };

  const handleExit = () => {
    if (window.confirm('Exit this interview and open its current report?')) finishInterview();
  };

  if (!currentSession) return null;

  if (sessionLoading) {
    return (
      <>
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
          <div className="mb-5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
              {company && <Building2 size={16} className="text-amber-400" />}
              {company ? `${company} interview` : 'Interview practice'}
            </div>
            <button type="button" onClick={handleExit} disabled={loading} className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50">
              {loading ? <Loader size={15} className="animate-spin" /> : <LogOut size={15} />} Exit interview
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium">
                Question {currentQuestionNumber} of {questionCount}
              </span>
              <span className="text-sm text-slate-400">
                {Math.round((currentQuestionNumber / questionCount) * 100)}%
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-indigo-500 to-pink-500 h-2 rounded-full transition-all"
                style={{ width: `${(currentQuestionNumber / questionCount) * 100}%` }}
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
                <><Building2 size={12} className="mr-1 inline" />{company}</>
              </span>
            )}
            {sessionMetadata.role && <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-300">{sessionMetadata.role}</span>}
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
                {(!currentQuestion || pendingAdvanceRef.current) && (
                  <button
                    onClick={retryLoading}
                    className="text-indigo-400 text-xs mt-1 hover:underline"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
            <div className="min-w-0">
              <section className="card mb-5">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-indigo-500/15 px-2.5 py-1 text-xs font-medium text-indigo-300">
                    {currentQuestion?.topic || currentQuestion?.category || 'Interview question'}
                  </span>
                  <span className="rounded-full bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                    {currentQuestion?.difficulty || sessionMetadata.difficulty || 'MEDIUM'}
                  </span>
                </div>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Question {currentQuestionNumber}
                </h2>
                <p className="text-xl leading-relaxed text-white">
                  {currentQuestion?.question_text || (sessionLoading ? 'Loading question…' : 'Question could not be loaded. Use Retry to try again.')}
                </p>
                {currentQuestion?.context && <p className="mt-4 border-l-2 border-indigo-500 pl-3 text-sm text-slate-400">{currentQuestion.context}</p>}
              </section>

              <section className="card">
                <form onSubmit={handleSubmitAnswer} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" htmlFor="interview-answer">Your answer</label>
                    <textarea
                      id="interview-answer"
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      data-answer-field="true"
                      placeholder="Explain your approach and include a relevant example."
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 resize-none transition-colors"
                      rows={8}
                      disabled={!fullyOnline || !currentQuestion || loading || submitting}
                    />
                    <p className="mt-1 text-right text-xs text-slate-500" aria-live="polite">{answer.length} characters</p>
                  </div>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <button
                      type="submit"
                      disabled={loading || submitting || !currentQuestion || answer.trim().length < 10 || !fullyOnline}
                      className="flex-1 btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {submitting ? <><Loader size={18} className="animate-spin" /> Evaluating...</> : <><Send size={18} /> Submit answer</>}
                    </button>
                    <button
                      type="button"
                      onClick={handleSkipQuestion}
                      disabled={loading || submitting || !currentQuestion || !fullyOnline}
                      className="btn-secondary py-3 px-6 flex items-center justify-center gap-2"
                    >
                      <SkipForward size={18} /> Skip question
                    </button>
                  </div>
                </form>
              </section>
            </div>

            <aside className="space-y-4">
              <section className="card">
                <h3 className="text-sm font-semibold text-white">Interview progress</h3>
                <p className="mt-3 text-2xl font-semibold text-white">{currentQuestionNumber}<span className="text-sm font-normal text-slate-500"> / {questionCount}</span></p>
                <p className="mt-1 text-xs text-slate-400">{Math.max(questionCount - currentQuestionNumber, 0)} questions remaining</p>
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-700">
                  <div className="h-full rounded-full bg-indigo-500" style={{ width: `${(currentQuestionNumber / questionCount) * 100}%` }} />
                </div>
              </section>
              <section className="card">
                <h3 className="text-sm font-semibold text-white">Interview details</h3>
                <dl className="mt-3 space-y-2 text-xs">
                  <div className="flex justify-between gap-3"><dt className="text-slate-500">Round</dt><dd className="text-right text-slate-300">{sessionMetadata.interview_round || 'General'}</dd></div>
                  <div className="flex justify-between gap-3"><dt className="text-slate-500">Experience</dt><dd className="text-right text-slate-300">{sessionMetadata.experience || 'Not specified'}</dd></div>
                  <div className="flex justify-between gap-3"><dt className="text-slate-500">Difficulty</dt><dd className="text-right text-slate-300">{sessionMetadata.difficulty || 'MEDIUM'}</dd></div>
                  <div className="flex justify-between gap-3"><dt className="text-slate-500">Monitoring</dt><dd className="text-right text-slate-300">Not enabled</dd></div>
                </dl>
              </section>
              <section className="card">
                <h3 className="text-sm font-semibold text-white">Guidelines</h3>
                <ul className="mt-3 space-y-2 text-xs leading-5 text-slate-400">
                  <li>Explain your reasoning step by step.</li>
                  <li>Use a concrete example when useful.</li>
                  <li>Keep the answer relevant to the selected role.</li>
                </ul>
              </section>
            </aside>
          </div>
        </div>
      </div>
    </>
  );
};
