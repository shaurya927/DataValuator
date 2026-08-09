from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DatasetInfo(BaseModel):
    id: str
    name: str
    type: str
    task_type: Optional[str] = None
    target_column: Optional[str] = None
    default_template: Optional[str] = None
    num_samples: int
    num_classes: int
    created_at: datetime
    path: str

class DatasetUploadResponse(BaseModel):
    id: str
    message: str

class DatasetPreview(BaseModel):
    info: DatasetInfo
    preview_data: List[dict]  # contains 'image' (base64) or 'row' data
