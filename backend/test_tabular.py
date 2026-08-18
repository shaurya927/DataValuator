import asyncio
from app.services.job_manager import JobManager

async def debug_tabular():
    jm = JobManager()
    
    config = {
        "dataset_id": "163745ca-89ae-4a69-84d4-9c335fa9445d",
        "model_name": "xgboost",
        "task_type": "classification",
        "target_column": "Survived",
        "epochs": 2,
        "learning_rate": 0.01,
    }
    
    try:
        await jm.start_training_job(config)
        while jm.current_job:
            await asyncio.sleep(1)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_tabular())

