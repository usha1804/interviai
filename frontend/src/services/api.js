import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ── Request interceptor: attach token ────────────────────────────
api.interceptors.request.use(
  (config) => {
    // Block request if browser reports offline
    if (!navigator.onLine) {
      return Promise.reject(
        Object.assign(new Error('No internet connection'), { isOffline: true })
      );
    }
    const token = localStorage.getItem('accessToken');
    config.headers = config.headers || {};
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401 / network errors ────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Offline / network error
    if (!error.response || error.isOffline) {
      return Promise.reject(
        Object.assign(error, {
          isNetworkError: true,
          userMessage: 'No internet connection. Please check your network.',
        })
      );
    }

    const originalRequest = error.config;
    const status = error.response.status;

    // Skip retry for auth endpoints and already-retried requests
    const isAuthEndpoint =
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/register');

    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refreshToken');

      if (refreshToken) {
        try {
          const res = await axios.post(
            `${API_URL}/auth/refresh`,
            {},
            { headers: { Authorization: `Bearer ${refreshToken}` }, timeout: 10000 }
          );
          const newToken = res.data.access_token;
          localStorage.setItem('accessToken', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        } catch {
          // Refresh failed — force logout
        }
      }

      // Clear session and redirect
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.patch('/auth/profile', data),
  verify: () => api.get('/auth/verify'),
};

export const interviewService = {
  startInterview: (data) => api.post('/interview/start', data),
  generateQuestion: (sessionId, category, difficulty) =>
    api.post(`/interview/generate-question/${sessionId}`, { category, difficulty }),
  submitAnswer: (data) => api.post('/interview/submit-answer', data),
  endInterview: (sessionId) => api.post(`/interview/end/${sessionId}`),
  getSession: (sessionId) => api.get(`/interview/session/${sessionId}`),
  getQuestions: (sessionId) => api.get(`/interview/questions/${sessionId}`),
  getAnswer: (answerId) => api.get(`/interview/answer/${answerId}`),
};

export const analyticsService = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getHistory: (skip = 0, limit = 10) =>
    api.get(`/analytics/history?skip=${skip}&limit=${limit}`),
  getReport: (sessionId) => api.get(`/analytics/report/${sessionId}`),
  getStrengthsWeaknesses: () => api.get('/analytics/strengths-weaknesses'),
  getPerformanceTrend: () => api.get('/analytics/performance-trend'),
  getCategoryPerformance: () => api.get('/analytics/category-performance'),
};

export const proctorService = {
  start: (data) => api.post('/proctor/start', data),
  logEvent: (data) => api.post('/proctor/event', data),
  end: (data) => api.post('/proctor/end', data),
  getReport: (sessionKey) => api.get(`/proctor/report/${sessionKey}`),
  readinessReport: (data) => api.post('/proctor/readiness-report', data),
};

export const webcamService = {
  analyze: (data) => api.post('/webcam/analyze', data),
  getReport: (sessionId) => api.get(`/webcam/report/${sessionId}`),
  getHistory: () => api.get('/webcam/history'),
};

export const codingService = {
  getProblem: (data) => api.post('/coding/problem', data),
  runCode: (data) => api.post('/coding/run', data),
  submit: (data) => api.post('/coding/submit', data),
  getHistory: () => api.get('/coding/history'),
};

export const resumeService = {
  upload: (formData) =>
    api.post('/resume/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getLatest: () => api.get('/resume/latest'),
  getAll: () => api.get('/resume/all'),
  delete: (id) => api.delete(`/resume/${id}`),
  generateQuestions: (resumeId, difficulty = 'MEDIUM') =>
    api.post('/resume/generate-questions', { resume_id: resumeId, difficulty }),
};

export const atsService = {
  analyze: (data) => api.post('/ats/analyze', data),
  getReports: () => api.get('/ats/reports'),
  downloadPdf: (reportId) => api.get(`/ats/report/${reportId}/pdf`, { responseType: 'blob' }),
};

export const adaptiveService = {
  nextQuestion: (data) => api.post('/adaptive/next-question', data),
  submitAnswer: (data) => api.post('/adaptive/submit-answer', data),
};

export const githubService = {
  analyze: (data) => api.post('/github/analyze', data),
  getLatest: () => api.get('/github/latest'),
};

export const systemDesignService = {
  getTopics: () => api.get('/system-design/topics'),
  start: (data) => api.post('/system-design/start', data),
  submitAnswer: (data) => api.post('/system-design/submit-answer', data),
  end: (sessionId) => api.post(`/system-design/end/${sessionId}`),
  getSession: (sessionId) => api.get(`/system-design/session/${sessionId}`),
};

export const voiceService = {
  start: (data) => api.post('/voice/start', data),
  tts: (data) => api.post('/voice/tts', data, { responseType: 'blob' }),
  stt: (sessionId, formData) => api.post(`/voice/stt/${sessionId}`, formData),
  end: (sessionId) => api.post(`/voice/end/${sessionId}`),
};

export const recruiterService = {
  getCandidates: (search = '', skip = 0) => api.get(`/recruiter/candidates?search=${search}&skip=${skip}`),
  getCandidate: (id) => api.get(`/recruiter/candidate/${id}`),
  hiringDecision: (id) => api.post(`/recruiter/hiring-decision/${id}`),
  saveNote: (data) => api.post('/recruiter/note', data),
  getNotes: (candidateId) => api.get(`/recruiter/notes/${candidateId}`),
};

export const ragService = {
  uploadJD: (data) => api.post('/rag/upload-jd', data),
  getJD: () => api.get('/rag/jd'),
  generateQuestions: (data) => api.post('/rag/generate-questions', data),
  evaluate: (data) => api.post('/rag/evaluate', data),
  ingestResume: (resumeId) => api.post(`/rag/ingest-resume/${resumeId}`),
  listCompanies: () => api.get('/rag/companies'),
  ingestCompany: (data) => api.post('/rag/company/ingest', data),
};

export const careerCoachService = {
  analyze: (data) => api.post('/career-coach/analyze', data),
  getProfile: () => api.get('/career-coach/profile'),
  getSkillGap: () => api.get('/career-coach/skill-gap'),
  getLearningPlan: (days) => api.get(`/career-coach/learning-plan/${days}`),
};

export const reportService = {
  generate: (sessionId) => api.post(`/report/generate/${sessionId}`),
  get: (sessionId) => api.get(`/report/${sessionId}`),
  downloadPdf: (sessionId) =>
    api.get(`/report/${sessionId}/pdf`, { responseType: 'blob' }),
};

export const adminService = {
  listUsers: (skip = 0, limit = 50) => api.get(`/admin/users?skip=${skip}&limit=${limit}`),
  getStatistics: () => api.get('/admin/statistics'),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  getUserDetails: (userId) => api.get(`/admin/user/${userId}`),
  listAIPrompts: () => api.get('/admin/ai-prompts'),
  createAIPrompt: (data) => api.post('/admin/ai-prompts', data),
  listSessions: (skip = 0, limit = 50) => api.get(`/admin/sessions?skip=${skip}&limit=${limit}`),
};

export default api;
