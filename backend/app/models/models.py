"""Database models for InterviAI"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)  # Nullable for OAuth users
    role = Column(String(50), default="USER")  # USER, ADMIN
    google_id = Column(String(255), unique=True, nullable=True)
    profile_picture = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interview_sessions = relationship("InterviewSession", back_populates="user")
    analytics = relationship("Analytics", back_populates="user")


class InterviewSession(Base):
    """Interview session model"""
    __tablename__ = "interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interview_type = Column(String(50), nullable=False)  # TECHNICAL, HR, MIXED
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    overall_score = Column(Float, nullable=True)
    status = Column(String(50), default="IN_PROGRESS")  # IN_PROGRESS, COMPLETED, ABANDONED
    total_questions = Column(Integer, default=0)
    duration_minutes = Column(Integer, nullable=True)
    session_metadata = Column(JSON, nullable=True)
    # prompt_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("Question", back_populates="session")


class Question(Base):
    """Interview question model"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # Java, React, SQL, HR, etc.
    difficulty = Column(String(50), default="MEDIUM")  # EASY, MEDIUM, HARD
    question_type = Column(String(50), default="TECHNICAL")  # TECHNICAL, HR, FOLLOW_UP
    parent_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("InterviewSession", back_populates="questions")
    answers = relationship("Answer", back_populates="question")


class Answer(Base):
    """User answer model"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    ai_feedback = Column(Text, nullable=True)
    ideal_answer = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    
    # Evaluation metrics
    technical_accuracy = Column(Float, nullable=True)
    completeness = Column(Float, nullable=True)
    clarity = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    
    # Detailed feedback
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    evaluation_metadata = Column(JSON, nullable=True)
    
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question", back_populates="answers")


class Analytics(Base):
    """User analytics and performance tracking"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Overall statistics
    total_interviews = Column(Integer, default=0)
    average_score = Column(Float, nullable=True)
    best_score = Column(Float, nullable=True)
    worst_score = Column(Float, nullable=True)
    
    # Category scores
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    hr_score = Column(Float, nullable=True)
    
    # Skill analysis
    strengths = Column(JSON, nullable=True)  # List of strengths
    weaknesses = Column(JSON, nullable=True)  # List of weaknesses
    category_performance = Column(JSON, nullable=True)  # Dict of category: score
    
    # Topic expertise
    topics_covered = Column(JSON, nullable=True)  # List of topics
    weak_areas = Column(JSON, nullable=True)  # List of weak areas
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analytics")


