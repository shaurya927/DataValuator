from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TrainingConfig(BaseModel):
    dataset_id: str
    model_name: str
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    template: Optional[str] = None
    epochs: int
    learning_rate: float

class TrainingStatus(BaseModel):
    run_id: str
    status: str
    current_epoch: int
    train_loss: float
    val_accuracy: float
    progress_pct: float

class TrainingRunInfo(BaseModel):
    id: str
    dataset_id: str
    model_name: str
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    template: Optional[str] = None
    epochs: int
    learning_rate: float
    status: str
    current_epoch: int
    train_loss: Optional[float] = None
    val_accuracy: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    checkpoint_dir: Optional[str] = None
    metrics_path: Optional[str] = None
