import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { InterviewProvider } from './contexts/InterviewContext';
import { NetworkProvider } from './contexts/NetworkContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import './styles/globals.css';

import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { StartInterview } from './pages/StartInterview';
import { InterviewSession } from './pages/InterviewSession';
import { InterviewFeedback } from './pages/InterviewFeedback';
import { Analytics } from './pages/Analytics';
import { ResumeUpload } from './pages/ResumeUpload';
import { ResumeInterview } from './pages/ResumeInterview';
import { WebcamInterview } from './pages/WebcamInterview';
import { CodingInterview } from './pages/CodingInterview';
import { CompanySelection } from './pages/CompanySelection';

// New feature pages
import { ATSAnalyzer } from './pages/ATSAnalyzer';
import { GitHubAnalyzer } from './pages/GitHubAnalyzer';
import { SystemDesignInterview } from './pages/SystemDesignInterview';
import { VoiceInterview } from './pages/VoiceInterview';
import { RecruiterDashboard } from './pages/RecruiterDashboard';

function App() {
  return (
    <Router>
      <NetworkProvider>
        <AuthProvider>
          <InterviewProvider>
            <Routes>
              {/* Public */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />

              {/* Existing Protected */}
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/interview/new" element={<ProtectedRoute><StartInterview /></ProtectedRoute>} />
              <Route path="/interview/session" element={<ProtectedRoute><InterviewSession /></ProtectedRoute>} />
              <Route path="/interview/feedback" element={<ProtectedRoute><InterviewFeedback /></ProtectedRoute>} />
              <Route path="/interview/*" element={<Navigate to="/interview/new" />} />
              <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
              <Route path="/resume/upload" element={<ProtectedRoute><ResumeUpload /></ProtectedRoute>} />
              <Route path="/resume/interview" element={<ProtectedRoute><ResumeInterview /></ProtectedRoute>} />
              <Route path="/webcam" element={<ProtectedRoute><WebcamInterview /></ProtectedRoute>} />
              <Route path="/coding" element={<ProtectedRoute><CodingInterview /></ProtectedRoute>} />
              <Route path="/company-selection" element={<ProtectedRoute><CompanySelection /></ProtectedRoute>} />

              {/* New Feature Routes */}
              <Route path="/ats" element={<ProtectedRoute><ATSAnalyzer /></ProtectedRoute>} />
              <Route path="/github" element={<ProtectedRoute><GitHubAnalyzer /></ProtectedRoute>} />
              <Route path="/system-design" element={<ProtectedRoute><SystemDesignInterview /></ProtectedRoute>} />
              <Route path="/voice-interview" element={<ProtectedRoute><VoiceInterview /></ProtectedRoute>} />
              <Route path="/recruiter" element={<ProtectedRoute><RecruiterDashboard /></ProtectedRoute>} />

              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </InterviewProvider>
        </AuthProvider>
      </NetworkProvider>
    </Router>
  );
}

export default App;