class InterviewReport(Base):
    """Interview session report"""
    __tablename__ = "interview_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report data
    overall_score = Column(Float, nullable=False)
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    
    # Summary
    summary = Column(Text, nullable=True)
    strengths_list = Column(JSON, nullable=True)
    improvements_list = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Detailed metrics
    performance_metrics = Column(JSON, nullable=True)
    time_analysis = Column(JSON, nullable=True)
    
    # Report file
    pdf_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIPrompt(Base):
    """Store AI prompts and templates"""
    __tablename__ = "ai_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # QUESTION_GEN, EVAL, FOLLOWUP, etc.
    prompt_template = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    prompt_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit log for system activities"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Resume(Base):
    """User resume uploads"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    resume_text = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)        # ["Java", "React", ...]
    projects = Column(JSON, nullable=True)      # ["Doctor App", ...]
    experience = Column(JSON, nullable=True)    # [{"company": ..., "role": ...}]
    education = Column(JSON, nullable=True)     # [{"degree": ..., "college": ...}]
    parsed_data = Column(JSON, nullable=True)   # full AI extraction
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="resumes")

    @property
    def extraction_status(self):
        return "completed" if self.resume_text and self.resume_text.strip() else "unavailable"


# ==================== Webcam / Behavior Models ====================

class InterviewBehavior(Base):
    """Stores webcam behavior analysis results per session"""
    __tablename__ = "interview_behaviors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(64), nullable=False, index=True)  # frontend-generated UUID
    confidence_score = Column(Float, nullable=True)
    eye_contact_score = Column(Float, nullable=True)
    posture_score = Column(Float, nullable=True)
    expression_score = Column(Float, nullable=True)
    ai_feedback = Column(JSON, nullable=True)   # {strengths, improvements}
    raw_metrics = Column(JSON, nullable=True)   # full frame-by-frame data
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="behaviors")


# ==================== Coding Interview Models ====================

class CodingSession(Base):
    __tablename__ = "coding_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    difficulty = Column(String(20), default="MEDIUM")  # EASY, MEDIUM, HARD
    language = Column(String(30), nullable=False)       # python, javascript, java, cpp
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="coding_sessions")
    submissions = relationship("CodingSubmission", back_populates="session")


class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), default="MEDIUM")
    topic = Column(String(100), nullable=False)
    constraints = Column(Text, nullable=True)
    sample_input = Column(Text, nullable=True)
    sample_output = Column(Text, nullable=True)
    test_cases = Column(JSON, nullable=True)         # [{input, expected_output}]
    expected_complexity = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("coding_sessions.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("coding_problems.id"), nullable=True)
    code = Column(Text, nullable=False)
    language = Column(String(30), nullable=False)
    score = Column(Float, nullable=True)
    passed_tests = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    time_complexity = Column(String(50), nullable=True)
    space_complexity = Column(String(50), nullable=True)
    ai_feedback = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("CodingSession", back_populates="submissions")


# ==================== Proctoring Model ====================

class ProctoringSession(Base):
    """Stores all proctoring events and final scores for any interview session"""
    __tablename__ = "proctoring_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_key = Column(String(128), nullable=False, index=True)
    session_type = Column(String(50), nullable=False)

    tab_switches = Column(Integer, default=0)
    copy_paste_count = Column(Integer, default=0)
    face_not_detected = Column(Integer, default=0)
    multiple_faces = Column(Integer, default=0)
    fullscreen_exits = Column(Integer, default=0)
    looking_away = Column(Integer, default=0)

    eye_contact_score = Column(Float, nullable=True)
    posture_score = Column(Float, nullable=True)
    expression_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    proctoring_score = Column(Float, nullable=True)

    events = Column(JSON, nullable=True)
    ai_feedback = Column(JSON, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="proctoring_sessions")


# ==================== RAG / GenAI Models ====================

class JobDescription(Base):
    """Uploaded job descriptions for RAG pipeline"""
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)
    experience_required = Column(String(100), nullable=True)
    chroma_doc_id = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="job_descriptions")


class InterviewMemory(Base):
    """Long-term memory: tracks topics, mistakes, progress per user"""
    __tablename__ = "interview_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    asked_questions = Column(JSON, default=list)       # list of question texts
    weak_topics = Column(JSON, default=list)
    strong_topics = Column(JSON, default=list)
    topic_scores = Column(JSON, default=dict)          # {topic: avg_score}
    total_sessions = Column(Integer, default=0)
    last_difficulty = Column(String(20), default="MEDIUM")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="interview_memory")


class CareerProfile(Base):
    """Career coach analysis results"""
    __tablename__ = "career_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)

    resume_match_score = Column(Float, nullable=True)
    job_match_score = Column(Float, nullable=True)
    hiring_probability = Column(Float, nullable=True)
    interview_readiness = Column(Float, nullable=True)

    current_skills = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    skill_gap_analysis = Column(JSON, nullable=True)

    recommended_courses = Column(JSON, nullable=True)
    recommended_certifications = Column(JSON, nullable=True)
    recommended_projects = Column(JSON, nullable=True)

    learning_plan_30 = Column(JSON, nullable=True)
    learning_plan_60 = Column(JSON, nullable=True)
    learning_plan_90 = Column(JSON, nullable=True)

    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="career_profiles")


class EnhancedInterviewReport(Base):
    """Full AI-generated report with radar chart data and hiring recommendation"""
    __tablename__ = "enhanced_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    coding_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    resume_match_score = Column(Float, nullable=True)
    job_match_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    hiring_probability = Column(Float, nullable=True)

    skill_matrix = Column(JSON, nullable=True)         # {skill: score}
    radar_chart_data = Column(JSON, nullable=True)     # [{subject, score}]
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    topics_to_improve = Column(JSON, nullable=True)
    learning_recommendations = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    hiring_recommendation = Column(String(50), nullable=True)  # STRONG_YES, YES, MAYBE, NO

    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="enhanced_reports")


# ==================== ATS / Resume Match ====================

class ATSReport(Base):
    __tablename__ = "ats_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    jd_text = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    keyword_match_pct = Column(Float, nullable=True)
    matching_skills = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    missing_technologies = Column(JSON, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    improvements = Column(JSON, nullable=True)
    formatting_suggestions = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", backref="ats_reports")


# ==================== GitHub Analysis ====================

class GitHubAnalysis(Base):
    __tablename__ = "github_analyses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    github_url = Column(String(500), nullable=False)
    username = Column(String(255), nullable=True)
    github_score = Column(Float, nullable=True)
    project_quality_score = Column(Float, nullable=True)
    coding_activity_score = Column(Float, nullable=True)
    open_source_score = Column(Float, nullable=True)
    languages = Column(JSON, nullable=True)
    frameworks = Column(JSON, nullable=True)
    top_repos = Column(JSON, nullable=True)
    total_stars = Column(Integer, default=0)
    total_forks = Column(Integer, default=0)
    commit_frequency = Column(String(50), nullable=True)
    recommendations = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", backref="github_analyses")


# ==================== System Design ====================

class SystemDesignSession(Base):
    __tablename__ = "system_design_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String(255), nullable=False)
    difficulty = Column(String(20), default="MEDIUM")
    questions = Column(JSON, nullable=True)
    answers = Column(JSON, nullable=True)
    architecture_score = Column(Float, nullable=True)
    scalability_score = Column(Float, nullable=True)
    tradeoffs_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    ai_feedback = Column(JSON, nullable=True)
    status = Column(String(30), default="IN_PROGRESS")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User", backref="system_design_sessions")


# ==================== Voice Interview ====================

class VoiceInterviewSession(Base):
    __tablename__ = "voice_interview_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interview_type = Column(String(50), default="TECHNICAL")
    transcript = Column(JSON, nullable=True)   # [{role, text, timestamp}]
    overall_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    speaking_speed = Column(String(30), nullable=True)
    filler_word_count = Column(Integer, default=0)
    filler_words = Column(JSON, nullable=True)
    ai_feedback = Column(JSON, nullable=True)
    status = Column(String(30), default="IN_PROGRESS")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User", backref="voice_sessions")


# ==================== Recruiter ====================

class RecruiterNote(Base):
    __tablename__ = "recruiter_notes"
    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)   # 1-5
    decision = Column(String(30), nullable=True)  # SHORTLIST, REJECT, HOLD
    created_at = Column(DateTime, default=datetime.utcnow)


