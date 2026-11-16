import React, { useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useInterview } from '../contexts/InterviewContext';
import { interviewService, reportService } from '../services/api';
import { CheckCircle, XCircle, Lightbulb, ArrowRight, Flag, AlertCircle, Loader } from 'lucide-react';

const ScoreBar = ({ label, value }) => (
  <div className="mb-3">
    <div className="flex justify-between text-sm mb-1">
      <span className="text-slate-400">{label}</span>
      <span className="font-semibold">{value?.toFixed(1) ?? 'N/A'}/10</span>
    </div>
    <div className="w-full bg-slate-700 rounded-full h-2">
      <div
        className="bg-gradient-to-r from-indigo-500 to-pink-500 h-2 rounded-full transition-all"
        style={{ width: `${((value || 0) / 10) * 100}%` }}
      />
    </div>
  </div>
);

export const InterviewFeedback = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentSession, setCurrentQuestion, resetInterview } = useInterview();
  const { answer, isLastQuestion, currentQuestionId } = location.state || {};
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const actionLockRef = useRef(false);

  if (!answer) {
    navigate('/dashboard');
    return null;
  }

  const handleNextQuestion = async () => {
    if (actionLockRef.current || !currentSession || !currentQuestionId) return;
    actionLockRef.current = true;
    setLoading(true);
    setError('');
    try {
      const res = await interviewService.nextQuestion(
        currentSession.id,
        currentQuestionId,
        'answered',
      );
      const response = res.data?.data && typeof res.data.data === 'object'
        ? res.data.data
        : res.data;
      const nestedQuestion = response?.question && typeof response.question === 'object'
        ? response.question
        : response;
      const question = {
        ...nestedQuestion,
        ...response,
        id: response?.id ?? response?.question_id ?? nestedQuestion?.id ?? nestedQuestion?.question_id,
        question_text: typeof response?.question_text === 'string'
          ? response.question_text
          : typeof response?.question === 'string'
            ? response.question
            : nestedQuestion?.question_text,
      };
      if (!question.id) throw new Error('The server response did not include a question ID.');
      if (typeof question.question_text !== 'string' || !question.question_text.trim()) {
        throw new Error('The server response did not include question text.');
      }
      setCurrentQuestion(question);
      navigate('/interview/session');
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || 'The next question could not be generated. Please retry.');
    } finally {
      setLoading(false);
      actionLockRef.current = false;
    }
  };

  const handleEndInterview = async () => {
    if (actionLockRef.current || !currentSession) return;
    actionLockRef.current = true;
    setLoading(true);
    setError('');
    try {
      await interviewService.endInterview(currentSession.id);
      await reportService.generate(currentSession.id);
      navigate(`/interviews/report/${currentSession.id}`);
      resetInterview();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'The final report could not be generated. Please retry.');
    } finally {
      setLoading(false);
      actionLockRef.current = false;
    }
  };

  return (
    <div className="min-h-screen bg-dark py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Score Header */}
        <div className="card mb-6 text-center">
          <div className={`text-6xl font-black mb-2 ${
            (answer.score || 0) >= 7 ? 'text-green-400' :
            (answer.score || 0) >= 5 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {answer.score?.toFixed(1) ?? '—'}
            <span className="text-2xl text-slate-400">/10</span>
          </div>
          <p className="text-slate-400 text-sm">Answer Score</p>
        </div>

        {/* Score Breakdown */}
        <div className="card mb-6">
          <h3 className="font-bold mb-4">Score Breakdown</h3>
          <ScoreBar label="Technical Accuracy" value={answer.technical_accuracy} />
          <ScoreBar label="Completeness" value={answer.completeness} />
          <ScoreBar label="Clarity" value={answer.clarity} />
          <ScoreBar label="Communication" value={answer.communication_score} />
        </div>

        {/* AI Feedback */}
        <div className="card mb-6">
          <h3 className="font-bold mb-3 flex items-center gap-2">
            <Lightbulb size={18} className="text-yellow-400" /> AI Feedback
          </h3>
          <p className="text-slate-300 text-sm leading-relaxed">{answer.ai_feedback}</p>
        </div>

        {/* Strengths & Improvements */}
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <div className="card">
            <h3 className="font-bold mb-3 flex items-center gap-2 text-green-400">
              <CheckCircle size={16} /> Strengths
            </h3>
            <p className="text-slate-300 text-sm leading-relaxed">{answer.strengths}</p>
          </div>
          <div className="card">
            <h3 className="font-bold mb-3 flex items-center gap-2 text-red-400">
              <XCircle size={16} /> Improvements
            </h3>
            <p className="text-slate-300 text-sm leading-relaxed">{answer.improvements}</p>
          </div>
        </div>

        {/* Ideal Answer */}
        <div className="card mb-8 bg-indigo-900/20 border border-indigo-800">
          <h3 className="font-bold mb-3 text-indigo-300">💡 Model Answer</h3>
          <p className="text-slate-300 text-sm leading-relaxed">{answer.ideal_answer}</p>
        </div>

        {/* Actions */}
        {error && <div role="alert" className="mb-4 flex gap-2 rounded-lg border border-red-800 bg-red-900/20 p-3 text-sm text-red-300"><AlertCircle size={16} />{error}</div>}
        <div className="flex gap-4">
          {!isLastQuestion ? (
            <button
              onClick={handleNextQuestion}
              disabled={loading}
              className="flex-1 btn-primary py-4 flex items-center justify-center gap-2 font-semibold"
            >
              {loading ? <Loader size={18} className="animate-spin" /> : <>Next Question <ArrowRight size={18} /></>}
            </button>
          ) : null}
          <button
            onClick={handleEndInterview}
            disabled={loading}
            className="flex-1 btn-secondary py-4 flex items-center justify-center gap-2 font-semibold"
          >
          {loading ? <Loader size={18} className="animate-spin" /> : <><Flag size={18} /> Finish & View Report</>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InterviewFeedback;
