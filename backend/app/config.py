import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "DataValuator"
    DATA_DIR: Path = Path("data")
    UPLOAD_DIR: Path = Path("data/uploads")
    CHECKPOINT_DIR: Path = Path("data/checkpoints")
    METRICS_DIR: Path = Path("data/metrics")
    DB_PATH: Path = Path("data/db/dataValuator.db")
    DEFAULT_EPOCHS: int = 20
    DEFAULT_LR: float = 0.01
    CHECKPOINT_INTERVAL: int = 5
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        self.METRICS_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_settings() -> Settings:
    return Settings()
