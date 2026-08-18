import asyncio
from app.services.job_manager import JobManager
from app.config import get_settings

async def test():
    jm = JobManager()
    
    # 1. Start XGBoost
    config1 = {
        "dataset_id": "titanic", # Assume titanic is the id, or get it from db
        "model_name": "xgboost",
        "task_type": "classification",
        "target_column": "Survived",
        "epochs": 20,
        "learning_rate": 0.01,
    }
    
    # Try tabular PyTorch
    config2 = {
        "dataset_id": "titanic",
        "model_name": "tabular",
        "task_type": "classification",
        "target_column": "Survived",
        "epochs": 20,
        "learning_rate": 0.01,
    }
    
    # Let's just fetch the first dataset from the DB to be safe
    import sqlite3
    import json
    settings = get_settings()
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM datasets WHERE type='csv' LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("No csv dataset found")
        return
    
    ds_id, ds_path = row
    config1["dataset_id"] = ds_id
    config2["dataset_id"] = ds_id
    
    print(f"Testing with dataset: {ds_id} at {ds_path}")
    
    # Try training tabular net
    try:
        print("Testing Tabular Net...")
        await jm.start_training_job(config2)
        # We need to wait for it since it runs in the background
        while jm.current_job:
            await asyncio.sleep(1)
    except Exception as e:
        import traceback
        traceback.print_exc()

    # Try training XGBoost
    try:
        print("Testing XGBoost...")
        await jm.start_training_job(config1)
        while jm.current_job:
            await asyncio.sleep(1)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
