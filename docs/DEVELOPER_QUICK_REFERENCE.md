# InterviAI Developer Quick Reference

## 🚀 Commands Cheat Sheet

### Backend Commands

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Development
uvicorn app.main:app --reload  # Hot reload on port 8000
uvicorn app.main:app --reload --port 8001  # Custom port

# Database
# Tables auto-created on first run from models.py

# Docker
docker build -t interviai-backend:latest .
docker run -d -p 8000:8000 -e DATABASE_URL=... interviai-backend:latest
```

### Frontend Commands

```bash
# Setup
cd frontend
npm install

# Development
npm run dev  # Starts on port 5173
npm run dev:host  # Accessible from network

# Production
npm run build  # Creates dist/
npm run preview  # Preview production build

# Quality
npm run lint  # ESLint check
npm run format  # Prettier formatting
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f  # All services
docker-compose logs -f backend  # Specific service

# Rebuild
docker-compose up -d --build

# Stop
docker-compose down

# Clean
docker-compose down -v  # Remove volumes too
```

---

## 📊 File Tree

```
interviai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py (FastAPI app, routes setup)
│   │   ├── config.py (Settings, environment)
│   │   ├── database.py (DB session, engine)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py (SQLAlchemy models)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py (Pydantic schemas)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py (Auth endpoints)
│   │   │   ├── interview.py (Interview endpoints)
│   │   │   ├── analytics.py (Analytics endpoints)
│   │   │   └── admin.py (Admin endpoints)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py (Groq AI integration)
│   │   │   └── interview_service.py (Interview logic)
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── auth.py (JWT, hashing, auth guards)
│   │   └── middleware/
│   │       └── __init__.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx (Navigation)
│   │   │   └── ProtectedRoute.jsx (Auth guard)
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── InterviewSession.jsx
│   │   │   └── Analytics.jsx
│   │   ├── services/
│   │   │   └── api.js (Axios client)
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx
│   │   │   └── InterviewContext.jsx
│   │   ├── hooks/
│   │   │   └── useHooks.js (Custom hooks)
│   │   ├── styles/
│   │   │   └── globals.css
│   │   ├── App.jsx (Main app component)
│   │   └── main.jsx (Entry point)
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
│
├── docs/
│   ├── ARCHITECTURE.md (System design)
│   ├── DATABASE_SCHEMA.md (DB design)
│   ├── API_DOCUMENTATION.md (API reference)
│   ├── DEPLOYMENT.md (Deploy guide)
│   ├── SETUP_GUIDE.md (Setup instructions)
│   ├── AI_PROMPTS_REFERENCE.md (AI prompts)
│   └── DEVELOPER_QUICK_REFERENCE.md (This file)
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🔐 Environment Variables

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | MySQL connection | `mysql+pymysql://user:pass@localhost/interviai` |
| SECRET_KEY | JWT secret | 32+ char random string |
| GROQ_API_KEY | Groq API key | `gsk_xxxxx` |
| ALGORITHM | JWT algorithm | `HS256` |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry | `30` |
| GOOGLE_CLIENT_ID | Google OAuth | Required for OAuth |
| GOOGLE_CLIENT_SECRET | Google OAuth secret | Required for OAuth |
| DEBUG | Debug mode | `True` or `False` |
| ENVIRONMENT | Environment | `development` or `production` |

### Frontend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| VITE_API_URL | Backend URL | `http://localhost:8000` |
| VITE_APP_NAME | App name | `InterviAI` |
| VITE_APP_VERSION | Version | `1.0.0` |

---

## 🌐 API Endpoints Summary

```
POST   /auth/register              # Register
POST   /auth/login                 # Login
POST   /auth/refresh               # Refresh token
GET    /auth/profile               # Get profile
GET    /auth/verify                # Verify auth

POST   /interview/start            # Start session
POST   /interview/generate-question/{session_id}
POST   /interview/submit-answer    # Submit answer
POST   /interview/end/{session_id} # End session
GET    /interview/session/{session_id}
GET    /interview/questions/{session_id}
GET    /interview/answer/{answer_id}

GET    /analytics/dashboard        # Dashboard
GET    /analytics/history          # History
GET    /analytics/report/{session_id}
GET    /analytics/strengths-weaknesses
GET    /analytics/performance-trend
GET    /analytics/category-performance

GET    /admin/users                # (Admin only)
GET    /admin/statistics           # (Admin only)
DELETE /admin/users/{user_id}      # (Admin only)
GET    /admin/sessions             # (Admin only)

GET    /health                     # Health check
GET    /                           # API info
```

---

## 🗄️ Database Tables

