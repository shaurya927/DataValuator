from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import uuid
import shutil

from app.config import Settings, get_settings
from app.database import list_datasets, get_dataset, delete_dataset, create_dataset
from app.models.dataset import DatasetInfo, DatasetPreview, DatasetUploadResponse
from app.engine.data_loader import load_cifar10

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

@router.get("/", response_model=List[DatasetInfo])
async def get_all_datasets(settings: Settings = Depends(get_settings)):
    datasets = await list_datasets(settings.DB_PATH)
    return [DatasetInfo(**ds) for ds in datasets]

@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...), 
    task_type: Optional[str] = Form(None),
    target_column: Optional[str] = Form(None),
    template: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings)
):
    import zipfile
    dataset_id = str(uuid.uuid4())
    file_path = settings.UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    filename = file.filename.lower()
    
    if filename.endswith('.zip'):
        extract_dir = settings.UPLOAD_DIR / dataset_id
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        # Update path to point to the extracted directory
        file_path = extract_dir
        ds_type = 'image_folder'
    else:
        ds_type = 'csv' if filename.endswith('.csv') else 'image_folder'
    
    data = {
        'id': dataset_id,
        'name': file.filename,
        'type': ds_type,
        'task_type': task_type,
        'target_column': target_column,
        'default_template': template,
        'num_samples': 0,
        'num_classes': 0,
        'created_at': datetime.now().isoformat(),
        'path': str(file_path)
    }
    await create_dataset(settings.DB_PATH, data)
    return DatasetUploadResponse(id=dataset_id, message="Upload successful")

@router.post("/cifar10", response_model=DatasetUploadResponse)
async def download_cifar10(settings: Settings = Depends(get_settings)):
    dataset_id = str(uuid.uuid4())
    path = settings.DATA_DIR / "cifar10"
    
    data = {
        'id': dataset_id,
        'name': 'CIFAR-10',
        'type': 'cifar10',
        'num_samples': 50000,
        'num_classes': 10,
        'created_at': datetime.now().isoformat(),
        'path': str(path)
    }
    await create_dataset(settings.DB_PATH, data)
    return DatasetUploadResponse(id=dataset_id, message="CIFAR-10 downloaded")

@router.get("/{dataset_id}", response_model=DatasetPreview)
async def get_dataset_details(dataset_id: str, settings: Settings = Depends(get_settings)):
    ds = await get_dataset(settings.DB_PATH, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetPreview(info=DatasetInfo(**ds), preview_data=[])

@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset_route(dataset_id: str, settings: Settings = Depends(get_settings)):
    ds = await get_dataset(settings.DB_PATH, dataset_id)
    if ds and ds.get("path"):
        import os
        import shutil
        path = ds["path"]
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        except Exception as e:
            print(f"Failed to delete files for dataset {dataset_id}: {e}")
            
    await delete_dataset(settings.DB_PATH, dataset_id)
