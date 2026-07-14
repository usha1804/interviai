# InterviAI Backend

FastAPI-based backend for the InterviAI interview preparation platform.

## Overview

RESTful API built with FastAPI, SQLAlchemy, and integrated with Groq AI for intelligent interview question generation and answer evaluation.

## Features

- 🔐 JWT Authentication with Google OAuth support
- 🤖 AI-powered question generation using Groq API (Llama 3)
- 📊 Intelligent answer evaluation and feedback
- 📈 User analytics and performance tracking
- 🛡️ Role-based access control (RBAC)
- 📝 Complete database schema with analytics
- 🚀 Production-ready error handling and logging

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: MySQL
- **Authentication**: JWT + Bcrypt
- **AI**: Groq API (Llama 3)
- **Validation**: Pydantic v2
- **Server**: Uvicorn

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Server

```bash
uvicorn app.main:app --reload
```

Server will start at `http://localhost:8000`

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models/
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py       # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── interview.py     # Interview endpoints
│   │   ├── analytics.py     # Analytics endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── services/
│   │   ├── ai_service.py    # AI integration
│   │   └── interview_service.py  # Interview logic
│   ├── utils/
│   │   └── auth.py          # Auth utilities
│   └── middleware/          # Custom middleware
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Environment Variables

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/interviai

# JWT
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Groq AI
GROQ_API_KEY=your-groq-api-key

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Application
DEBUG=True
ENVIRONMENT=development
```

## Database Setup

```bash
# Create MySQL database
mysql -u root -p
> CREATE DATABASE interviai;
> EXIT;

# Tables are created automatically on first run
# SQLAlchemy will create all tables based on models
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh token
- `GET /auth/profile` - Get current user profile
- `GET /auth/verify` - Verify authentication

### Interview
- `POST /interview/start` - Start new interview
- `POST /interview/generate-question/{session_id}` - Generate question
- `POST /interview/submit-answer` - Submit and evaluate answer
- `POST /interview/end/{session_id}` - End interview session
- `GET /interview/session/{session_id}` - Get session details

### Analytics
- `GET /analytics/dashboard` - Get dashboard data
- `GET /analytics/history` - Get interview history
- `GET /analytics/report/{session_id}` - Get interview report
- `GET /analytics/performance-trend` - Get performance trend
- `GET /analytics/category-performance` - Get category performance

### Admin
- `GET /admin/users` - List all users
- `GET /admin/statistics` - Get platform statistics
- `DELETE /admin/users/{user_id}` - Delete user
- `GET /admin/sessions` - List all sessions

## AI Features

### Question Generation
Generates realistic interview questions using Groq's Llama 3 AI based on:
- Category (Java, Python, React, etc.)
- Difficulty level (Easy, Medium, Hard)
- Interview type (Technical, HR, Mixed)

### Answer Evaluation
Evaluates user answers and provides:
- Technical accuracy score
- Completeness score
- Clarity score
- Communication score
- Strengths identification
- Improvement suggestions
- Ideal answer generation

### Follow-up Questions
Generates contextual follow-up questions based on:
- Original question
- User's answer
- Knowledge gaps identified

## Authentication Flow

1. **Register**: User creates account with email/password
2. **Login**: User authenticates, receives JWT tokens
3. **Token Storage**: Frontend stores access and refresh tokens
4. **API Requests**: Include JWT in Authorization header
5. **Token Refresh**: Automatic refresh when token expires

## Error Handling

All endpoints return structured error responses:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Deployment

### Docker

```bash
# Build image
docker build -t interviai-backend:latest .

# Run container
docker run -d -p 8000:8000 \
  -e DATABASE_URL=mysql://... \
  -e GROQ_API_KEY=... \
  interviai-backend:latest
```

### Docker Compose

```bash
docker-compose up -d
```

See [DEPLOYMENT.md](/docs/DEPLOYMENT.md) for detailed deployment instructions.

## Testing

```bash
# Run tests (to be implemented)
pytest

# Test coverage
pytest --cov=app
```

## Performance

- Async/await for non-blocking operations
- Database connection pooling
- Response caching with Redis
- Efficient query optimization

## Security

- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention via SQLAlchemy
- ✅ Rate limiting ready
- ✅ HTTPS support in production

## Monitoring

- Application logging to stdout
- Database query logging (dev mode)
- Error tracking ready (Sentry integration)
- Performance metrics collection

## Contributing

1. Create feature branch
2. Make changes
3. Write tests
4. Submit pull request

## Documentation

- [Architecture](../docs/ARCHITECTURE.md)
- [Database Schema](../docs/DATABASE_SCHEMA.md)
- [API Documentation](../docs/API_DOCUMENTATION.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)

## Support

- Issues: GitHub Issues
- Email: support@interviai.com
- Documentation: [https://github.com/yourusername/interviai](https://github.com/yourusername/interviai)

## License

MIT License - See LICENSE file

---

**Version**: 1.0.0  
**Last Updated**: January 2024
