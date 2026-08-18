import os
import torch
import numpy as np
from typing import Any, Dict

from .base import BaseValuator

class TracInValuator(BaseValuator):
    """
    Computes TracIn scores, Embeddings, Rarity, AUM, and Forgetting Events 
    for PyTorch models using saved checkpoints.
    """
    def __init__(self, checkpoint_dir: str, configured_lr: float, trainer_results: Dict[str, Any]):
        self.checkpoint_dir = checkpoint_dir
        self.configured_lr = configured_lr
        self.trainer_results = trainer_results

    def calculate_influence(self, model_adapter: Any, train_data: Any, val_data: Any = None, **kwargs) -> Dict[str, Any]:
        from app.engine.tracin import compute_tracin_scores
        from app.engine.embeddings import extract_embeddings, compute_rarity_scores, compute_umap_projection
        from app.engine.valuator import compute_unified_scores
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model_adapter.model
        
        # In PyTorchAdapter, train_data is the DataLoader for images, 
        # but for tabular datasets, it's a tuple of (X, y) numpy arrays.
        if isinstance(train_data, tuple) and isinstance(train_data[0], np.ndarray):
            from app.engine.data_loader import create_pytorch_dataloaders
            X_train, y_train = train_data
            X_val, y_val = val_data if val_data else (None, None)
            # Use task_type from model_adapter if available
            task_type = getattr(model_adapter, 'task_type', kwargs.get('task_type', 'classification'))
            train_loader, val_loader = create_pytorch_dataloaders(X_train, y_train, X_val, y_val, task_type)
            num_samples = len(X_train)
        else:
            train_loader = train_data
            val_loader = val_data
            num_samples = len(train_loader.dataset)
            
        num_classes = 2 # Placeholder, factory will recreate with right size
        model_name = "tabular" # Need better logic for factory, but we can pass model_factory directly
        
        checkpoint_files = sorted([
            f for f in os.listdir(self.checkpoint_dir) if f.endswith(".pt") and f != "ckpt_final.pt"
        ])
        checkpoint_paths = [os.path.join(self.checkpoint_dir, f) for f in checkpoint_files]
        
        if len(checkpoint_paths) >= 2:
            lrs = []
            for path in checkpoint_paths:
                ckpt = torch.load(path, map_location="cpu", weights_only=True)
                lrs.append(ckpt.get("learning_rate", self.configured_lr))
                
            # Instead of passing model_factory by string name, we can just pass a lambda that clones the model
            import copy
            def model_factory():
                return copy.deepcopy(model)
                
            tracin_scores = compute_tracin_scores(
                model_factory=model_factory,
                checkpoint_paths=checkpoint_paths,
                learning_rates=lrs,
                train_loader=train_loader,
                val_loader=val_loader,
                device=device,
            )
        else:
            tracin_scores = np.zeros(num_samples, dtype=np.float32)
            
        model.eval()
        model.to(device)
        embeddings, indices = extract_embeddings(model, train_loader, device)
        rarity_scores = compute_rarity_scores(embeddings)
        embeddings_2d = compute_umap_projection(embeddings)
        
        forgetting_counts = self.trainer_results["forgetting_counts"]
        avg_loss = self.trainer_results["avg_loss"]
        aum_scores = self.trainer_results["aum_scores"]
        
        unified_scores, categories = compute_unified_scores(
            forgetting_counts, avg_loss, aum_scores, tracin_scores, rarity_scores
        )
        
        return {
            "forgetting_counts": forgetting_counts,
            "avg_loss": avg_loss,
            "aum_scores": aum_scores,
            "tracin_scores": tracin_scores,
            "rarity_scores": rarity_scores,
            "unified_scores": unified_scores,
            "categories": categories,
            "embeddings_2d": embeddings_2d,
        }
