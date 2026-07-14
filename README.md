# 🎯 InterviAI - AI-Powered Interview Preparation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

A production-ready AI-powered platform that helps users master interviews through interactive practice sessions, AI-generated questions, intelligent feedback, and comprehensive performance analytics.

## 🌟 Key Features

### 🤖 AI-Powered Interview Questions
- Intelligent question generation using Groq API (Llama 3)
- Support for multiple domains: Java, Python, React, SQL, HR, and more
- Difficulty levels: Easy, Medium, Hard
- Context-aware follow-up questions

### 📊 Intelligent Answer Evaluation
- Real-time answer evaluation using AI
- Scoring across multiple dimensions:
  - Technical accuracy
  - Completeness
  - Clarity
  - Communication skills
- Personalized feedback and improvement suggestions
- Ideal answer generation

### 📈 Comprehensive Analytics
- Performance dashboard with key metrics
- Interview history and trend analysis
- Category-wise performance breakdown
- Strengths and weaknesses identification
- Detailed analytics reports

### 🔐 Enterprise-Grade Security
- JWT-based authentication
- Google OAuth integration
- Role-based access control (RBAC)
- Password hashing with bcrypt
- HTTPS support

### 💾 Production-Ready Backend
- FastAPI with async support
- MySQL database with optimized schema
- Comprehensive error handling
- API documentation (Swagger/OpenAPI)
- Database migrations ready

### 🎨 Modern Frontend UI
- React 18 with Vite
- Dark theme with glassmorphism design
- Responsive mobile-first design
- Real-time interactive components
- Interactive charts and analytics

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│     React Frontend (Vite + Tailwind)    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      FastAPI Backend (Python)           │
├─────────────────────────────────────────┤
│  Routes │ Services │ Models │ Schemas  │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼──┐  ┌──▼────┐  ┌──▼─────┐
    │MySQL │  │ Groq  │  │ Redis  │
    │      │  │ API   │  │ Cache  │
    └──────┘  └───────┘  └────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- Groq API key (free from https://console.groq.com)

### 5-Minute Setup

```bash
# Clone repository
git clone https://github.com/yourusername/interviai.git
cd interviai

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Add your Groq API key to backend/.env
GROQ_API_KEY=your_api_key_here

# Start with Docker Compose
docker-compose up -d

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

See [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed setup instructions.

## 📁 Project Structure

```
interviai/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── services/       # API client
│   │   ├── contexts/       # React contexts
│   │   └── styles/         # CSS files
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── README.md
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT.md
│   └── SETUP_GUIDE.md
│
├── docker-compose.yml
└── README.md
```

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **Lucide React** - Icons

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Bcrypt** - Password hashing
- **Groq API** - AI integration

### Database
- **MySQL** - Primary database
- **Redis** - Caching (optional)

## 📚 Documentation

- [Complete Architecture Overview](docs/ARCHITECTURE.md)
- [Database Schema Documentation](docs/DATABASE_SCHEMA.md)
- [API Reference Guide](docs/API_DOCUMENTATION.md)
- [Deployment Instructions](docs/DEPLOYMENT.md)
- [Setup & Installation Guide](docs/SETUP_GUIDE.md)

## 🎓 Interview Types Supported

### Technical Interviews
- Java
- Python
- JavaScript/React
- SQL & Databases
- System Design
- Data Structures & Algorithms

### HR Interviews
- Behavioral Questions
- Conflict Resolution
- Leadership & Teamwork
- Communication Skills
- Problem-Solving

### Mixed Mode
- Combination of technical and HR questions

## 🔄 Interview Flow

```
1. User Login/Register
   ↓
2. Start Interview (Select Type & Category)
   ↓
3. AI Generates Question
   ↓
4. User Answers Question
   ↓
5. AI Evaluates Answer
   ↓
6. User Receives Feedback & Scores
   ↓
7. Generate Follow-up Question (Optional)
   ↓
8. Repeat or End Interview
   ↓
9. Generate & View Report
   ↓
10. Track Progress in Analytics
```

## 🔐 Security Features

✅ **Password Security**
- Bcrypt hashing (10+ rounds)
- Minimum 8 character requirement

✅ **Authentication**
- JWT with 30-minute expiry
- Refresh tokens for extended sessions
- Automatic token rotation

✅ **Authorization**
- Role-based access control
- Protected API endpoints
- User data isolation

✅ **Data Protection**
- SQL injection prevention
- CORS policy enforcement
- HTTPS in production
- Input validation on all endpoints

✅ **Infrastructure**
- Environment variable configuration
- Secure headers (X-Frame-Options, CSP, etc.)
- HTTPS ready

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - Login
- `GET /auth/profile` - Get profile

### Interview
- `POST /interview/start` - Start session
- `POST /interview/generate-question/{id}` - Get question
- `POST /interview/submit-answer` - Submit & evaluate
- `POST /interview/end/{id}` - End session

### Analytics
- `GET /analytics/dashboard` - Dashboard data
- `GET /analytics/history` - Interview history
- `GET /analytics/report/{id}` - Session report
- `GET /analytics/performance-trend` - Trend data

Full API documentation: [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

## 🚀 Deployment

### Quick Deployment

**Frontend → Vercel:**
```bash
# Connect GitHub and auto-deploy from Vercel dashboard
```

**Backend → Render:**
```bash
# Connect GitHub and auto-deploy from Render dashboard
```

**Database → Managed Service:**
- AWS RDS
- Render MySQL
- DigitalOcean Managed Database

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 💰 Cost Estimate

| Service | Cost | Notes |
|---------|------|-------|
| Frontend (Vercel) | Free - $20/mo | Generous free tier |
| Backend (Render) | $7 - $100/mo | Starts at $7/mo |
| Database | $15 - $300/mo | Depends on scale |
| Groq API | Free | Generous free tier |
| **Total** | **$22 - $420/mo** | Can start free |

## 🧪 Testing the API

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"Test123456"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123456"}'

# Start interview
curl -X POST http://localhost:8000/interview/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interview_type":"TECHNICAL","category":"Java","difficulty":"MEDIUM"}'
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

### Frontend can't reach backend
- Verify `VITE_API_URL` in frontend/.env
- Check backend is running
- Review browser console for errors

### Database connection error
- Verify DATABASE_URL in backend/.env
- Check MySQL is running
- Test connection: `mysql -u user -p`

See [SETUP_GUIDE.md](docs/SETUP_GUIDE.md#-troubleshooting) for more solutions.

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq API** - For Llama 3 LLM capabilities
- **FastAPI** - Modern web framework
- **React** - UI library
- **Tailwind CSS** - Utility-first CSS framework

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/interviai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/interviai/discussions)
- **Email**: support@interviai.com
- **Documentation**: Check `/docs` folder

## 🗺️ Roadmap

- [ ] Voice interview support (speech-to-text)
- [ ] Video interview recording
- [ ] Resume-based questions
- [ ] Real-time collaboration
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Interview scheduling
- [ ] Peer review system
- [ ] Skill badges & certificates
- [ ] Mentor matching

## 📊 Project Stats

- **Backend Files**: 15+
- **Frontend Components**: 10+
- **Database Tables**: 8
- **API Endpoints**: 20+
- **Lines of Code**: 5000+
- **Documentation**: Comprehensive

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Status**: Production Ready ✅

Made with ❤️ for interview preparation
