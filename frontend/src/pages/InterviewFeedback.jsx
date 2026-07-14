import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useInterview } from '../contexts/InterviewContext';
import { interviewService } from '../services/api';
import { CheckCircle, XCircle, Lightbulb, ArrowRight, Flag } from 'lucide-react';

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
  const { answer, isLastQuestion } = location.state || {};

  if (!answer) {
    navigate('/dashboard');
    return null;
  }

  const handleNextQuestion = async () => {
    try {
      const cat = currentSession.interview_type === 'MIXED'
        ? ['Java', 'Python', 'SQL', 'Behavioral'][Math.floor(Math.random() * 4)]
        : currentSession.interview_type === 'HR' ? 'Behavioral' : 'Technical';

      const res = await interviewService.generateQuestion(
        currentSession.id,
        cat,
        'MEDIUM',
      );
      setCurrentQuestion(res.data);
      navigate('/interview/session');
    } catch {
      navigate('/interview/session');
    }
  };

  const handleEndInterview = async () => {
    try {
      await interviewService.endInterview(currentSession.id);
    } catch {
      // still navigate even if end call fails
    }
    resetInterview();
    navigate('/dashboard');
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
        <div className="flex gap-4">
          {!isLastQuestion ? (
            <button
              onClick={handleNextQuestion}
              className="flex-1 btn-primary py-4 flex items-center justify-center gap-2 font-semibold"
            >
              Next Question <ArrowRight size={18} />
            </button>
          ) : null}
          <button
            onClick={handleEndInterview}
            className="flex-1 btn-secondary py-4 flex items-center justify-center gap-2 font-semibold"
          >
            <Flag size={18} /> End Interview
          </button>
        </div>
      </div>
    </div>
  );
};

export default InterviewFeedback;
