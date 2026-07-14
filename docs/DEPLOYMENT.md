# InterviAI Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Git
- Node.js 18+ (for local dev)
- Python 3.11+ (for local dev)
- MySQL 8.0+ (for local dev)

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/interviai.git
cd interviai
```

### 2. Environment Configuration

**Backend (.env)**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/interviai
SECRET_KEY=your-secret-key-minimum-32-characters
GROQ_API_KEY=your-groq-api-key
DEBUG=True
ENVIRONMENT=development
```

**Frontend (.env)**
```bash
cp frontend/.env.example frontend/.env
```

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=InterviAI
```

### 3. Start Services with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

This starts:
- MySQL on localhost:3306
- Backend on localhost:8000
- Frontend on localhost:5173
- Redis on localhost:6379

### 4. Manual Local Setup (Without Docker)

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (create tables)
python -m app.main  # This creates tables automatically

# Start server
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Production Deployment

### Option 1: Render (Recommended)

#### Deploy Backend to Render

1. **Push code to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Create Render Account**: https://render.com

3. **Create Web Service**:
   - Connect GitHub repository
   - Select `backend` as root directory
   - Environment: `python-3.11`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

4. **Set Environment Variables** in Render dashboard:
```
DATABASE_URL=mysql://user:password@host:3306/interviai
SECRET_KEY=your-production-secret-key
GROQ_API_KEY=your-groq-api-key
DEBUG=False
ENVIRONMENT=production
```

5. **Create PostgreSQL or MySQL Database**:
   - Use Render's database service or external MySQL host
   - Update DATABASE_URL

#### Deploy Frontend to Vercel

1. **Create Vercel Account**: https://vercel.com

2. **Import Project**:
   - Connect GitHub repository
   - Select `frontend` directory
   - Framework preset: Vite
   - Build command: `npm run build`
   - Output directory: `dist`

3. **Set Environment Variables**:
```
VITE_API_URL=https://your-backend-url.onrender.com
```

4. **Deploy**: Push to main branch (auto-deploys)

---

### Option 2: AWS Deployment

#### Backend (ECS + RDS)

1. **Create RDS MySQL Instance**:
```bash
aws rds create-db-instance \
  --db-instance-identifier interviai-mysql \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --master-username admin \
  --master-user-password YourSecurePassword
```

2. **Create ECR Repository**:
```bash
aws ecr create-repository --repository-name interviai-backend
```

3. **Build and Push Docker Image**:
```bash
# Build
docker build -t interviai-backend:latest backend/

# Tag
docker tag interviai-backend:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/interviai-backend:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/interviai-backend:latest
```

4. **Deploy to ECS**:
   - Create ECS cluster
   - Create task definition using Docker image
   - Create service and run tasks

#### Frontend (CloudFront + S3)

1. **Build Frontend**:
```bash
cd frontend
npm run build
```

2. **Create S3 Bucket**:
```bash
aws s3 mb s3://interviai-frontend --region us-east-1
```

3. **Upload Files**:
```bash
aws s3 sync dist/ s3://interviai-frontend/ --delete
```

4. **Create CloudFront Distribution**:
   - Origin: S3 bucket
   - Default cache behavior: Allow GET, HEAD, OPTIONS
   - Enable HTTPS

---

### Option 3: Kubernetes Deployment

1. **Create Docker Images**:
```bash
docker build -t interviai-backend:1.0.0 backend/
docker build -t interviai-frontend:1.0.0 frontend/
```

2. **Create Kubernetes Manifests** (k8s/):

**backend-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: interviai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: interviai-backend
  template:
    metadata:
      labels:
        app: interviai-backend
    spec:
      containers:
      - name: backend
        image: interviai-backend:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: interviai-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: interviai-secrets
              key: secret-key
---
apiVersion: v1
kind: Service
metadata:
  name: interviai-backend-service
spec:
  selector:
    app: interviai-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

3. **Deploy to Kubernetes**:
```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

---

## Database Setup

### Local MySQL
```bash
# Create database
mysql -u root -p
CREATE DATABASE interviai;
CREATE USER 'interviai_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON interviai.* TO 'interviai_user'@'localhost';
FLUSH PRIVILEGES;
```

### Managed Services
- **Render MySQL**: https://render.com/docs/mysql
- **AWS RDS**: https://aws.amazon.com/rds/
- **DigitalOcean Managed Database**: https://www.digitalocean.com/products/managed-databases

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push backend
      run: |
        docker build -t interviai-backend:latest backend/
        docker push your-registry/interviai-backend:latest
    
    - name: Deploy to Render
      run: |
        curl https://api.render.com/deploy/${{ secrets.BACKEND_SERVICE_ID }}?key=${{ secrets.RENDER_DEPLOY_KEY }}
    
    - name: Build and deploy frontend
      run: |
        cd frontend
        npm install
        npm run build
    
    - name: Deploy to Vercel
      env:
        VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
      run: |
        npm install -g vercel
        vercel --prod
```

---

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up firewall rules
- [ ] Enable CORS only for allowed domains
- [ ] Rotate JWT secret key
- [ ] Enable database encryption
- [ ] Regular security audits

### Performance
- [ ] Enable Redis caching
- [ ] Set up CDN for static assets
- [ ] Enable gzip compression
- [ ] Optimize database indexes
- [ ] Set up monitoring and alerts
- [ ] Configure auto-scaling

### Reliability
- [ ] Set up automated backups (daily)
- [ ] Configure health checks
- [ ] Set up log aggregation
- [ ] Error tracking (Sentry)
- [ ] Load testing and capacity planning
- [ ] Disaster recovery plan

### Monitoring
```bash
# Recommended tools:
# - New Relic
# - DataDog
# - Sentry
# - LogRocket
# - Prometheus + Grafana
```

---

## Scaling Considerations

### Horizontal Scaling
```yaml
# Docker Compose - Multiple backend instances
version: '3.8'
services:
  backend:
    build: ./backend
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=mysql://...
```

### Database Scaling
- Read replicas for analytics queries
- Connection pooling (PgBouncer)
- Query caching with Redis
- Sharding if needed

### Frontend Scaling
- CDN distribution (Cloudflare, Akamai)
- Edge caching
- Service workers for offline support

---

## Troubleshooting

### Common Issues

**Database connection failed**:
```bash
# Check MySQL is running
docker-compose ps

# Check connection string
echo $DATABASE_URL
```

**API not responding**:
```bash
# Check backend logs
docker-compose logs backend

# Test endpoint
curl http://localhost:8000/health
```

**Frontend can't reach backend**:
```bash
# Check CORS settings
# Check VITE_API_URL environment variable
# Check frontend .env file
```

### Logs
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs (dev console)
# Ctrl+Shift+J in browser

# Database logs
docker-compose logs -f mysql
```

---

## Cost Estimation (Monthly)

### Render
- Backend: $7 - $100/month
- Database: $15 - $300/month

### Vercel
- Frontend: Free - $20/month

### AWS
- RDS MySQL: $15 - $300/month
- ECS: $0.04/hour per GB

### Total: $22 - $420/month (depends on scale)

---

## Support & Resources

- Documentation: `/docs` folder
- Issue Tracker: GitHub Issues
- Discord Community: [Link]
- Email Support: support@interviai.com

