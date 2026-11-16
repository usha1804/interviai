import React, { createContext, useCallback, useContext, useState } from 'react';

const InterviewContext = createContext();
const ACTIVE_SESSION_KEY = 'interviai.activeInterviewSession';

function readStoredSession() {
  try {
    const stored = sessionStorage.getItem(ACTIVE_SESSION_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch (error) {
    console.error('Unable to restore the active interview session.', error);
    sessionStorage.removeItem(ACTIVE_SESSION_KEY);
    return null;
  }
}

export const InterviewProvider = ({ children }) => {
  const [currentSession, setCurrentSessionState] = useState(readStoredSession);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const addAnswer = (answer) => {
    setAnswers((previous) => (
      previous.some((item) => item.question_id === answer.question_id)
        ? previous
        : [...previous, answer]
    ));
  };

  const setCurrentSession = useCallback((sessionOrUpdater) => {
    setCurrentSessionState((previous) => {
      const session = typeof sessionOrUpdater === 'function'
        ? sessionOrUpdater(previous)
        : sessionOrUpdater;
      if (session) sessionStorage.setItem(ACTIVE_SESSION_KEY, JSON.stringify(session));
      else sessionStorage.removeItem(ACTIVE_SESSION_KEY);
      return session;
    });
  }, []);

  const updateSessionScore = (score) => {
    if (currentSession) {
      setCurrentSession({ ...currentSession, overall_score: score });
    }
  };

  const resetInterview = () => {
    setCurrentSession(null);
    setCurrentQuestion(null);
    setAnswers([]);
    setError(null);
  };

  const value = {
    currentSession,
    setCurrentSession,
    currentQuestion,
    setCurrentQuestion,
    answers,
    addAnswer,
    loading,
    setLoading,
    error,
    setError,
    updateSessionScore,
    resetInterview,
  };

  return (
    <InterviewContext.Provider value={value}>
      {children}
    </InterviewContext.Provider>
  );
};

export const useInterview = () => {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error('useInterview must be used within InterviewProvider');
  }
  return context;
};
