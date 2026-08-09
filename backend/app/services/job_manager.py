"""Background job orchestrator for training and experiment pipelines."""
import asyncio
import uuid
import os
import json
import traceback
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from app.config import get_settings
from app.database import (
    create_training_run, update_training_run, get_dataset, get_training_run,
    insert_valuations_batch, create_experiment, update_experiment,
)
from app.services.ws_manager import manager as ws_manager


class JobManager:
    """Manages background training and experiment jobs."""

    def __init__(self):
        self.current_job: Optional[Dict[str, Any]] = None
        self.cancel_event = asyncio.Event()

    # ------------------------------------------------------------------ #
    #  Training pipeline                                                  #
    # ------------------------------------------------------------------ #

    async def start_training_job(self, config_dict: dict) -> str:
        """Starts the full training + valuation pipeline in the background."""
        run_id = str(uuid.uuid4())
        settings = get_settings()

        await create_training_run(settings.DB_PATH, {
            "id": run_id,
            "dataset_id": config_dict["dataset_id"],
            "model_name": config_dict.get("model_name", "simple_cnn"),
            "task_type": config_dict.get("task_type"),
            "target_column": config_dict.get("target_column"),
            "template": config_dict.get("template"),
            "epochs": config_dict.get("epochs", settings.DEFAULT_EPOCHS),
            "learning_rate": config_dict.get("learning_rate", settings.DEFAULT_LR),
            "status": "starting",
            "current_epoch": 0,
            "train_loss": 0.0,
            "val_accuracy": 0.0,
            "started_at": datetime.now().isoformat(),
        })

        self.current_job = {"type": "training", "id": run_id, "status": "running"}
        self.cancel_event.clear()

        asyncio.create_task(self._run_training_pipeline(run_id, config_dict))
        return run_id

    async def _run_training_pipeline(self, run_id: str, config_dict: dict):
        """Full pipeline: train → TracIn → embeddings → unified scores → DB."""
        settings = get_settings()
        try:
            await update_training_run(settings.DB_PATH, run_id, {"status": "loading_data"})
            await ws_manager.broadcast({"run_id": run_id, "status": "loading_data", "message": "Loading dataset..."})

            # ---------- 1. Load dataset ---------- #
            dataset_info = await get_dataset(settings.DB_PATH, config_dict["dataset_id"])
            if not dataset_info:
                raise ValueError(f"Dataset {config_dict['dataset_id']} not found")

            train_loader, val_loader, ds_meta = await asyncio.to_thread(
                self._load_dataset, dataset_info, config_dict.get("target_column")
            )

            # ---------- 2. Train model ---------- #
            await update_training_run(settings.DB_PATH, run_id, {"status": "training"})
            await ws_manager.broadcast({"run_id": run_id, "status": "training", "message": "Training started..."})

            checkpoint_dir = os.path.join(str(settings.CHECKPOINT_DIR), run_id)
            metrics_path = os.path.join(str(settings.METRICS_DIR), f"{run_id}.h5")
            os.makedirs(checkpoint_dir, exist_ok=True)

            epochs = config_dict.get("epochs", settings.DEFAULT_EPOCHS)
            lr = config_dict.get("learning_rate", settings.DEFAULT_LR)
            model_name = config_dict.get("template") or config_dict.get("model_name", "simple_cnn")

            # Create progress callback that posts WebSocket updates
            loop = asyncio.get_event_loop()

            def progress_callback(epoch, train_loss, val_acc, msg):
                asyncio.run_coroutine_threadsafe(
                    self._on_epoch_complete(run_id, epoch, epochs, train_loss, val_acc, msg),
                    loop,
                )

            trainer_results = await asyncio.to_thread(
                self._train_model,
                model_name, ds_meta["num_classes"], train_loader, val_loader,
                epochs, lr, checkpoint_dir, metrics_path,
                config_dict.get("checkpoint_interval", settings.CHECKPOINT_INTERVAL),
                progress_callback,
                ds_meta.get("sample_shape"),
            )

            if self.cancel_event.is_set():
                await update_training_run(settings.DB_PATH, run_id, {
                    "status": "cancelled", "completed_at": datetime.now().isoformat(),
                })
                return

            # ---------- 3. Post-training valuation ---------- #
            await update_training_run(settings.DB_PATH, run_id, {"status": "computing_valuations"})
            await ws_manager.broadcast({"run_id": run_id, "status": "computing_valuations", "message": "Computing TracIn scores..."})

            valuation_data = await asyncio.to_thread(
                self._compute_valuations,
                model_name, ds_meta["num_classes"], checkpoint_dir,
                train_loader, val_loader, trainer_results,
            )

            # ---------- 4. Store results ---------- #
            await update_training_run(settings.DB_PATH, run_id, {"status": "storing_results"})
            await ws_manager.broadcast({"run_id": run_id, "status": "storing_results", "message": "Saving valuation results..."})

            rows = []
            for i in range(len(valuation_data["unified_scores"])):
                rows.append({
                    "run_id": run_id,
                    "sample_index": int(i),
                    "forgetting_count": int(valuation_data["forgetting_counts"][i]),
                    "avg_loss": float(valuation_data["avg_loss"][i]),
                    "aum_score": float(valuation_data["aum_scores"][i]),
                    "tracin_score": float(valuation_data["tracin_scores"][i]),
                    "rarity_score": float(valuation_data["rarity_scores"][i]),
                    "unified_score": float(valuation_data["unified_scores"][i]),
                    "category": valuation_data["categories"][i],
                    "embedding_x": float(valuation_data["embeddings_2d"][i, 0]),
                    "embedding_y": float(valuation_data["embeddings_2d"][i, 1]),
                })

            await insert_valuations_batch(settings.DB_PATH, rows)

            # ---------- 5. Finalize ---------- #
            final_loss = trainer_results.get("final_train_loss", 0.0)
            final_acc = trainer_results.get("final_val_accuracy", 0.0)

            await update_training_run(settings.DB_PATH, run_id, {
                "status": "completed",
                "train_loss": final_loss,
                "val_accuracy": final_acc,
                "current_epoch": epochs,
                "checkpoint_dir": checkpoint_dir,
                "metrics_path": metrics_path,
                "completed_at": datetime.now().isoformat(),
            })

            await ws_manager.broadcast({
                "run_id": run_id, "status": "completed",
                "train_loss": final_loss, "val_accuracy": final_acc,
                "message": "Training and valuation complete!",
            })

        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            traceback.print_exc()
            await update_training_run(settings.DB_PATH, run_id, {
                "status": f"failed",
                "completed_at": datetime.now().isoformat(),
            })
            await ws_manager.broadcast({
                "run_id": run_id, "status": "failed", "message": error_msg,
            })
        finally:
            if self.current_job and self.current_job.get("id") == run_id:
                self.current_job = None

    async def _on_epoch_complete(self, run_id, epoch, total_epochs, train_loss, val_acc, msg):
        """WebSocket + DB update after each epoch."""
        settings = get_settings()
        await update_training_run(settings.DB_PATH, run_id, {
            "current_epoch": epoch + 1,
            "train_loss": train_loss,
            "val_accuracy": val_acc,
        })
        await ws_manager.broadcast({
            "run_id": run_id,
            "status": "training",
            "epoch": epoch + 1,
            "total_epochs": total_epochs,
            "train_loss": round(train_loss, 4),
            "val_accuracy": round(val_acc, 4),
            "progress": round((epoch + 1) / total_epochs * 100, 1),
            "message": msg,
        })

    # ---- blocking helpers (run in thread) ---- #

    @staticmethod
    def _load_dataset(dataset_info: dict, target_column: str = None):
        """Load dataset based on type — runs in thread."""
        from app.engine.data_loader import load_cifar10, load_image_folder, load_csv_dataset

        ds_type = dataset_info["type"]
        ds_path = dataset_info["path"]
        t_col = target_column or dataset_info.get("target_column") or "target"

        if ds_type == "cifar10":
            return load_cifar10(ds_path)
        elif ds_type == "image_folder":
            return load_image_folder(ds_path)
        elif ds_type == "csv":
            return load_csv_dataset(ds_path, target_col=t_col)
        else:
            raise ValueError(f"Unknown dataset type: {ds_type}")

    @staticmethod
    def _train_model(model_name, num_classes, train_loader, val_loader,
                     epochs, lr, checkpoint_dir, metrics_path,
                     checkpoint_interval, progress_callback, sample_shape=None):
        """Run the training loop — blocking, runs in thread."""
        from app.engine.models import get_model
        from app.engine.trainer import DataValuatorTrainer

        kwargs = {}
        if model_name == 'tabular' and sample_shape:
            kwargs['input_dim'] = sample_shape[0]

        model = get_model(model_name, num_classes, **kwargs)

        config = {
            "epochs": epochs,
            "lr": lr,
            "save_dir": checkpoint_dir,
            "storage_path": metrics_path,
            "checkpoint_interval": checkpoint_interval,
        }

        trainer = DataValuatorTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            config=config,
            progress_callback=progress_callback,
        )

        tracker_results = trainer.train()

        # Attach final metrics
        tracker_results["model"] = model
        tracker_results["final_train_loss"] = float(tracker_results.get("final_train_loss", 0.0))
        tracker_results["final_val_accuracy"] = float(tracker_results.get("final_val_accuracy", 0.0))

        return tracker_results

    @staticmethod
    def _compute_valuations(model_name, num_classes, checkpoint_dir,
                            train_loader, val_loader, trainer_results):
        """Post-training valuation: TracIn + embeddings + unified scores."""
        import torch
        from app.engine.models import get_model
        from app.engine.tracin import compute_tracin_scores
        from app.engine.embeddings import extract_embeddings, compute_rarity_scores, compute_umap_projection
        from app.engine.valuator import compute_unified_scores

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = trainer_results.get("model")
        if model is None:
            model = get_model(model_name, num_classes)

        # Collect checkpoint paths and learning rates
        checkpoint_files = sorted([
            f for f in os.listdir(checkpoint_dir) if f.endswith(".pt")
        ])
        checkpoint_paths = [os.path.join(checkpoint_dir, f) for f in checkpoint_files]

        # TracIn scores
        if len(checkpoint_paths) >= 2:
            # Use uniform learning rate estimate for simplicity
            lrs = [0.01] * len(checkpoint_paths)
            tracin_scores = compute_tracin_scores(
                model_class=type(model),
                model_kwargs={"num_classes": num_classes},
                checkpoint_paths=checkpoint_paths,
                learning_rates=lrs,
                train_loader=train_loader,
                val_loader=val_loader,
                device=device,
            )
        else:
            tracin_scores = np.zeros(len(train_loader.dataset), dtype=np.float32)

        # Embeddings & rarity
        model.eval()
        embeddings, indices = extract_embeddings(model, train_loader, device)
        rarity_scores = compute_rarity_scores(embeddings)
        embeddings_2d = compute_umap_projection(embeddings)

        # Unified scores
        forgetting_counts = trainer_results["forgetting_counts"]
        avg_loss = trainer_results["avg_loss"]
        aum_scores = trainer_results["aum_scores"]

        unified_scores, categories = compute_unified_scores(
            forgetting_counts, avg_loss, aum_scores, tracin_scores, rarity_scores,
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

    # ------------------------------------------------------------------ #
    #  Experiment pipeline                                                #
    # ------------------------------------------------------------------ #

    async def start_experiment_job(self, config_dict: dict) -> str:
        """Start a pruning or label-corruption experiment."""
        exp_id = str(uuid.uuid4())
        settings = get_settings()

        await create_experiment(settings.DB_PATH, {
            "id": exp_id,
            "run_id": config_dict["run_id"],
            "type": config_dict.get("type", "prune"),
            "config": json.dumps(config_dict),
            "status": "starting",
            "started_at": datetime.now().isoformat(),
        })

        asyncio.create_task(self._run_experiment(exp_id, config_dict))
        return exp_id

    async def _run_experiment(self, exp_id: str, config_dict: dict):
        """Run a pruning or label-corruption experiment in background."""
        settings = get_settings()
        try:
            await update_experiment(settings.DB_PATH, exp_id, {"status": "running"})

            run_info = await get_training_run(settings.DB_PATH, config_dict["run_id"])
            if not run_info:
                raise ValueError(f"Training run {config_dict['run_id']} not found")

            dataset_info = await get_dataset(settings.DB_PATH, run_info["dataset_id"])
            if not dataset_info:
                raise ValueError(f"Dataset {run_info['dataset_id']} not found")
                
            from app.database import get_refined_valuations
            exclude_cats = config_dict.get("exclude_categories", ["harmful", "redundant"])
            refined_vals = await get_refined_valuations(settings.DB_PATH, config_dict["run_id"], exclude_cats)
            kept_indices = [v["sample_index"] for v in refined_vals]

            result = await asyncio.to_thread(
                self._run_experiment_blocking, config_dict, run_info, dataset_info, kept_indices
            )

            await update_experiment(settings.DB_PATH, exp_id, {
                "status": "completed",
                "original_accuracy": result.get("original_accuracy", 0.0),
                "result_accuracy": result.get("result_accuracy", 0.0),
                "samples_removed": result.get("samples_removed", 0),
                "precision": result.get("precision"),
                "recall": result.get("recall"),
                "completed_at": datetime.now().isoformat(),
            })

        except Exception as e:
            traceback.print_exc()
            await update_experiment(settings.DB_PATH, exp_id, {
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
            })

    @staticmethod
    def _run_experiment_blocking(config_dict, run_info, dataset_info, kept_indices):
        """Blocking experiment execution — pruning and retraining."""
        import os
        import tempfile
        from torch.utils.data import Subset, DataLoader
        from app.engine.trainer import DataValuatorTrainer
        from app.engine.models import get_model
        
        # load original dataset
        train_loader_orig, val_loader, ds_meta = JobManager._load_dataset(dataset_info, run_info.get("target_column"))
        
        # filter train_loader
        pruned_dataset = Subset(train_loader_orig.dataset, kept_indices)
        num_workers = getattr(train_loader_orig, 'num_workers', 0)
        train_loader = DataLoader(
            pruned_dataset, 
            batch_size=train_loader_orig.batch_size, 
            shuffle=True, 
            num_workers=num_workers
        )
        
        # model setup
        model_name = run_info.get("template") or run_info.get("model_name", "simple_cnn")
        epochs = config_dict.get("epochs", run_info.get("epochs", 20))
        lr = config_dict.get("learning_rate", run_info.get("learning_rate", 0.01))
        
        kwargs = {}
        if model_name == 'tabular' and ds_meta.get('sample_shape'):
            kwargs['input_dim'] = ds_meta['sample_shape'][0]
            
        model = get_model(model_name, ds_meta["num_classes"], **kwargs)
        
        # Create a temporary file for HDF5 storage that won't crash on Windows
        fd, temp_h5_path = tempfile.mkstemp(suffix=".h5")
        os.close(fd)
        
        config = {
            "epochs": epochs,
            "lr": lr,
            "original_num_samples": len(train_loader_orig.dataset),
            "save_dir": None,
            "storage_path": temp_h5_path, 
            "checkpoint_interval": 9999
        }
        
        try:
            trainer = DataValuatorTrainer(
                 model=model,
                 train_loader=train_loader,
                 val_loader=val_loader,
                 config=config
            )
            results = trainer.train()
        finally:
            # Clean up the temporary HDF5 file
            if os.path.exists(temp_h5_path):
                try:
                    os.remove(temp_h5_path)
                except Exception:
                    pass
        
        return {
            "original_accuracy": run_info.get("val_accuracy", 0.0),
            "result_accuracy": results.get("final_val_accuracy", 0.0),
            "samples_removed": len(train_loader_orig.dataset) - len(kept_indices),
            "precision": None,
            "recall": None,
        }

    # ------------------------------------------------------------------ #
    #  Job control                                                        #
    # ------------------------------------------------------------------ #

    def get_current_job(self) -> Optional[Dict[str, Any]]:
        """Returns the currently running job or None."""
        return self.current_job

    def cancel_current_job(self):
        """Signal the current job to stop."""
        if self.current_job:
            self.cancel_event.set()


job_manager = JobManager()
