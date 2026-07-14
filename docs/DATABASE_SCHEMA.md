# InterviAI Database Schema

## Overview
MySQL 8.0 database with normalized schema for storing user data, interview sessions, questions, answers, and analytics.

## Tables

### 1. Users
Stores user account information.

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255),
    role VARCHAR(50) DEFAULT 'USER',  -- USER, ADMIN
    google_id VARCHAR(255) UNIQUE,
    profile_picture VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (email),
    INDEX (google_id)
);
```

### 2. InterviewSessions
Stores interview session records.

```sql
CREATE TABLE interview_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    interview_type VARCHAR(50) NOT NULL,  -- TECHNICAL, HR, MIXED
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    overall_score FLOAT,
    status VARCHAR(50) DEFAULT 'IN_PROGRESS',  -- IN_PROGRESS, COMPLETED, ABANDONED
    total_questions INT DEFAULT 0,
    duration_minutes INT,
    session_metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX (user_id),
    INDEX (status),
    INDEX (created_at)
);
```

### 3. Questions
Stores interview questions.

```sql
CREATE TABLE questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    question_text LONGTEXT NOT NULL,
    category VARCHAR(100) NOT NULL,  -- Java, React, HR, Python, SQL, etc.
    difficulty VARCHAR(50) DEFAULT 'MEDIUM',  -- EASY, MEDIUM, HARD
    question_type VARCHAR(50) DEFAULT 'TECHNICAL',  -- TECHNICAL, HR, FOLLOW_UP
    parent_question_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id),
    FOREIGN KEY (parent_question_id) REFERENCES questions(id),
    INDEX (session_id),
    INDEX (category),
    INDEX (difficulty)
);
```

### 4. Answers
Stores user answers with AI evaluations.

```sql
CREATE TABLE answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    user_answer LONGTEXT NOT NULL,
    ai_feedback LONGTEXT,
    ideal_answer LONGTEXT,
    score FLOAT,
    technical_accuracy FLOAT,
    completeness FLOAT,
    clarity FLOAT,
    communication_score FLOAT,
    strengths TEXT,
    improvements TEXT,
    evaluation_metadata JSON,
    answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    INDEX (question_id),
    INDEX (score)
);
```

### 5. Analytics
Stores aggregated user analytics and performance data.

```sql
CREATE TABLE analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    total_interviews INT DEFAULT 0,
    average_score FLOAT,
    best_score FLOAT,
    worst_score FLOAT,
    technical_score FLOAT,
    communication_score FLOAT,
    hr_score FLOAT,
    strengths JSON,  -- Array of strength strings
    weaknesses JSON,  -- Array of weakness strings
    category_performance JSON,  -- Object mapping categories to scores
    topics_covered JSON,  -- Array of topics
    weak_areas JSON,  -- Array of weak areas
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX (user_id)
);
```

### 6. InterviewReports
Stores comprehensive interview reports.

```sql
CREATE TABLE interview_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL,
    overall_score FLOAT NOT NULL,
    technical_score FLOAT,
    communication_score FLOAT,
    summary LONGTEXT,
    strengths_list JSON,  -- Array of strengths
    improvements_list JSON,  -- Array of improvements
    recommendations JSON,  -- Array of recommendations
    performance_metrics JSON,
    time_analysis JSON,
    pdf_url VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX (user_id),
    INDEX (created_at)
);
```

### 7. AIPrompts
Stores AI prompt templates for different features.

```sql
CREATE TABLE ai_prompts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,  -- QUESTION_GEN, EVAL, FOLLOWUP, ANALYSIS
    prompt_template LONGTEXT NOT NULL,
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (category),
    INDEX (is_active)
);
```

### 8. AuditLogs
Stores system activity audit logs.

```sql
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id INT,
    details JSON,
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX (user_id),
    INDEX (created_at)
);
```

## Indexes Strategy

### Performance Indexes
- **Users**: email (frequent queries), google_id (OAuth lookups)
- **InterviewSessions**: user_id (user dashboard), status (filtering), created_at (sorting)
- **Questions**: session_id (fetch by session), category (analytics)
- **Answers**: question_id (fetch answers), score (sorting/filtering)
- **Analytics**: user_id (unique, used frequently)
- **InterviewReports**: user_id (user reports), created_at (listing)

### Query Optimization
```sql
-- Frequently used queries

-- Get user's recent interviews
SELECT * FROM interview_sessions 
WHERE user_id = ? AND status = 'COMPLETED'
ORDER BY completed_at DESC LIMIT 10;

-- Get session questions and answers
SELECT q.*, a.score, a.ai_feedback 
FROM questions q
LEFT JOIN answers a ON q.id = a.question_id
WHERE q.session_id = ?;

-- Get user analytics
SELECT * FROM analytics WHERE user_id = ?;

-- Get category performance
SELECT category, AVG(score) as avg_score, COUNT(*) as count
FROM answers a
JOIN questions q ON a.question_id = q.id
JOIN interview_sessions s ON q.session_id = s.id
WHERE s.user_id = ?
GROUP BY category;
```

## Data Relationships

```
Users (1) ──→ (Many) InterviewSessions
              ↓
              (Many) Questions
              ↓
              (Many) Answers
              ↓
            Analytics

InterviewSessions (1) ──→ (1) InterviewReports

Questions (1) ──→ (Many) Answers
Questions (Self) ──→ Parent/Child Questions (for follow-ups)
```

## Database Constraints

1. **Foreign Key Constraints**: Maintain referential integrity
2. **Unique Constraints**: User email, google_id, analytics per user
3. **Check Constraints**: Score ranges (0-10)
4. **NOT NULL**: Critical fields (user_id, question_text, user_answer)

## Backup Strategy

- Daily automated backups
- Point-in-time recovery capability
- Backup retention: 30 days
- Offsite backup storage

## Migration Strategy

Use Flask-Migrate or Alembic for schema versioning:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Capacity Planning

### Estimated Storage
- 1M users with 10 interviews each = 10M sessions
- Average session: 5 questions, 5 answers
- Each answer: ~2KB (text + feedback)
- Estimated DB size: ~250GB for 1M users

### Scalability Considerations
- Implement archiving of old sessions (>1 year)
- Partitioning on interview_sessions by date
- Read replicas for analytics queries
- Caching frequently accessed analytics
