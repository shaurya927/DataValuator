"""TracIn (Tracing with Individual Checkpoints) computation.

Estimates the influence of each training sample by computing gradient
dot products across saved model checkpoints. Uses last-layer gradients
for efficiency.

Reference: Pruthi et al., "Estimating Training Data Influence by
Tracing Gradient Descent" (NeurIPS 2020).
"""
import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Any, Callable, Type
import torch.nn.functional as F


def compute_tracin_scores(
    model_factory: Callable[[], nn.Module],
    checkpoint_paths: List[str],
    learning_rates: List[float],
    train_loader: Any,
    val_loader: Any,
    task_type: str = "classification",
    device: str = "cpu",
) -> np.ndarray:
    """Computes TracIn self-influence scores for all training samples.

    For each checkpoint, loads the model weights and computes the squared
    gradient norm of the last linear layer for each training sample.
    Self-influence = sum_k lr_k * ||grad_last_layer(z_i, theta_k)||^2

    Positive scores indicate the sample helped its own prediction;
    negative or near-zero scores may indicate harmful/redundant samples.

    Args:
        model_factory: A callable that returns a new instance of the model.
        checkpoint_paths: List of checkpoint file paths.
        learning_rates: Learning rate at each checkpoint (same length).
        train_loader: DataLoader yielding (index, data, target).
        val_loader: Validation DataLoader (used for cross-influence if needed).
        device: Torch device string ("cpu" or "cuda").

    Returns:
        np.ndarray of shape (num_train_samples,) with TracIn self-influence.
    """
    num_train_samples = len(train_loader.dataset)
    tracin_scores = np.zeros(num_train_samples, dtype=np.float32)
    device_t = torch.device(device)

    for ckpt_idx, (ckpt_path, lr) in enumerate(zip(checkpoint_paths, learning_rates)):
        model = model_factory()

        # Handle both raw state_dict and wrapped checkpoint formats
        checkpoint = torch.load(ckpt_path, map_location=device_t, weights_only=True)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        model.to(device_t)
        model.eval()

        # Find the last Linear layer for efficient gradient computation
        final_layer = _find_last_linear(model)
        if final_layer is None:
            raise ValueError("No nn.Linear layer found in model")

        # Batch-level gradient computation (much faster than per-sample)
        for indices, data, targets in train_loader:
            data, targets = data.to(device_t), targets.to(device_t)
            batch_size = len(targets)

            # Forward pass
            logits = model(data)

            # Compute per-sample gradient norms using the diagonal trick:
            # For the last layer: grad_W = (dL/dz) outer (h)
            # ||grad||^2 = ||dL/dz||^2 * ||h||^2  for self-influence
            # This avoids per-sample backward passes

            # Get input to final layer via hook
            activations = []

            def hook_fn(module, inp, out):
                activations.append(inp[0].detach())

            handle = final_layer.register_forward_hook(hook_fn)

            # Re-forward to capture activations
            with torch.no_grad():
                model(data)
            handle.remove()

            h = activations[0]  # (batch, hidden_dim)

            # Compute per-sample loss gradients w.r.t. logits
            if task_type == "classification":
                # For cross-entropy: dL/dz = softmax(z) - one_hot(y)
                probs = F.softmax(logits.detach(), dim=1)
                one_hot = torch.zeros_like(probs)
                one_hot.scatter_(1, targets.unsqueeze(1), 1.0)
                dl_dz = probs - one_hot  # (batch, num_classes)
            else:
                # For MSE: dL/dz = 2 * (z - y) / (num_classes|1) but we can ignore constants for relative score
                # Let's just use (logits - targets)
                targets_resized = targets.view_as(logits)
                dl_dz = logits.detach() - targets_resized # (batch, output_dim)

            # Per-sample gradient norm squared for weight matrix
            # grad_W_i = dl_dz_i (outer) h_i
            # ||grad_W_i||^2 = ||dl_dz_i||^2 * ||h_i||^2
            grad_norm_sq = (dl_dz.pow(2).sum(dim=1) * h.pow(2).sum(dim=1)).cpu().numpy()

            # Add bias gradient norm if present
            if final_layer.bias is not None:
                grad_norm_sq += dl_dz.pow(2).sum(dim=1).cpu().numpy()

            indices_np = indices.cpu().numpy()
            tracin_scores[indices_np] += lr * grad_norm_sq

    return tracin_scores


def _find_last_linear(model: nn.Module) -> nn.Linear:
    """Finds the last nn.Linear layer in the model."""
    last_linear = None
    for module in model.modules():
        if isinstance(module, nn.Linear):
            last_linear = module
    return last_linear
