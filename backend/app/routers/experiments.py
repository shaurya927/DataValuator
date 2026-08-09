from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.config import Settings, get_settings
from app.models.valuation import ExperimentConfig, ExperimentResult
from app.services.job_manager import job_manager

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

@router.post("/prune", response_model=dict)
async def start_prune_experiment(config: ExperimentConfig, settings: Settings = Depends(get_settings)):
    exp_id = await job_manager.start_experiment_job({"type": "prune", **config.dict()})
    return {"experiment_id": exp_id, "message": "Prune experiment started"}

@router.post("/random-prune", response_model=dict)
async def start_random_prune_experiment(config: ExperimentConfig, settings: Settings = Depends(get_settings)):
    exp_id = await job_manager.start_experiment_job({"type": "random_prune", **config.dict()})
    return {"experiment_id": exp_id, "message": "Random prune experiment started"}

@router.post("/label-corruption", response_model=dict)
async def start_label_corruption(config: ExperimentConfig, settings: Settings = Depends(get_settings)):
    exp_id = await job_manager.start_experiment_job({"type": "label_corruption", **config.dict()})
    return {"experiment_id": exp_id, "message": "Label corruption experiment started"}

@router.get("/{experiment_id}/results", response_model=ExperimentResult)
async def get_results(experiment_id: str, settings: Settings = Depends(get_settings)):
    from app.database import get_experiment
    exp = await get_experiment(settings.DB_PATH, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentResult(**exp)

@router.get("/history", response_model=List[ExperimentResult])
async def get_experiments_history(settings: Settings = Depends(get_settings)):
    from app.database import list_experiments
    exps = await list_experiments(settings.DB_PATH)
    return [ExperimentResult(**e) for e in exps]
