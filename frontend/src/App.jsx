import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { InterviewProvider } from './contexts/InterviewContext';
import { NetworkProvider } from './contexts/NetworkContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import './styles/globals.css';

import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { ForgotPassword } from './pages/ForgotPassword';
import { Dashboard } from './pages/Dashboard';
import { InterviewsOverview } from './pages/InterviewsOverview';
import { PracticeOverview } from './pages/PracticeOverview';
import { CareerToolsOverview } from './pages/CareerToolsOverview';
import { StartInterview } from './pages/StartInterview';
import { InterviewSession } from './pages/InterviewSession';
import { InterviewFeedback } from './pages/InterviewFeedback';
import { Analytics } from './pages/Analytics';
import { ResumeUpload } from './pages/ResumeUpload';
import { ResumeInterview } from './pages/ResumeInterview';
import { WebcamInterview } from './pages/WebcamInterview';
import { CodingInterview } from './pages/CodingInterview';
import { CompanySelection } from './pages/CompanySelection';

// New feature pages + existing pages
import { ATSAnalyzer } from './pages/ATSAnalyzer';
import { GitHubAnalyzer } from './pages/GitHubAnalyzer';
import { SystemDesignInterview } from './pages/SystemDesignInterview';
import { VoiceInterview } from './pages/VoiceInterview';
import { RecruiterDashboard } from './pages/RecruiterDashboard';
import { InterviewHistory } from './pages/InterviewHistory';
import { InterviewReport } from './pages/InterviewReport';
import { CareerCoach } from './pages/CareerCoach';
import { Settings } from './pages/Settings';
import { AdaptiveInterview } from './pages/AdaptiveInterview';

const Layout = ({ children, title, breadcrumbs }) => (
  <AppLayout pageTitle={title} breadcrumbs={breadcrumbs}>{children}</AppLayout>
);

