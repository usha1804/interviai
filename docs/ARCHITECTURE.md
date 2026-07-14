# InterviAI Architecture

## System Overview

InterviAI is a production-ready AI-powered interview preparation platform built with a modern microservices architecture.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  React + Vite + Tailwind CSS (Browser-based SPA)                │
├─────────────────────────────────────────────────────────────────┤
│                         API GATEWAY LAYER                         │
│  Nginx (Reverse Proxy, Load Balancer)                            │
├─────────────────────────────────────────────────────────────────┤
│                         APPLICATION LAYER                         │
│  FastAPI Backend (REST APIs, Business Logic)                     │
├─────────────────────────────────────────────────────────────────┤
│                         AI LAYER                                  │
│  Groq API (Llama 3 LLM for Question Generation & Evaluation)    │
├─────────────────────────────────────────────────────────────────┤
│                         DATA LAYER                                │
│  MySQL (Primary Database)                                        │
│  Redis (Caching & Sessions)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Components

### 1. Frontend (React + Vite)
- **Framework**: React 18 with Vite bundler
- **Styling**: Tailwind CSS with glassmorphism effects
- **State Management**: Context API + Custom Hooks
- **HTTP Client**: Axios with interceptors for auth
- **Routing**: React Router v6
- **Charts**: Recharts for analytics visualization
- **Icons**: Lucide React icons

**Key Features**:
- Responsive dark theme UI
- Real-time form validation
- Protected routes with auth guards
- Automatic token refresh
- Error handling and user feedback

### 2. Backend (FastAPI)
- **Framework**: FastAPI (async/await)
- **ORM**: SQLAlchemy with SQLModel
- **Validation**: Pydantic v2
- **Authentication**: JWT + Bcrypt
- **Database**: MySQL with PyMySQL
- **API Documentation**: Auto-generated OpenAPI (Swagger)

**Key Components**:
- **Routes**: Auth, Interview, Analytics, Admin
- **Services**: AI service, Interview service
- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic request/response models
- **Middleware**: CORS, GZIP compression
- **Error Handling**: Global exception handlers

### 3. AI Integration (Groq API)
- **LLM**: Llama 3 via Groq API
- **Features**:
  - AI question generation
  - Follow-up question generation
  - Answer evaluation
  - Ideal answer generation
  - Performance analysis

### 4. Database (MySQL)
- Relational schema with proper indexing
- Foreign key relationships
- JSON fields for flexible data storage
- Audit logging for compliance

## API Architecture

### RESTful Endpoints

```
Authentication:
  POST   /auth/register
  POST   /auth/login
  POST   /auth/refresh
  POST   /auth/google
  GET    /auth/profile
  GET    /auth/verify

Interview Management:
  POST   /interview/start
  POST   /interview/generate-question/{session_id}
  POST   /interview/submit-answer
  POST   /interview/end/{session_id}
  GET    /interview/session/{session_id}
  GET    /interview/questions/{session_id}
  GET    /interview/answer/{answer_id}

Analytics:
  GET    /analytics/dashboard
  GET    /analytics/history
  GET    /analytics/report/{session_id}
  GET    /analytics/strengths-weaknesses
  GET    /analytics/performance-trend
  GET    /analytics/category-performance

Admin:
  GET    /admin/users
  GET    /admin/statistics
  DELETE /admin/users/{user_id}
  GET    /admin/user/{user_id}
  GET    /admin/ai-prompts
  POST   /admin/ai-prompts
  GET    /admin/sessions
```

## Authentication Flow

```
1. User Registration
   - User submits email + password
   - Password hashed with bcrypt
   - JWT tokens generated (access + refresh)

2. User Login
   - Email/password verified
   - Access token (30 min expiry)
   - Refresh token (7 days expiry)

3. Request Authentication
   - Access token sent in Authorization header
   - Verified using JWT decode
   - Tokens auto-refreshed when expired

4. Role-Based Access Control
   - USER role: Standard features
   - ADMIN role: Admin panel + system management
```

## Data Flow

### Interview Session Flow

```
Start Interview
  ↓
Generate Question (via Groq AI)
  ↓
User Answers Question
  ↓
Submit Answer
  ↓
AI Evaluates Answer (via Groq AI)
  ↓
Store Answer with Evaluation
  ↓
Generate Follow-up Question (optional)
  ↓
Repeat or End Session
  ↓
Generate Report & Update Analytics
```

## Deployment Architecture

### Local Development
```
Docker Compose orchestrates:
- MySQL (port 3306)
- FastAPI Backend (port 8000)
- React Frontend (port 5173)
- Redis (port 6379)
```

### Production Deployment
```
Frontend: Vercel (edge functions + static assets)
Backend: Render (containerized FastAPI)
Database: MySQL (managed service)
Cache: Redis (managed service)
CI/CD: GitHub Actions
```

## Security Measures

1. **Authentication**: JWT with secure token management
2. **Authorization**: Role-based access control (RBAC)
3. **Data Protection**: Password hashing (bcrypt), HTTPS only
4. **API Security**: CORS policies, rate limiting, input validation
5. **Database Security**: SQL prepared statements (SQLAlchemy)
6. **Environment Variables**: Sensitive data in .env files
7. **Headers**: Security headers (X-Frame-Options, CSP, etc.)

## Scalability Considerations

1. **Horizontal Scaling**: Stateless backend allows multiple instances
2. **Database**: Connection pooling with SQLAlchemy
3. **Caching**: Redis for session management and analytics
4. **Load Balancing**: Nginx reverse proxy
5. **CDN**: Vercel Edge Network for frontend assets
6. **API Rate Limiting**: Implement based on user tier

## Monitoring & Logging

- Application logs: stdout/file
- Database queries: SQLAlchemy echo mode (dev only)
- Error tracking: Sentry integration (recommended)
- Analytics: Dashboard metrics

## Performance Optimization

1. **Frontend**:
   - Code splitting with Vite
   - Asset compression
   - Lazy loading components

2. **Backend**:
   - Database query optimization
   - Connection pooling
   - Response caching with Redis

3. **AI Integration**:
   - Prompt template caching
   - Batch processing where possible
   - Response streaming for long operations
