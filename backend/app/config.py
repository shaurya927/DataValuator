import os
import functools
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DataValuator"
    ENVIRONMENT: str = "production"

    # Paths — anchored to project root
    DATA_DIR: Path = Path("data")
    UPLOAD_DIR: Path = Path("data/uploads")
    CHECKPOINT_DIR: Path = Path("data/checkpoints")
    METRICS_DIR: Path = Path("data/metrics")
    DB_PATH: Path = Path("data/db/dataValuator.db")

    # Training defaults
    DEFAULT_EPOCHS: int = 20
    DEFAULT_LR: float = 0.01
    CHECKPOINT_INTERVAL: int = 5
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    # Security
    API_KEY: Optional[str] = None  # Set to enable API key authentication
    CORS_ORIGINS: str = "http://localhost:5173"  # Comma-separated allowed origins

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        self.METRICS_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    def get_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@functools.lru_cache()
def get_settings() -> Settings:
    return Settings()
