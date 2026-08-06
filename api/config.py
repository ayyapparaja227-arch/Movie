from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application configuration and credentials loaded from environment variables
    with safe default fallbacks.
    """
    # API authentication
    admin_api_key: str = "hackathon-secret-key-123"
    
    # Model configuration
    model_version: Optional[str] = None
    
    # Infrastructure defaults (caching and logs)
    redis_url: str = "redis://localhost:6379"
    postgres_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
