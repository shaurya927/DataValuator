from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import numpy as np

class BaseModel(ABC):
    """Abstract base class for all ML models in DataValuator."""
    
    @abstractmethod
    def train(self, train_data: Any, val_data: Optional[Any] = None, config: Optional[Dict] = None, progress_callback=None, cancel_event=None) -> Dict[str, Any]:
        """
        Train the model.
        Returns a dictionary containing training metrics and results.
        """
        pass
        
    @abstractmethod
    def predict(self, X: Any) -> Any:
        """Make predictions on data."""
        pass
        
    @abstractmethod
    def evaluate(self, X: Any, y: Any) -> float:
        """Evaluate the model and return the primary metric (accuracy/mse)."""
        pass
        
    @property
    @abstractmethod
    def supported_valuation_method(self) -> str:
        """Return the valuation method to use (e.g., 'tracin', 'leave_one_out')."""
        pass
        
    def get_embeddings(self, X: Any) -> Optional[np.ndarray]:
        """Extract embeddings if supported by the architecture."""
        return None
        
    def save_checkpoint(self, path: str):
        """Save model checkpoint if supported."""
        pass
