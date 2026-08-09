import numpy as np
import torch
import torch.nn.functional as F

class ForgettingTracker:
    def __init__(self, num_samples: int):
        self.num_samples = num_samples
        self.forgetting_counts = np.zeros(num_samples, dtype=np.int32)
        self.last_correct = np.zeros(num_samples, dtype=bool)
        self.ever_correct = np.zeros(num_samples, dtype=bool)
        self.is_first_epoch = True

    def update(self, sample_indices: torch.Tensor, logits: torch.Tensor, targets: torch.Tensor):
        preds = logits.argmax(dim=1).detach().cpu().numpy()
        targets_np = targets.detach().cpu().numpy()
        indices_np = sample_indices.detach().cpu().numpy()
        
        correct_now = (preds == targets_np)
        
        if not self.is_first_epoch:
            forgotten = self.last_correct[indices_np] & (~correct_now)
            self.forgetting_counts[indices_np[forgotten]] += 1
            
        self.last_correct[indices_np] = correct_now
        self.ever_correct[indices_np] |= correct_now

    def finalize_epoch(self):
        self.is_first_epoch = False

    def get_forgetting_counts(self) -> np.ndarray:
        return self.forgetting_counts.copy()

    def get_never_learned_mask(self) -> np.ndarray:
        return ~self.ever_correct

class LossAUMTracker:
    def __init__(self, num_samples: int):
        self.num_samples = num_samples
        self.sum_loss = np.zeros(num_samples, dtype=np.float32)
        self.sum_aum = np.zeros(num_samples, dtype=np.float32)
        self.epoch_counts = np.zeros(num_samples, dtype=np.int32)
        self.current_epoch_losses = np.zeros(num_samples, dtype=np.float32)
        
    def record_batch(self, sample_indices: torch.Tensor, logits: torch.Tensor, targets: torch.Tensor):
        indices_np = sample_indices.detach().cpu().numpy()
        targets_np = targets.detach().cpu().numpy()
        
        loss = F.cross_entropy(logits, targets, reduction='none').detach().cpu().numpy()
        self.current_epoch_losses[indices_np] = loss
        self.sum_loss[indices_np] += loss
        
        probs = F.softmax(logits, dim=1).detach().cpu().numpy()
        target_probs = probs[np.arange(len(targets_np)), targets_np]
        probs[np.arange(len(targets_np)), targets_np] = -1
        max_other_probs = probs.max(axis=1)
        
        margin = target_probs - max_other_probs
        self.sum_aum[indices_np] += margin
        self.epoch_counts[indices_np] += 1

    def finalize_epoch(self):
        pass

    def get_avg_loss(self) -> np.ndarray:
        counts = np.maximum(self.epoch_counts, 1)
        return self.sum_loss / counts

    def get_aum(self) -> np.ndarray:
        counts = np.maximum(self.epoch_counts, 1)
        return self.sum_aum / counts

    def get_epoch_losses(self) -> np.ndarray:
        return self.current_epoch_losses.copy()
