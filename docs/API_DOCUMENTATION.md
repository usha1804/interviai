# InterviAI API Documentation

## Base URL
```
Development: http://localhost:8000
Production: https://api.interviai.com
```

## Authentication
All protected endpoints require JWT authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Response Format
All responses are in JSON format:

```json
{
  "data": {...},
  "error": null,
  "status": "success"
}
```

## Error Responses
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Authentication Endpoints

### 1. Register User
**POST** `/auth/register`

Register a new user account.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `400`: Email already registered
- `422`: Validation error

---

### 2. Login User
**POST** `/auth/login`

Authenticate user and get tokens.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401`: Invalid credentials
- `403`: Account disabled

---

### 3. Refresh Token
**POST** `/auth/refresh`

Get a new access token using refresh token.

**Request Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401`: Invalid refresh token

---

### 4. Get Profile
**GET** `/auth/profile`

Get current user profile.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "USER",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Interview Endpoints

### 1. Start Interview
**POST** `/interview/start`

Start a new interview session.

**Request:**
```json
{
  "interview_type": "TECHNICAL",
  "category": "Java",
  "difficulty": "MEDIUM"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "interview_type": "TECHNICAL",
  "status": "IN_PROGRESS",
  "overall_score": null,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "total_questions": 0
}
```

---

### 2. Generate Question
**POST** `/interview/generate-question/{session_id}`

Generate an interview question for the session.

**Query Parameters:**
- `category` (string): Question category (Java, React, Python, etc.)
- `difficulty` (string): EASY, MEDIUM, HARD

**Response:** `200 OK`
```json
{
  "id": 1,
  "session_id": 1,
  "question_text": "What is Java's garbage collection mechanism?",
  "category": "Java",
  "difficulty": "MEDIUM",
  "question_type": "TECHNICAL",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### 3. Submit Answer
**POST** `/interview/submit-answer`

Submit user answer and get AI evaluation.

**Request:**
```json
{
  "question_id": 1,
  "user_answer": "Garbage collection is an automatic memory management feature..."
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "question_id": 1,
  "user_answer": "Garbage collection is an automatic memory management feature...",
  "score": 8.5,
  "technical_accuracy": 9,
  "completeness": 8,
  "clarity": 8,
  "communication_score": 8,
  "ai_feedback": "Good understanding of GC mechanisms...",
  "strengths": "Clear explanation with specific examples",
  "improvements": "Could mention specific GC algorithms",
  "ideal_answer": "Java's GC is an automatic memory management...",
  "answered_at": "2024-01-15T10:35:00Z"
}
```

---

### 4. End Interview
**POST** `/interview/end/{session_id}`

Complete interview session and calculate overall score.

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "interview_type": "TECHNICAL",
  "status": "COMPLETED",
  "overall_score": 8.2,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:50:00Z",
  "total_questions": 5,
  "duration_minutes": 20
}
```

---

## Analytics Endpoints

### 1. Get Dashboard
**GET** `/analytics/dashboard`

Get user's analytics dashboard data.

**Response:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "total_interviews": 10,
  "average_score": 7.8,
  "best_score": 9.2,
  "worst_score": 6.5,
  "technical_score": 8.1,
  "communication_score": 7.5,
  "hr_score": 7.0,
  "strengths": ["Problem Solving", "Communication"],
  "weaknesses": ["Time Management", "Depth of Knowledge"]
}
```

---

### 2. Get Interview History
**GET** `/analytics/history`

Get user's interview history.

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Number of results (default: 10)

**Response:** `200 OK`
```json
{
  "total_count": 15,
  "interviews": [
    {
      "id": 15,
      "interview_type": "TECHNICAL",
      "overall_score": 8.5,
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:50:00Z",
      "duration_minutes": 20,
      "status": "COMPLETED"
    }
  ]
}
```

---

### 3. Get Interview Report
**GET** `/analytics/report/{session_id}`

Get detailed report for a specific interview.

**Response:** `200 OK`
```json
{
  "id": 1,
  "session_id": 1,
  "overall_score": 8.2,
  "technical_score": 8.5,
  "communication_score": 7.9,
  "summary": "Strong technical foundation with good communication skills...",
  "strengths_list": ["Problem solving", "Clear explanation"],
  "improvements_list": ["Time management", "Covering edge cases"],
  "recommendations": ["Practice system design", "Study advanced algorithms"],
  "pdf_url": "https://example.com/reports/1.pdf",
  "created_at": "2024-01-15T10:50:00Z"
}
```

---

### 4. Get Performance Trend
**GET** `/analytics/performance-trend`

Get performance trend over time.

**Response:** `200 OK`
```json
{
  "trend": [
    {
      "date": "2024-01-10T10:30:00Z",
      "score": 7.5,
      "interview_type": "TECHNICAL"
    },
    {
      "date": "2024-01-12T14:20:00Z",
      "score": 8.2,
      "interview_type": "HR"
    }
  ],
  "total_sessions": 10
}
```

---

### 5. Get Category Performance
**GET** `/analytics/category-performance`

Get performance breakdown by category.

**Response:** `200 OK`
```json
{
  "categories": [
    {
      "category": "Java",
      "questions_answered": 5,
      "average_score": 8.2,
      "max_score": 9.0,
      "min_score": 7.5
    },
    {
      "category": "React",
      "questions_answered": 4,
      "average_score": 7.8,
      "max_score": 8.5,
      "min_score": 7.0
    }
  ]
}
```

---

## Admin Endpoints

### 1. List Users (Admin Only)
**GET** `/admin/users`

List all users in the system.

**Query Parameters:**
- `skip` (int): Pagination offset
- `limit` (int): Number of results

**Response:** `200 OK`
```json
{
  "total_count": 1250,
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "USER",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 2. Get Statistics (Admin Only)
**GET** `/admin/statistics`

Get platform-wide statistics.

**Response:** `200 OK`
```json
{
  "total_sessions": 5000,
  "completed_sessions": 4500,
  "average_score": 7.9,
  "most_common_type": "TECHNICAL",
  "most_common_category": "Java"
}
```

---

### 3. Delete User (Admin Only)
**DELETE** `/admin/users/{user_id}`

Soft delete a user account.

**Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Auth required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

---

## Rate Limiting

Coming soon: API rate limiting based on user tier

- Free: 100 requests/hour
- Pro: 1000 requests/hour
- Enterprise: Unlimited

---

## Example cURL Requests

### Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePassword123"
  }'
```

### Start Interview
```bash
curl -X POST http://localhost:8000/interview/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_type": "TECHNICAL",
    "category": "Java",
    "difficulty": "MEDIUM"
  }'
```

### Submit Answer
```bash
curl -X POST http://localhost:8000/interview/submit-answer \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "user_answer": "Your comprehensive answer here..."
  }'
```
