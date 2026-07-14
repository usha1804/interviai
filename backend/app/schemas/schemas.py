"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema"""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=60)


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdateProfile(BaseModel):
    """User profile update schema"""
    name: Optional[str] = None
    profile_picture: Optional[str] = None


# ==================== Authentication Schemas ====================

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class GoogleAuthRequest(BaseModel):
    """Google OAuth request schema"""
    code: str
    redirect_uri: str


class GoogleAuthResponse(BaseModel):
    """Google auth response with token"""
    access_token: str
    user: UserResponse


# ==================== Question Schemas ====================

class QuestionCreate(BaseModel):
    """Question creation schema"""
    question_text: str
    category: str
    difficulty: str = "MEDIUM"
    question_type: str = "TECHNICAL"


class QuestionResponse(BaseModel):
    """Question response schema"""
    id: int
    session_id: int
    question_text: str
    category: str
    difficulty: str
    question_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Answer Schemas ====================

class AnswerSubmit(BaseModel):
    """Answer submission schema"""
    question_id: int
    user_answer: str = Field(..., min_length=10)


class AnswerResponse(BaseModel):
    """Answer response schema"""
    id: int
    question_id: int
    user_answer: str
    score: Optional[float]
    ai_feedback: Optional[str]
    ideal_answer: Optional[str]
    technical_accuracy: Optional[float]
    completeness: Optional[float]
    clarity: Optional[float]
    communication_score: Optional[float]
    strengths: Optional[str]
    improvements: Optional[str]
    answered_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Interview Session Schemas ====================

class InterviewSessionStart(BaseModel):
    """Start interview session schema"""
    interview_type: str  # TECHNICAL, HR, MIXED
    category: Optional[str] = None  # Java, React, etc.
    difficulty: str = "MEDIUM"
    company: Optional[str] = None
    role: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[List[str]] = None
    session_metadata: Optional[Dict[str, Any]] = None


class InterviewSessionResponse(BaseModel):
    """Interview session response schema"""
    id: int
    user_id: int
    interview_type: str
    status: str
    overall_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    total_questions: int
    duration_minutes: Optional[int]
    session_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class InterviewSessionEnd(BaseModel):
    """End interview session schema"""
    session_id: int


# ==================== Analytics Schemas ====================

class AnalyticsResponse(BaseModel):
    """Analytics response schema"""
    id: int
    user_id: int
    total_interviews: int
    average_score: Optional[float]
    best_score: Optional[float]
    worst_score: Optional[float]
    technical_score: Optional[float]
    communication_score: Optional[float]
    hr_score: Optional[float]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    weak_areas: Optional[List[str]]
    
    class Config:
        from_attributes = True


class InterviewHistoryItem(BaseModel):
    """Interview history item"""
    id: int
    interview_type: str
    overall_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_minutes: Optional[int]
    status: str


class InterviewHistoryResponse(BaseModel):
    """Interview history response"""
    total_count: int
    interviews: List[InterviewHistoryItem]


# ==================== Report Schemas ====================

class InterviewReportResponse(BaseModel):
    """Interview report response"""
    id: int
    session_id: int
    overall_score: float
    technical_score: Optional[float]
    communication_score: Optional[float]
    summary: Optional[str]
    strengths_list: Optional[List[str]]
    improvements_list: Optional[List[str]]
    recommendations: Optional[List[str]]
    pdf_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== AI Service Schemas ====================

class AIQuestionGenerateRequest(BaseModel):
    """AI question generation request"""
    category: str
    difficulty: str = "MEDIUM"
    previous_answers: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None


class AIFollowUpRequest(BaseModel):
    """AI follow-up question request"""
    original_question: str
    user_answer: str
    category: str


class AIEvaluationRequest(BaseModel):
    """AI answer evaluation request"""
    question: str
    user_answer: str
    category: str
    difficulty: str


class AIEvaluationResponse(BaseModel):
    """AI evaluation response"""
    score: float
    feedback: str
    technical_accuracy: float
    completeness: float
    clarity: float
    communication_score: float
    strengths: str
    improvements: str
    ideal_answer: str


# ==================== Admin Schemas ====================

class UserListResponse(BaseModel):
    """User list response"""
    total_count: int
    users: List[UserResponse]


class SessionStatisticsResponse(BaseModel):
    """Session statistics response"""
    total_sessions: int
    completed_sessions: int
    average_score: float
    most_common_type: str
    most_common_category: str


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== Resume Schemas ====================

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    resume_text: Optional[str]
    skills: Optional[List[str]]
    projects: Optional[List[str]]
    experience: Optional[List[Dict[str, Any]]]
    education: Optional[List[Dict[str, Any]]]
    parsed_data: Optional[Dict[str, Any]]
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ResumeQuestionRequest(BaseModel):
    resume_id: int
    difficulty: str = "MEDIUM"


class ResumeQuestionSet(BaseModel):
    technical: List[str]
    project_based: List[str]
    behavioral: List[str]