```
users
├─ id (PK)
├─ name, email, password
├─ role (USER/ADMIN)
├─ is_active
└─ created_at, updated_at

interview_sessions
├─ id (PK)
├─ user_id (FK)
├─ interview_type
├─ status (IN_PROGRESS/COMPLETED)
├─ overall_score
└─ started_at, completed_at

questions
├─ id (PK)
├─ session_id (FK)
├─ question_text
├─ category
├─ difficulty
└─ question_type

answers
├─ id (PK)
├─ question_id (FK)
├─ user_answer
├─ score
├─ ai_feedback
└─ ideal_answer

analytics
├─ id (PK)
├─ user_id (FK, UNIQUE)
├─ total_interviews
├─ average_score
└─ strengths, weaknesses (JSON)

interview_reports
├─ id (PK)
├─ session_id (FK)
├─ user_id (FK)
├─ overall_score
└─ summary, pdf_url
```

---

## 🔧 Adding New Features

### Add New API Endpoint

1. **Create model** (if needed) in `backend/app/models/models.py`
2. **Create schema** in `backend/app/schemas/schemas.py`
3. **Create route** in `backend/app/routes/new_route.py`
4. **Include router** in `backend/app/main.py`

### Add New Page

1. **Create component** in `frontend/src/pages/NewPage.jsx`
2. **Add route** in `frontend/src/App.jsx`
3. **Add navigation** in `frontend/src/components/Navbar.jsx`

### Add New Service Method

1. **Add method** to service class in `backend/app/services/`
2. **Use in route** via dependency injection
3. **Test with API client**

---

## 📱 Common Patterns

### API Call with Error Handling

```javascript
// Frontend
try {
  const response = await api.post('/endpoint', data);
  setData(response.data);
} catch (error) {
  setError(error.response?.data?.detail || 'Error');
}
```

### Protected API Route

```python
# Backend
from app.utils.auth import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    return {"user": current_user}
```

### Auth Context Usage

```javascript
// Frontend
const { isAuthenticated, user, login, logout } = useAuth();
```

---

## 🧪 Testing

### Backend Test Example

```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register():
    response = client.post("/auth/register", json={
        "name": "Test",
        "email": "test@example.com",
        "password": "TestPassword123"
    })
    assert response.status_code == 200
```

### Frontend Test Example

```javascript
// src/__tests__/components.test.jsx
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '../contexts/AuthContext';

test('renders navbar', () => {
  render(<Navbar />, { wrapper: AuthProvider });
  expect(screen.getByText('InterviAI')).toBeInTheDocument();
});
```

---

## 🚀 Performance Tips

### Backend
- Use database indexes
- Implement Redis caching
- Use connection pooling
- Optimize N+1 queries

### Frontend
- Code split with React.lazy
- Memoize expensive components
- Lazy load images
- Minimize bundle size

### Database
- Regular VACUUM/OPTIMIZE
- Monitor slow queries
- Archive old data
- Use read replicas

---

## 📊 Monitoring

### Key Metrics to Track
- API response time
- Database query time
- Error rate
- User engagement
- AI evaluation accuracy
- Token refresh frequency

### Logging Levels
```python
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

---

## 🐛 Debug Mode

### Backend
```python
# In app/main.py
if settings.DEBUG:
    # Enable query logging
    # Enable stack traces
    # Enable detailed error responses
```

### Frontend
```javascript
// In .env
VITE_DEBUG=true

// In code
if (import.meta.env.VITE_DEBUG) {
    console.log('Debug info');
}
```

---

## 📝 Code Style

### Backend (Python)
```python
# Follow PEP 8
# Use type hints
# Document functions with docstrings
# Use meaningful variable names
```

### Frontend (JavaScript)
```javascript
// Use meaningful component names
// Keep components small and focused
// Use Tailwind CSS utilities
// Follow React best practices
```

---

## 🔄 Git Workflow

```bash
# Feature development
git checkout -b feature/feature-name
git add .
git commit -m "Add feature description"
git push origin feature/feature-name
# Open PR on GitHub

# Before pushing
git pull origin main
git rebase main (if needed)
git push origin feature/feature-name --force-with-lease
```

---

## 📞 Getting Help

- Check existing issues on GitHub
- Review documentation in `/docs`
- Check API docs at `http://localhost:8000/docs`
- Ask questions in discussions
- Email: support@interviai.com

---

## ✅ Pre-commit Checklist

- [ ] Tests pass
- [ ] No console errors
- [ ] Code formatted (Prettier/Black)
- [ ] No secrets in code
- [ ] Documentation updated
- [ ] PR description clear
- [ ] Related issues linked

---

**Last Updated**: January 2024  
**Version**: 1.0.0
