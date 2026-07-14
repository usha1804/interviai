import React, { createContext, useContext, useState } from 'react';

const InterviewContext = createContext();

export const InterviewProvider = ({ children }) => {
  const [currentSession, setCurrentSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const addAnswer = (answer) => {
    setAnswers([...answers, answer]);
  };

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