function App() {
  return (
    <Router>
      <NetworkProvider>
        <AuthProvider>
          <InterviewProvider>
            <Routes>
              {/* Public auth routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/register" element={<Signup />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />

              {/* Main app shell */}
              <Route path="/dashboard" element={<ProtectedRoute><Layout title="Dashboard"><Dashboard /></Layout></ProtectedRoute>} />
              <Route path="/interviews" element={<ProtectedRoute><Layout title="Interviews" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }]}><InterviewsOverview /></Layout></ProtectedRoute>} />
              <Route path="/interviews/ai" element={<ProtectedRoute><Layout title="AI Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'AI Interview', path: '/interviews/ai' }]}><StartInterview /></Layout></ProtectedRoute>} />
              <Route path="/interviews/company" element={<ProtectedRoute><Layout title="Company Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Company Interview', path: '/interviews/company' }]}><CompanySelection /></Layout></ProtectedRoute>} />
              <Route path="/interviews/adaptive" element={<ProtectedRoute><Layout title="Adaptive Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Adaptive Interview', path: '/interviews/adaptive' }]}><AdaptiveInterview /></Layout></ProtectedRoute>} />
              <Route path="/interviews/voice" element={<ProtectedRoute><Layout title="Voice Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Voice Interview', path: '/interviews/voice' }]}><VoiceInterview /></Layout></ProtectedRoute>} />
              <Route path="/interviews/session/:id" element={<ProtectedRoute><Layout title="Interview Session" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Interview Session', path: '/interviews/session' }]}><InterviewSession /></Layout></ProtectedRoute>} />
              <Route path="/interviews/report/:id" element={<ProtectedRoute><Layout title="Interview Report" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Interview Report', path: '/interviews/report' }]}><InterviewReport /></Layout></ProtectedRoute>} />

              <Route path="/practice" element={<ProtectedRoute><Layout title="Practice" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Practice', path: '/practice' }]}><PracticeOverview /></Layout></ProtectedRoute>} />
              <Route path="/practice/coding" element={<ProtectedRoute><Layout title="Coding Practice" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Practice', path: '/practice' }, { label: 'Coding Practice', path: '/practice/coding' }]}><CodingInterview /></Layout></ProtectedRoute>} />
              <Route path="/practice/system-design" element={<ProtectedRoute><Layout title="System Design" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Practice', path: '/practice' }, { label: 'System Design', path: '/practice/system-design' }]}><SystemDesignInterview /></Layout></ProtectedRoute>} />
              <Route path="/practice/technical" element={<ProtectedRoute><Layout title="Technical Questions" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Practice', path: '/practice' }, { label: 'Technical Questions', path: '/practice/technical' }]}><StartInterview /></Layout></ProtectedRoute>} />

              <Route path="/career-tools" element={<ProtectedRoute><Layout title="Career Tools" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }]}><CareerToolsOverview /></Layout></ProtectedRoute>} />
              <Route path="/career-tools/resume-analyzer" element={<ProtectedRoute><Layout title="Resume Analyzer" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'Resume Analyzer', path: '/career-tools/resume-analyzer' }]}><ATSAnalyzer /></Layout></ProtectedRoute>} />
              <Route path="/career-tools/job-description" element={<ProtectedRoute><Layout title="Job Description Analyzer" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'Job Description Analyzer', path: '/career-tools/job-description' }]}><ATSAnalyzer /></Layout></ProtectedRoute>} />
              <Route path="/career-tools/github" element={<ProtectedRoute><Layout title="GitHub Portfolio Analyzer" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'GitHub Portfolio Analyzer', path: '/career-tools/github' }]}><GitHubAnalyzer /></Layout></ProtectedRoute>} />

              <Route path="/career-coach" element={<ProtectedRoute><Layout title="AI Career Coach" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'AI Career Coach', path: '/career-coach' }]}><CareerCoach /></Layout></ProtectedRoute>} />
              <Route path="/history" element={<ProtectedRoute><Layout title="Interview History" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interview History', path: '/history' }]}><InterviewHistory /></Layout></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute><Layout title="Settings" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Settings', path: '/settings' }]}><Settings /></Layout></ProtectedRoute>} />
              <Route path="/analytics" element={<ProtectedRoute><Layout title="Analytics" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Analytics', path: '/analytics' }]}><Analytics /></Layout></ProtectedRoute>} />
              {/* Existing routes preserved */}
              <Route path="/interview/new" element={<ProtectedRoute><Layout title="Start Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Start Interview', path: '/interview/new' }]}><StartInterview /></Layout></ProtectedRoute>} />
              <Route path="/interview/session" element={<ProtectedRoute><Layout title="Interview Session" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Interview Session', path: '/interview/session' }]}><InterviewSession /></Layout></ProtectedRoute>} />
              <Route path="/interview/feedback" element={<ProtectedRoute><Layout title="Interview Feedback" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Interview Feedback', path: '/interview/feedback' }]}><InterviewFeedback /></Layout></ProtectedRoute>} />
              <Route path="/interview/*" element={<Navigate to="/interviews" />} />
              <Route path="/analytics" element={<ProtectedRoute><Layout title="Analytics" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Analytics', path: '/analytics' }]}><Analytics /></Layout></ProtectedRoute>} />
              <Route path="/resume/upload" element={<ProtectedRoute><Layout title="Resume Upload" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'Resume Upload', path: '/resume/upload' }]}><ResumeUpload /></Layout></ProtectedRoute>} />
              <Route path="/resume/interview" element={<ProtectedRoute><Layout title="Resume Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'Resume Interview', path: '/resume/interview' }]}><ResumeInterview /></Layout></ProtectedRoute>} />
              <Route path="/webcam" element={<ProtectedRoute><Layout title="Webcam Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Webcam Interview', path: '/webcam' }]}><WebcamInterview /></Layout></ProtectedRoute>} />
              <Route path="/coding" element={<ProtectedRoute><Layout title="Coding Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Practice', path: '/practice' }, { label: 'Coding Interview', path: '/coding' }]}><CodingInterview /></Layout></ProtectedRoute>} />
              <Route path="/company-selection" element={<ProtectedRoute><Layout title="Company Selection" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Company Selection', path: '/company-selection' }]}><CompanySelection /></Layout></ProtectedRoute>} />

              {/* New feature routes */}
              <Route path="/ats" element={<ProtectedRoute><Layout title="ATS Analyzer" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'ATS Analyzer', path: '/ats' }]}><ATSAnalyzer /></Layout></ProtectedRoute>} />
              <Route path="/github" element={<ProtectedRoute><Layout title="GitHub Analyzer" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Career Tools', path: '/career-tools' }, { label: 'GitHub Analyzer', path: '/github' }]}><GitHubAnalyzer /></Layout></ProtectedRoute>} />
              <Route path="/system-design" element={<ProtectedRoute><Layout title="System Design Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Practice', path: '/practice' }, { label: 'System Design Interview', path: '/system-design' }]}><SystemDesignInterview /></Layout></ProtectedRoute>} />
              <Route path="/voice-interview" element={<ProtectedRoute><Layout title="Voice Interview" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Interviews', path: '/interviews' }, { label: 'Voice Interview', path: '/voice-interview' }]}><VoiceInterview /></Layout></ProtectedRoute>} />
              <Route path="/recruiter" element={<ProtectedRoute><Layout title="Recruiter Dashboard" breadcrumbs={[{ label: 'Dashboard', path: '/dashboard' }, { label: 'Recruiter Dashboard', path: '/recruiter' }]}><RecruiterDashboard /></Layout></ProtectedRoute>} />

              <Route path="*" element={<Navigate to="/dashboard" />} />
            </Routes>
          </InterviewProvider>
        </AuthProvider>
      </NetworkProvider>
    </Router>
  );
}

export default App;
