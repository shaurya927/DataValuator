import numpy as np
from typing import Any, Dict
from sklearn.metrics import accuracy_score, r2_score
import copy

from .base import BaseValuator

class FastLOOValuator(BaseValuator):
    """
    Fast approximation of Leave-One-Out influence using Monte Carlo subset training.
    Instead of retraining N times, we train K times (e.g., K=10) on random 80% subsets.
    Influence of sample i = Avg Val Metric (when i in train) - Avg Val Metric (when i not in train).
    """
    def __init__(self, n_iterations: int = 10):
        self.n_iterations = n_iterations

    def calculate_influence(self, model_adapter: Any, train_data: Any, val_data: Any = None, **kwargs) -> Dict[str, Any]:
        X_train, y_train = train_data
        n_samples = len(X_train)
        
        # We need validation data to compute influence. If none, we evaluate influence on the training set itself.
        if val_data is None:
            X_val, y_val = X_train, y_train
        else:
            X_val, y_val = val_data
            
        task_type = model_adapter.task_type
        
        # 1. Compute individual sample losses on the full trained model to populate avg_loss & aum
        preds = model_adapter.predict(X_train)
        avg_loss = np.zeros(n_samples, dtype=np.float32)
        aum_scores = np.zeros(n_samples, dtype=np.float32)
        
        if task_type == "classification":
            # For classification, loss is 0 if correct, 1 if wrong
            avg_loss = (preds != y_train).astype(np.float32)
            # AUM (Margin): For hard labels, margin is 1 if correct, -1 if wrong
            aum_scores = np.where(preds == y_train, 1.0, -1.0)
            
            # If the model supports predict_proba, we can get better margins
            if hasattr(model_adapter.model, "predict_proba"):
                probs = model_adapter.model.predict_proba(X_train)
                # Loss = 1 - prob(true_class)
                true_probs = probs[np.arange(n_samples), y_train]
                avg_loss = 1.0 - true_probs
                
                # Margin = prob(true_class) - max(prob(other_classes))
                mask = np.ones(probs.shape, dtype=bool)
                mask[np.arange(n_samples), y_train] = False
                # Handle binary classification gracefully
                if probs.shape[1] > 1:
                    max_other_probs = probs[mask].reshape(n_samples, probs.shape[1] - 1).max(axis=1)
                    aum_scores = true_probs - max_other_probs
        else:
            # Regression
            avg_loss = (preds - y_train) ** 2
            aum_scores = -avg_loss # Lower loss means better "margin"
            
        # 2. Monte Carlo Approximation for Influence (TracIn proxy)
        # We track the sum of validation metrics when sample i is included vs excluded
        incl_sum = np.zeros(n_samples, dtype=np.float32)
        incl_count = np.zeros(n_samples, dtype=np.float32)
        excl_sum = np.zeros(n_samples, dtype=np.float32)
        excl_count = np.zeros(n_samples, dtype=np.float32)
        
        for _ in range(self.n_iterations):
            # Random 80% subset
            subset_indices = np.random.choice(n_samples, int(0.8 * n_samples), replace=False)
            subset_mask = np.zeros(n_samples, dtype=bool)
            subset_mask[subset_indices] = True
            
            # Train a clone of the model
            import sklearn
            cloned_estimator = sklearn.base.clone(model_adapter.model)
            cloned_estimator.fit(X_train[subset_mask], y_train[subset_mask])
            
            # Evaluate on validation
            val_preds = cloned_estimator.predict(X_val)
            if task_type == "classification":
                val_metric = accuracy_score(y_val, val_preds)
            else:
                val_metric = max(0.0, r2_score(y_val, val_preds))
                
            # Update running sums
            incl_sum[subset_mask] += val_metric
            incl_count[subset_mask] += 1
            excl_sum[~subset_mask] += val_metric
            excl_count[~subset_mask] += 1
            
        # Avoid division by zero
        safe_incl_count = np.where(incl_count > 0, incl_count, 1)
        safe_excl_count = np.where(excl_count > 0, excl_count, 1)
        
        # Influence = E[val_metric | included] - E[val_metric | excluded]
        # Positive influence means including the sample increases validation metric (Good)
        influence_scores = (incl_sum / safe_incl_count) - (excl_sum / safe_excl_count)
        
        # For samples that were NEVER included or NEVER excluded, influence is 0
        influence_scores[incl_count == 0] = 0
        influence_scores[excl_count == 0] = 0
        
        # We use influence_scores in place of tracin_scores
        # 3. Compute Rarity (Optional, we'll set to 0 for non-PyTorch to keep it fast)
        rarity_scores = np.zeros(n_samples, dtype=np.float32)
        
        # 4. Generate Unified Categories
        from app.engine.valuator import compute_unified_scores
        forgetting_counts = np.zeros(n_samples, dtype=np.float32)
        
        unified_scores, categories = compute_unified_scores(
            forgetting_counts, avg_loss, aum_scores, influence_scores, rarity_scores
        )
        
        return {
            "forgetting_counts": forgetting_counts,
            "avg_loss": avg_loss,
            "aum_scores": aum_scores,
            "tracin_scores": influence_scores, # Aliased for DB compatibility
            "rarity_scores": rarity_scores,
            "unified_scores": unified_scores,
            "categories": categories,
            "embeddings_2d": np.zeros((n_samples, 2), dtype=np.float32) # No embeddings for sklearn
        }
