import React, { useRef, useState } from 'react';
import { AlertCircle, ArrowRight, CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import { PageHeader } from '../components/PageHeader';
import { adaptiveService, interviewService } from '../services/api';

const QUESTION_LIMIT = 5;

export const AdaptiveInterview = () => {
  const [category, setCategory] = useState('Technical');
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [finalScore, setFinalScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState('');
  const actionLockRef = useRef(false);

  const start = async () => {
    if (actionLockRef.current) return;
    actionLockRef.current = true;
    setLoading(true);
    setError('');
    try {
      const { data: startedSession } = await interviewService.startInterview({
        interview_type: 'TECHNICAL',
        category,
        difficulty: 'MEDIUM',
        question_count: QUESTION_LIMIT,
      });
      setSession(startedSession);
      const { data } = await adaptiveService.nextQuestion({
        session_id: startedSession.id,
        category,
      });
      if (!data.question?.id || !data.question.question_text?.trim()) {
        throw new Error('The server did not return a valid interview question.');
      }
      setQuestion(data.question);
      setQuestionNumber(data.question.question_number || 1);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || 'The adaptive interview could not be started.');
    } finally {
      setLoading(false);
      actionLockRef.current = false;
    }
  };

  const submitAnswer = async (event) => {
    event.preventDefault();
    if (actionLockRef.current || !session || !question) return;
    if (!answer.trim() || answer.trim().length < 10) {
      setError('Please enter an answer of at least 10 characters.');
      return;
    }
    actionLockRef.current = true;
    setLoading(true);
    setError('');
    try {
      const { data } = await adaptiveService.submitAnswer({
        session_id: session.id,
        question_id: question.id,
        user_answer: answer.trim(),
      });
      setEvaluation(data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || 'Your answer could not be evaluated.');
    } finally {
      setLoading(false);
      actionLockRef.current = false;
    }
  };

  const loadNextQuestion = async () => {
    if (actionLockRef.current || !session) return;
    const shouldAdvance = Boolean(question && evaluation);
    if (questionNumber >= QUESTION_LIMIT) {
      if (!shouldAdvance) return;
      actionLockRef.current = true;
      setLoading(true);
      setError('');
      try {
        const { data } = await interviewService.endInterview(session.id);
        setFinalScore(data.overall_score);
        setCompleted(true);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'The interview could not be completed.');
      } finally {
        setLoading(false);
        actionLockRef.current = false;
      }
      return;
    }

    actionLockRef.current = true;
    setLoading(true);
    setError('');
    try {
      const { data } = await adaptiveService.nextQuestion({
        session_id: session.id,
        category,
        current_question_id: question?.id || null,
      });
      if (!data.question?.id || !data.question.question_text?.trim()) {
        throw new Error('The server did not return a valid interview question.');
      }
      setQuestion(data.question);
      setQuestionNumber(data.question.question_number || (shouldAdvance ? questionNumber + 1 : questionNumber));
      setAnswer('');
      setEvaluation(null);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || 'The next adaptive question could not be loaded.');
    } finally {
      setLoading(false);
      actionLockRef.current = false;
    }
  };

  const continueInterview = () => loadNextQuestion();
  const retryQuestion = () => loadNextQuestion();

  if (completed) {
    return (
      <section className="mx-auto max-w-2xl rounded-2xl border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600" />
        <h2 className="mt-4 text-xl font-semibold text-slate-900">Practice session complete</h2>
        <p className="mt-2 text-sm text-slate-500">The interview has been saved to your history.</p>
        <p className="mt-5 text-3xl font-semibold tabular-nums text-slate-900">
          {typeof finalScore === 'number' ? finalScore.toFixed(1) : '—'}
          <span className="ml-1 text-base font-normal text-slate-500">/ 10</span>
        </p>
      </section>
    );
  }

  if (!session) {
    return (
      <div className="mx-auto max-w-3xl pb-8">
        <PageHeader
          eyebrow="Interview suite"
          title="Adaptive interview"
          description="Answer a short set of questions; the interview engine adjusts difficulty and question type based on your performance."
        />
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          {error && <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}
          <label htmlFor="adaptive-category" className="block text-sm font-medium text-slate-700">Practice category</label>
          <select
            id="adaptive-category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="mt-2 h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 sm:max-w-sm"
          >
            {['Technical', 'Java', 'Python', 'React', 'SQL', 'Behavioral', 'Leadership'].map((value) => <option key={value}>{value}</option>)}
          </select>
          <button
            type="button"
            onClick={start}
            disabled={loading}
            className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? 'Preparing interview…' : 'Start adaptive interview'}
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl pb-8">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-indigo-700">Adaptive practice</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">{category}</h2>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">Question {questionNumber} of {QUESTION_LIMIT}</span>
      </div>

      {error && <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}

      {!question ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p className="text-sm text-slate-600">The next question is not available yet.</p>
          <button type="button" onClick={retryQuestion} disabled={loading} className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />} Retry
          </button>
        </section>
      ) : (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="mb-5 flex flex-wrap items-center gap-2 text-xs">
          {question?.difficulty && <span className="rounded-full bg-indigo-50 px-2.5 py-1 font-medium text-indigo-700">{question.difficulty.toLowerCase()}</span>}
          {question?.question_type && <span className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600">{question.question_type.replace(/_/g, ' ').toLowerCase()}</span>}
        </div>
        <h3 className="text-lg font-semibold leading-7 text-slate-900">{question?.question_text}</h3>

        {evaluation ? (
          <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">
              AI feedback
              {typeof evaluation.score === 'number' && <span className="ml-2 font-medium text-indigo-700">{evaluation.score.toFixed(1)} / 10</span>}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{evaluation.feedback || 'No written feedback was returned.'}</p>
            {evaluation.ideal_answer && <details className="mt-3"><summary className="cursor-pointer text-sm font-medium text-indigo-700">Review a model answer</summary><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{evaluation.ideal_answer}</p></details>}
            <button type="button" onClick={continueInterview} disabled={loading} className="mt-5 inline-flex min-h-10 items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              {questionNumber >= QUESTION_LIMIT ? 'Finish interview' : 'Next question'}
            </button>
            {error && <button type="button" onClick={retryQuestion} disabled={loading} className="mt-5 ml-3 inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-60">Retry next question</button>}
          </div>
        ) : (
          <form onSubmit={submitAnswer} className="mt-6">
            <label htmlFor="adaptive-answer" className="block text-sm font-medium text-slate-700">Your answer</label>
            <textarea
              id="adaptive-answer"
              rows={7}
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              placeholder="Explain your approach and reasoning…"
              className="mt-2 w-full resize-y rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 placeholder:text-slate-400"
              required
            />
            <p className="mt-2 text-xs text-slate-500">A thoughtful answer of at least 10 characters is required.</p>
            <button type="submit" disabled={loading} className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Submit answer
            </button>
          </form>
        )}
      </section>
      )}
    </div>
  );
};
