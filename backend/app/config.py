"""Configuration settings for InterviAI backend"""
import os
from datetime import timedelta
from pydantic_settings import BaseSettings


def _load_list(value: str | list | None, fallback: list) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return fallback
    return [item.strip() for item in str(value).split(",") if item.strip()]


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "InterviAI API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered Interview Preparation Platform"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/interviai"
    )
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-in-production-minimum-32-characters"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Judge0 API Configuration (get free key at rapidapi.com/judge0-official)
    JUDGE0_API_KEY: str = os.getenv("JUDGE0_API_KEY", "your-judge0-key")

    # GitHub API (optional — increases rate limit from 60 to 5000 req/hr)
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URL: str = os.getenv(
        "GOOGLE_REDIRECT_URL",
        "http://localhost:3000/auth/google/callback"
    )
    
    # CORS Configuration
    CORS_ORIGINS: list = _load_list(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,https://your-frontend-domain.com",
        ),
        [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://your-frontend-domain.com",
        ],
    )
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
