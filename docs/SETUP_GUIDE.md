# InterviAI Complete Setup Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- Groq API key (get from https://console.groq.com)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/interviai.git
cd interviai

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env and add your Groq API key
GROQ_API_KEY=your_api_key_here
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

### 3. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📋 Complete Manual Setup

### Backend Setup

#### Step 1: Python Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configure Database

**Option A: MySQL (Production)**

```bash
# Create MySQL database
mysql -u root -p
> CREATE DATABASE interviai;
> CREATE USER 'interviai'@'localhost' IDENTIFIED BY 'password';
> GRANT ALL PRIVILEGES ON interviai.* TO 'interviai'@'localhost';
> FLUSH PRIVILEGES;
> EXIT;

# Update backend/.env
DATABASE_URL=mysql+pymysql://interviai:password@localhost:3306/interviai
```

**Option B: SQLite (Development)**

```bash
# Update backend/.env
DATABASE_URL=sqlite:///./test.db
```

#### Step 3: Configure Groq API

```bash
# backend/.env
GROQ_API_KEY=your_groq_api_key
```

Get your free Groq API key:
1. Go to https://console.groq.com
2. Sign up/Login
3. Create API key
4. Copy and paste in .env

#### Step 4: Run Backend

```bash
# Inside backend directory with venv activated
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

Access API documentation: http://localhost:8000/docs

---

### Frontend Setup

#### Step 1: Node Dependencies

```bash
cd frontend

# Install dependencies
npm install
```

#### Step 2: Configure Environment

```bash
# .env (already copied from .env.example)
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=InterviAI
```

#### Step 3: Run Frontend

```bash
# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## 📁 Project Structure

```
interviai/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Main application
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routes/            # API routes
│   │   ├── services/          # Business logic
│   │   ├── utils/             # Utility functions
│   │   └── middleware/        # Middleware
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Docker configuration
│   ├── .env.example          # Environment template
│   └── README.md
│
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── contexts/         # React contexts
│   │   ├── hooks/            # Custom hooks
│   │   ├── styles/           # CSS files
│   │   ├── App.jsx           # Main app component
│   │   └── main.jsx          # Entry point
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration
│   ├── tailwind.config.js    # Tailwind configuration
│   ├── Dockerfile           # Docker configuration
│   ├── .env.example         # Environment template
│   └── README.md
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # System architecture
│   ├── DATABASE_SCHEMA.md    # Database design
│   ├── API_DOCUMENTATION.md  # API reference
│   ├── DEPLOYMENT.md         # Deployment guide
│   └── SETUP_GUIDE.md        # This file
│
├── docker-compose.yml        # Docker Compose config
└── README.md                # Project overview
```

---

## 🔐 Authentication Flow

### Register

1. User fills registration form
2. Frontend sends to `/auth/register`
3. Backend hashes password and creates user
4. Returns JWT tokens
5. Frontend stores tokens in localStorage

### Login

1. User enters credentials
2. Frontend sends to `/auth/login`
3. Backend verifies credentials
4. Returns JWT tokens
5. Frontend stores tokens

### Protected Routes

1. User accesses protected page
2. Frontend checks if authenticated
3. If not, redirects to login
4. If yes, includes token in API requests

---

## 🧪 Testing the Application

### Test User Registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPassword123"
  }'
```

### Test Interview Start

```bash
# 1. Get token from login response
TOKEN="your_access_token"

# 2. Start interview
curl -X POST http://localhost:8000/interview/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_type": "TECHNICAL",
    "category": "Java",
    "difficulty": "MEDIUM"
  }'
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version (need 3.11+)
python --version

# Check if port 8000 is in use
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Try different port
uvicorn app.main:app --port 8001
```

### Database connection error

```bash
# Check MySQL is running
mysql -u root -p -e "SELECT 1"

# Check DATABASE_URL is correct
echo $DATABASE_URL

# Try SQLite instead (for testing)
# Update DATABASE_URL=sqlite:///./test.db in .env
```

### Frontend can't reach backend

```bash
# Check VITE_API_URL in .env
cat frontend/.env

# Check backend is running
curl http://localhost:8000/health

# Check CORS settings in backend
# backend/app/main.py - CORS configuration
```

### Module not found errors

```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

---

## 🚢 Deployment Quick Commands

### Docker Compose (All Services)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild images
docker-compose up -d --build
```

### Manual Deployment

**Backend to Render:**
```bash
# Connect GitHub and deploy directly from Render dashboard
# https://render.com/docs/deploy-from-github
```

**Frontend to Vercel:**
```bash
# Connect GitHub and deploy directly from Vercel dashboard
# https://vercel.com/import
```

---

## 📊 Available Interview Types

### Technical
- Java
- Python
- JavaScript/React
- SQL
- System Design
- Data Structures & Algorithms

### HR (Behavioral)
- Situation-Based Questions
- Conflict Resolution
- Leadership
- Teamwork
- Problem-Solving

### Mixed
- Combination of Technical and HR

---

## 🎯 Features Implemented

✅ User Authentication (Register/Login)
✅ JWT Token Management
✅ Interview Sessions
✅ AI Question Generation (via Groq)
✅ Answer Evaluation & Feedback
✅ User Analytics & Dashboard
✅ Interview History & Reports
✅ Admin Dashboard
✅ Role-Based Access Control

---

## 🔧 Configuration Reference

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | Database connection | mysql+pymysql://user:pass@host/db |
| SECRET_KEY | JWT secret | 32+ character random string |
| GROQ_API_KEY | Groq API key | gsk_... |
| DEBUG | Debug mode | True/False |
| ENVIRONMENT | Environment | development/production |

### Frontend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| VITE_API_URL | Backend URL | http://localhost:8000 |
| VITE_APP_NAME | App name | InterviAI |

---

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` folder
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Email**: support@interviai.com

---

## 📝 Next Steps

1. ✅ Set up environment
2. ✅ Run both backend and frontend
3. ✅ Create test account
4. ✅ Start practice interview
5. ✅ Review analytics
6. ✅ Deploy to production

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- Groq API for AI capabilities
- React & FastAPI communities
- All contributors

---

**Last Updated**: January 2024
**Version**: 1.0.0
