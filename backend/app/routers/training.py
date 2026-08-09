from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.config import Settings, get_settings
from app.models.training import TrainingConfig, TrainingStatus, TrainingRunInfo
from app.services.job_manager import job_manager
from app.database import list_training_runs, get_training_run

router = APIRouter(prefix="/api/training", tags=["training"])

@router.post("/start", response_model=dict)
async def start_training(config: TrainingConfig, settings: Settings = Depends(get_settings)):
    if job_manager.get_current_job():
        raise HTTPException(status_code=400, detail="Job already running")
    
    run_id = await job_manager.start_training_job(config.dict())
    return {"run_id": run_id, "message": "Training started"}

@router.get("/status", response_model=dict)
async def get_status():
    job = job_manager.get_current_job()
    if not job:
        return {"status": "idle"}
    return job

@router.post("/stop", response_model=dict)
async def stop_training():
    job_manager.cancel_current_job()
    return {"message": "Stop requested"}

@router.get("/history", response_model=List[TrainingRunInfo])
async def get_history(settings: Settings = Depends(get_settings)):
    runs = await list_training_runs(settings.DB_PATH)
    return [TrainingRunInfo(**r) for r in runs]

@router.get("/{run_id}", response_model=TrainingRunInfo)
async def get_run_details(run_id: str, settings: Settings = Depends(get_settings)):
    run = await get_training_run(settings.DB_PATH, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return TrainingRunInfo(**run)
