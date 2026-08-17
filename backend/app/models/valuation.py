from pydantic import BaseModel
from typing import List, Dict, Optional

class ValuationSummary(BaseModel):
    category_counts: Dict[str, int]
    health_score: float
    recommended_removal_pct: float

class SampleValuation(BaseModel):
    id: int
    run_id: str
    sample_index: int
    forgetting_count: int
    avg_loss: float
    aum_score: float
    tracin_score: float
    rarity_score: float
    unified_score: float
    category: str
    embedding_x: float
    embedding_y: float
    image_base64: Optional[str] = None

class SampleListResponse(BaseModel):
    total: int
    samples: List[SampleValuation]

class DistributionData(BaseModel):
    metric: str
    bins: List[float]
    counts: List[int]

class EmbeddingPoint(BaseModel):
    x: float
    y: float
    category: str
    sample_index: int

class ExperimentConfig(BaseModel):
    run_id: str
    prune_pct: Optional[float] = None
    corruption_pct: Optional[float] = None

class ExperimentResult(BaseModel):
    id: str
    run_id: str
    type: str
    config: str
    status: str
    original_accuracy: Optional[float] = None
    result_accuracy: Optional[float] = None
    samples_removed: Optional[int] = None
    precision: Optional[float] = None
    recall: Optional[float] = None

class WeightConfig(BaseModel):
    forgetting: float = 0.20
    loss: float = 0.15
    aum: float = 0.25
    tracin: float = 0.20
    rarity: float = 0.20

class BatchUpdateRequest(BaseModel):
    sample_indices: List[int]
    category: str

class ComparisonResult(BaseModel):
    run_a_summary: dict
    run_b_summary: dict
    category_changes: List[dict]
    overlap_count: int
    total_samples: int

class RunSummaryItem(BaseModel):
    run_id: str
    model_name: str
    val_accuracy: Optional[float] = None
    epochs: int = 0
    learning_rate: float = 0.01
    category_counts: Dict[str, int] = {}
    total_samples: int = 0
    started_at: Optional[str] = None
