import os
from typing import List, Optional
from pydantic import BaseSettings, validator
import secrets

class Settings(BaseSettings):
    """Application settings configuration"""
    
    # Basic App Settings
    APP_NAME: str = "YUMZY Recipe Finder API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Security Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = False
    
    # Database Settings
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "yumzy_user"
    POSTGRES_PASSWORD: str = "yumzy_password"
    POSTGRES_DB: str = "yumzy_db"
    
    # Redis Settings (for caching and background tasks)
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 300  # 5 minutes default cache TTL
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "https://yumzy.app",
        "https://www.yumzy.app",
        "https://api.yumzy.app"
    ]
    
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "yumzy.app",
        "www.yumzy.app",
        "api.yumzy.app"
    ]
    
    # File Upload Settings
    UPLOAD_FOLDER: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".mp4", ".mov", ".avi", ".mkv"
    ]
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp"
    ]
    
    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Recipe Settings
    MAX_INGREDIENTS_PER_RECIPE: int = 50
    MAX_INSTRUCTIONS_LENGTH: int = 10000
    MAX_RECIPE_TITLE_LENGTH: int = 200
    MAX_RECIPE_DESCRIPTION_LENGTH: int = 1000
    
    # Search Settings
    SEARCH_RESULTS_LIMIT: int = 1000
    AUTOCOMPLETE_LIMIT: int = 10
    SIMILAR_RECIPES_LIMIT: int = 10
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    
    # Email Settings (for notifications)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@yumzy.app"
    
    # External API Settings
    SPOONACULAR_API_KEY: Optional[str] = None
    EDAMAM_APP_ID: Optional[str] = None
    EDAMAM_APP_KEY: Optional[str] = None
    NUTRITIONIX_APP_ID: Optional[str] = None
    NUTRITIONIX_API_KEY: Optional[str] = None
    
    # Social Media API Keys
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    
    # AWS Settings (for file storage)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    
    # CDN Settings
    CDN_BASE_URL: Optional[str] = None
    
    # Analytics and Monitoring
    SENTRY_DSN: Optional[str] = None
    GOOGLE_ANALYTICS_ID: Optional[str] = None
    MIXPANEL_TOKEN: Optional[str] = None
    
    # Feature Flags
    ENABLE_SOCIAL_SHARING: bool = True
    ENABLE_RECOMMENDATIONS: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_CACHING: bool = True
    ENABLE_EXTERNAL_RECIPES: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    
    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Testing Settings
    TESTING: bool = False
    TEST_DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("ALLOWED_ORIGINS must be a list or comma-separated string")
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Database configuration for different environments
class DatabaseConfig:
    """Database configuration helper"""
    
    @staticmethod
    def get_database_url(environment: str = "development") -> str:
        """Get database URL for specific environment"""
        if environment == "test":
            return settings.TEST_DATABASE_URL or "sqlite:///./test.db"
        elif environment == "production":
            return settings.DATABASE_URL
        else:  # development
            return settings.DATABASE_URL
    
    @staticmethod
    def get_engine_kwargs(environment: str = "development") -> dict:
        """Get SQLAlchemy engine kwargs for specific environment"""
        if "sqlite" in DatabaseConfig.get_database_url(environment):
            return {"connect_args": {"check_same_thread": False}}
        else:
            return {
                "pool_pre_ping": True,
                "pool_recycle": 300,
                "pool_size": 10,
                "max_overflow": 20
            }

# Feature flags helper
class FeatureFlags:
    """Feature flags management"""
    
    @staticmethod
    def is_enabled(feature: str) -> bool:
        """Check if a feature is enabled"""
        feature_map = {
            "social_sharing": settings.ENABLE_SOCIAL_SHARING,
            "recommendations": settings.ENABLE_RECOMMENDATIONS,
            "analytics": settings.ENABLE_ANALYTICS,
            "rate_limiting": settings.ENABLE_RATE_LIMITING,
            "caching": settings.ENABLE_CACHING,
            "external_recipes": settings.ENABLE_EXTERNAL_RECIPES,
            "email_notifications": settings.ENABLE_EMAIL_NOTIFICATIONS,
        }
        return feature_map.get(feature, False)

# Environment helper
def get_environment() -> str:
    """Get current environment"""
    return os.getenv("ENVIRONMENT", "development")

def is_development() -> bool:
    """Check if running in development environment"""
    return get_environment() == "development"

def is_production() -> bool:
    """Check if running in production environment"""
    return get_environment() == "production"

def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_environment() == "test" or settings.TESTING

# Configuration validation
def validate_configuration():
    """Validate configuration settings"""
    errors = []
    
    # Check required settings
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY is required")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if is_production():
        # Production-specific validations
        if settings.DEBUG:
            errors.append("DEBUG should be False in production")
        
        if "localhost" in settings.ALLOWED_ORIGINS:
            errors.append("Remove localhost from ALLOWED_ORIGINS in production")
        
        if not settings.SENTRY_DSN:
            errors.append("SENTRY_DSN recommended for production monitoring")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True

# Initialize configuration validation
if not is_testing():
    validate_configuration()