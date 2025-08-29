import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/picker"
    
    # Image processing
    image_root: str = "/absolute/path/to/images"
    max_image_mb: int = 8
    supported_formats: tuple = ("jpg", "jpeg", "png", "webp")
    
    # API
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()