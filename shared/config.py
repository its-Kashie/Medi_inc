"""
Configuration Management for HealthLink360
Centralized configuration loading from environment variables
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application Settings"""
    
    # Application
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    app_name: str = "HealthLink360"
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    pii_encryption_key: str = Field(..., env="PII_ENCRYPTION_KEY")
    
    # Backend Core
    backend_core_host: str = Field(default="0.0.0.0", env="BACKEND_CORE_HOST")
    backend_core_port: int = Field(default=8000, env="BACKEND_CORE_PORT")
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Backend Reporting
    backend_reporting_host: str = Field(default="0.0.0.0", env="BACKEND_REPORTING_HOST")
    backend_reporting_port: int = Field(default=8001, env="BACKEND_REPORTING_PORT")
    mongodb_url: str = Field(..., env="MONGODB_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_db: int = Field(default=1, env="REDIS_CACHE_DB")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000,http://localhost:8001",
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # File Storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    report_dir: str = Field(default="./generated_reports", env="REPORT_DIR")
    filled_report_dir: str = Field(default="./filled_reports", env="FILLED_REPORT_DIR")
    log_dir: str = Field(default="./logs", env="LOG_DIR")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Email
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    email_from: str = Field(default="noreply@healthlink360.com", env="EMAIL_FROM")
    
    # MCP Servers
    mcp_core_agents_port: int = Field(default=9000, env="MCP_CORE_AGENTS_PORT")
    mcp_nih_port: int = Field(default=9001, env="MCP_NIH_PORT")
    mcp_orchestrator_port: int = Field(default=9002, env="MCP_ORCHESTRATOR_PORT")
    mcp_report_gen_port: int = Field(default=9003, env="MCP_REPORT_GEN_PORT")
    mcp_rnd_port: int = Field(default=9004, env="MCP_RND_PORT")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/2", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/3", env="CELERY_RESULT_BACKEND")
    
    # Security & Compliance
    enable_audit_logging: bool = Field(default=True, env="ENABLE_AUDIT_LOGGING")
    audit_log_retention_days: int = Field(default=2555, env="AUDIT_LOG_RETENTION_DAYS")  # 7 years
    
    # WHO & NIH
    who_api_endpoint: str = Field(default="https://api.who.int/v1", env="WHO_API_ENDPOINT")
    nih_api_endpoint: str = Field(default="https://api.nih.gov/v1", env="NIH_API_ENDPOINT")
    enable_who_reporting: bool = Field(default=True, env="ENABLE_WHO_REPORTING")
    enable_nih_reporting: bool = Field(default=True, env="ENABLE_NIH_REPORTING")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Session
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    max_concurrent_sessions: int = Field(default=3, env="MAX_CONCURRENT_SESSIONS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields like REACT_APP_*
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.upload_dir,
            self.report_dir,
            self.filled_report_dir,
            self.log_dir,
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
