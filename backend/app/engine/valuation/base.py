from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseValuator(ABC):
    """Abstract base class for data valuation methods."""
    
    @abstractmethod
    def calculate_influence(self, model: Any, train_data: Any, val_data: Any = None, **kwargs) -> Dict[str, Any]:
        """
        Calculate influence scores for the training data.
        
        Returns:
            Dict containing:
                - forgetting_counts (1D array)
                - avg_loss (1D array) 
                - aum_scores (1D array)
                - tracin_scores (1D array, or loo_scores)
                - rarity_scores (1D array)
                - unified_scores (1D array)
                - categories (List of strings)
                - embeddings_2d (2D array, optional)
        """
        pass
