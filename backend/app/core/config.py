import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with algo-update.yaml parameters."""
    
    # Database
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/picker"
    
    # Image processing
    max_image_mb: int = 250  # Increased as per spec
    supported_formats: tuple = (".jpg", ".jpeg", ".png", ".webp", ".gif")  # Updated extensions from spec
    
    # API
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Directory Service (algo-update.yaml spec)
    max_total_files: int = 200_000
    max_file_size_mb: int = 250
    hash_chunk_size_bytes: int = 1048576  # 1 MB
    parallel_workers: int = 4
    
    # Pairing Engine (algo-update.yaml spec)
    epsilon_greedy: float = 0.10
    skip_inject_probability: float = 0.30
    skip_resurface_min_rounds: int = 11
    skip_resurface_max_rounds: int = 49
    recent_image_window: int = 64
    recent_pair_window: int = 128
    shortlist_k: int = 64
    avoid_recent_rounds: int = 12
    
    # Elo+σ Rating Model (algo-update.yaml spec)
    initial_mu: float = 1500.0
    initial_sigma: float = 350.0
    sigma_min: float = 60.0
    k_base: float = 24.0
    k_min: float = 8.0
    k_max: float = 48.0
    sigma_decay: float = 0.97
    
    # Stop/Exit Criteria (algo-update.yaml spec)
    target_top_k: int = 40
    natural_cutoff_delta: float = 0.0
    min_exposures_per_image: int = 5
    confidence_z: float = 1.0
    sigma_confident_max: float = 90.0
    min_boundary_gap: float = 25.0
    stability_window_rounds: int = 120
    max_rank_swaps_in_window: int = 1
    coverage_required: bool = True
    allow_manual_finish: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()