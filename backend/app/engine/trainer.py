"""DataValuator training loop with integrated metric tracking.

Orchestrates model training while simultaneously recording per-sample
forgetting events, loss trajectories, and AUM (Area Under Margin) scores.
Checkpoints are saved at configurable intervals for post-training TracIn.
"""
import os
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
from typing import Dict, Any, Callable, Optional
import torch.nn.functional as F

from .trackers import ForgettingTracker, LossAUMTracker
from .storage import MetricStore

logger = logging.getLogger(__name__)


class DataValuatorTrainer:
    """Training loop that tracks per-sample valuation metrics.

    Integrates ForgettingTracker and LossAUMTracker into a standard
    PyTorch training loop. Saves model checkpoints at intervals and
    writes per-epoch metrics to HDF5 storage.

    Args:
        model: PyTorch model to train.
        train_loader: Training DataLoader yielding (index, data, target).
        val_loader: Validation DataLoader yielding (index, data, target).
        config: Dict with keys: epochs, lr, save_dir, storage_path,
                checkpoint_interval.
        device: Torch device string. Auto-detects GPU if None.
        progress_callback: Called after each epoch with
            (epoch, train_loss, val_acc, status_msg).
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: Any,
        val_loader: Any,
        config: Dict[str, Any],
        device: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        cancel_event: Optional[Any] = None,
    ):
        self.cancel_event = cancel_event
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model = model.to(self.device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.progress_callback = progress_callback

        self.num_train_samples = config.get("original_num_samples") or len(train_loader.dataset)
        self.max_epochs = config.get("epochs", 20)
        self.checkpoint_interval = config.get("checkpoint_interval", 5)

        # Trackers
        self.forgetting_tracker = ForgettingTracker(self.num_train_samples)
        self.loss_aum_tracker = LossAUMTracker(self.num_train_samples)

        # Optimizer & scheduler
        self.optimizer = optim.SGD(
            self.model.parameters(),
            lr=config.get("lr", 0.01),
            momentum=0.9,
            weight_decay=5e-4,
        )
        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=self.max_epochs)
        self.criterion = nn.CrossEntropyLoss(reduction="none")

        # HDF5 metric storage
        storage_path = config.get("storage_path", "metrics.h5")
        os.makedirs(os.path.dirname(storage_path) if os.path.dirname(storage_path) else ".", exist_ok=True)
        self.store = MetricStore.create(storage_path, self.num_train_samples, self.max_epochs)

        # Track final metrics
        self._final_train_loss = 0.0
        self._final_val_accuracy = 0.0

    def train(self) -> dict:
        """Run the full training loop with metric tracking.

        For each epoch:
          1. Train — record per-sample loss and AUM in LossAUMTracker
          2. Evaluate on training set — track forgetting events
          3. Evaluate on val set — measure accuracy
          4. Save checkpoint at intervals
          5. Write epoch metrics to HDF5
          6. Call progress_callback

        Returns:
            Dict with tracker results and final metrics.
        """
        save_dir = self.config.get("save_dir")
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        for epoch in range(self.max_epochs):
            if self.cancel_event and self.cancel_event.is_set():
                logger.info("Training cancelled via event.")
                break

            # ---- Training pass ---- #
            self.model.train()
            train_loss_sum = 0.0
            train_correct = 0
            train_total = 0

            epoch_losses = np.zeros(self.num_train_samples, dtype=np.float32)
            epoch_margins = np.zeros(self.num_train_samples, dtype=np.float32)
            epoch_correctness = np.zeros(self.num_train_samples, dtype=np.bool_)

            for batch_idx, (indices, data, targets) in enumerate(self.train_loader):
                data, targets = data.to(self.device), targets.to(self.device)

                self.optimizer.zero_grad()
                logits = self.model(data)

                loss_per_sample = self.criterion(logits, targets)
                loss = loss_per_sample.mean()

                loss.backward()
                self.optimizer.step()

                batch_size = len(targets)
                train_loss_sum += loss.item() * batch_size

                indices_np = indices.detach().cpu().numpy()
                losses_np = loss_per_sample.detach().cpu().numpy()

                # Compute logit margins for AUM storage (Classification only)
                if getattr(self, "task_type", "classification") == "classification":
                    with torch.no_grad():
                        preds = logits.argmax(dim=1)
                        target_logits = logits[torch.arange(batch_size, device=self.device), targets]
                        mask = torch.ones_like(logits, dtype=torch.bool)
                        mask[torch.arange(batch_size, device=self.device), targets] = False
                        other_logits = logits[mask].view(batch_size, -1)
                        max_other = other_logits.max(dim=1).values
                        margins = (target_logits - max_other).cpu().numpy()

                    epoch_margins[indices_np] = margins
                    epoch_correctness[indices_np] = (preds == targets).cpu().numpy()
                    train_correct += (preds == targets).sum().item()
                else:
                    margins = -losses_np  # use negative loss as margin
                    epoch_margins[indices_np] = margins
                    epoch_correctness[indices_np] = False
                    
                # Track forgetting events on training data
                self.forgetting_tracker.update(indices, logits, targets)
                
                # Record loss & AUM (must be after margins are computed)
                self.loss_aum_tracker.record_batch(indices, loss_per_sample, margins)
                
                # Store per-sample epoch metrics for HDF5
                epoch_losses[indices_np] = losses_np
                
                train_total += batch_size

            self.loss_aum_tracker.finalize_epoch()
            self.forgetting_tracker.finalize_epoch()

            # ---- Validation pass ---- #
            self.model.eval()
            val_correct = 0
            val_total = 0
            with torch.no_grad():
                for indices, data, targets in self.val_loader:
                    data, targets = data.to(self.device), targets.to(self.device)
                    logits = self.model(data)
                    preds = logits.argmax(dim=1)
                    val_correct += (preds == targets).sum().item()
                    val_total += targets.size(0)

            self.scheduler.step()

            train_loss = train_loss_sum / max(train_total, 1)
            val_acc = val_correct / max(val_total, 1)
            self._final_train_loss = train_loss
            self._final_val_accuracy = val_acc

            # ---- Write epoch metrics to HDF5 ---- #
            self.store.write_epoch(epoch, epoch_losses, epoch_margins, epoch_correctness)

            # ---- Save checkpoint at intervals ---- #
            if save_dir and (epoch + 1) % self.checkpoint_interval == 0:
                ckpt_path = os.path.join(save_dir, f"ckpt_epoch_{epoch:03d}.pt")
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "train_loss": train_loss,
                    "val_accuracy": val_acc,
                    "learning_rate": self.scheduler.get_last_lr()[0],
                }, ckpt_path)

            # ---- Save final checkpoint ---- #
            if save_dir and epoch == self.max_epochs - 1:
                final_path = os.path.join(save_dir, "ckpt_final.pt")
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "train_loss": train_loss,
                    "val_accuracy": val_acc,
                }, final_path)

            # ---- Progress callback ---- #
            if self.progress_callback:
                self.progress_callback(
                    epoch, train_loss, val_acc,
                    f"Epoch {epoch + 1}/{self.max_epochs} — "
                    f"loss: {train_loss:.4f}, val_acc: {val_acc:.4f}",
                )

        self.store.close()

        results = self.get_tracker_results()
        results["final_train_loss"] = self._final_train_loss
        results["final_val_accuracy"] = self._final_val_accuracy
        results["model"] = self.model
        return results

    def get_tracker_results(self) -> dict:
        """Returns accumulated tracker metrics.

        Returns:
            Dict with forgetting_counts, avg_loss, aum_scores arrays.
        """
        return {
            "forgetting_counts": self.forgetting_tracker.get_forgetting_counts(),
            "avg_loss": self.loss_aum_tracker.get_avg_loss(),
            "aum_scores": self.loss_aum_tracker.get_aum(),
            "epoch_losses": self.loss_aum_tracker.get_epoch_losses(),
        }
