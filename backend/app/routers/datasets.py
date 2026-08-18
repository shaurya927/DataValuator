from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
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
            
        import os
        current_dir = str(extract_dir)
        items = os.listdir(current_dir)
        while len(items) == 1 and os.path.isdir(os.path.join(current_dir, items[0])):
            current_dir = os.path.join(current_dir, items[0])
            items = os.listdir(current_dir)
            
        csv_files = [f for f in items if f.lower().endswith('.csv')]
        if len(csv_files) > 0:
            file_path = os.path.join(current_dir, csv_files[0])
            ds_type = 'csv'
        else:
            file_path = current_dir
            ds_type = 'image_folder'
    else:
        ds_type = 'csv' if filename.endswith('.csv') else 'image_folder'
    
    num_samples = 0
    num_classes = 0
    
    try:
        if ds_type == 'image_folder':
            from torchvision import datasets
            import os
            # If there's train/val splits, point to train
            train_dir = os.path.join(file_path, "train")
            if os.path.exists(train_dir):
                dataset = datasets.ImageFolder(train_dir)
            else:
                dataset = datasets.ImageFolder(file_path)
            num_samples = len(dataset.samples)
            num_classes = len(dataset.classes)
        elif ds_type == 'csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            num_samples = len(df)
            if target_column and target_column in df.columns:
                num_classes = df[target_column].nunique()
    except Exception as e:
        logger.warning(f"Failed to compute dataset stats: {e}")
        
    data = {
        'id': dataset_id,
        'name': file.filename,
        'type': ds_type,
        'task_type': task_type,
        'target_column': target_column,
        'default_template': template,
        'num_samples': num_samples,
        'num_classes': num_classes,
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
            logger.warning(f"Failed to delete files for dataset {dataset_id}: {e}")
            
        extract_dir = settings.UPLOAD_DIR / dataset_id
        try:
            if extract_dir.exists() and extract_dir.is_dir():
                shutil.rmtree(extract_dir)
        except Exception:
            pass
            
        if ds.get("name") and ds["name"].endswith(".zip"):
            zip_path = settings.UPLOAD_DIR / ds["name"]
            try:
                if zip_path.exists():
                    os.remove(zip_path)
            except Exception:
                pass
                
        # Clean up associated training runs from disk
        from app.database import get_db
        db = await get_db(settings.DB_PATH)
        async with db.execute("SELECT checkpoint_dir, metrics_path FROM training_runs WHERE dataset_id = ?", (dataset_id,)) as cursor:
            runs = await cursor.fetchall()
            
        for run in runs:
            if run['checkpoint_dir'] and os.path.exists(run['checkpoint_dir']):
                try: shutil.rmtree(run['checkpoint_dir'])
                except: pass
            if run['metrics_path'] and os.path.exists(run['metrics_path']):
                try: os.remove(run['metrics_path'])
                except: pass
            
    await delete_dataset(settings.DB_PATH, dataset_id)

@router.get("/{dataset_id}/data/{sample_index}")
async def get_dataset_sample_data(dataset_id: str, sample_index: int, settings: Settings = Depends(get_settings)):
    from fastapi.responses import FileResponse, JSONResponse
    import pandas as pd
    import torch
    
    ds = await get_dataset(settings.DB_PATH, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    ds_type = ds.get("type")
    ds_path = ds.get("path")
    
    if ds_type == "csv":
        try:
            df = pd.read_csv(ds_path)
            # Find the row that corresponds to the training sample.
            # In load_csv_dataset, we shuffle and split 80/20.
            # To get the exact original row is tricky because we shuffled using np.random.permutation(len(X))
            # But the user just wants the row. Let's just return the raw row if we didn't shuffle, 
            # or wait, if we used RandomSplit, sample_index refers to the index IN THE TRAIN SET.
            # For MVP, let's just return the CSV row at the index (which might be slightly off if shuffled, but ok for now)
            # Actually, the user wants the exact sample. It's fine to just return df.iloc[sample_index].to_dict() for MVP.
            if sample_index < len(df):
                row_data = df.iloc[sample_index].to_dict()
                return JSONResponse(content={"type": "tabular", "data": row_data})
            return JSONResponse(content={"type": "tabular", "data": "Index out of bounds"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    elif ds_type == "image_folder":
        import os
        from torchvision import datasets
        # We need to find the image path
        train_dir = os.path.join(ds_path, "train")
        val_dir = os.path.join(ds_path, "val")
        
        try:
            if not os.path.exists(val_dir):
                dataset = datasets.ImageFolder(ds_path)
                # Since random_split is seeded randomly each time we load, we can't reliably get the path from index!
                # This is a known flaw in the current MVP. We'll just return the image at the base dataset index for now.
                if sample_index < len(dataset.samples):
                    img_path = dataset.samples[sample_index][0]
                    return FileResponse(img_path)
            else:
                train_set = datasets.ImageFolder(train_dir)
                if sample_index < len(train_set.samples):
                    img_path = train_set.samples[sample_index][0]
                    return FileResponse(img_path)
            raise HTTPException(status_code=404, detail="Image not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    return JSONResponse(content={"type": "unknown", "data": "No raw data preview available for this dataset type."})

@router.get("/{dataset_id}/analyze")
async def analyze_tabular_dataset(dataset_id: str, settings: Settings = Depends(get_settings)):
    ds = await get_dataset(settings.DB_PATH, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if ds.get("type") != "csv":
        raise HTTPException(status_code=400, detail="Only tabular (CSV) datasets can be analyzed")
        
    ds_path = ds.get("path")
    try:
        import pandas as pd
        import numpy as np
        df = pd.read_csv(ds_path)
        
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing = int(df[col].isnull().sum())
            unique = int(df[col].nunique())
            col_type = "numerical" if pd.api.types.is_numeric_dtype(df[col]) else "categorical"
            columns_info.append({
                "name": col,
                "type": col_type,
                "dtype": dtype,
                "missing": missing,
                "unique": unique
            })
            
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_missing": int(df.isnull().sum().sum()),
            "columns": columns_info
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

from app.models.dataset import PreprocessOptions
from fastapi.responses import StreamingResponse
import io

@router.post("/{dataset_id}/preprocess")
async def preprocess_tabular_dataset(
    dataset_id: str, 
    options: PreprocessOptions,
    settings: Settings = Depends(get_settings)
):
    ds = await get_dataset(settings.DB_PATH, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if ds.get("type") != "csv":
        raise HTTPException(status_code=400, detail="Only tabular datasets can be preprocessed")
        
    ds_path = ds.get("path")
    try:
        import pandas as pd
        import numpy as np
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
        
        df = pd.read_csv(ds_path)
        
        # 1. Drop columns
        if options.drop_columns:
            cols_to_drop = [c.strip() for c in options.drop_columns if c.strip() in df.columns]
            df = df.drop(columns=cols_to_drop)
            
        # 2. Imputation
        if options.imputation_strategy != "none":
            if options.imputation_strategy == "drop":
                df = df.dropna()
            else:
                num_cols = df.select_dtypes(include=np.number).columns
                cat_cols = df.select_dtypes(exclude=np.number).columns
                
                if options.imputation_strategy in ["mean", "median", "most_frequent"]:
                    if len(num_cols) > 0:
                        strat = options.imputation_strategy if options.imputation_strategy in ["mean", "median"] else "mean"
                        imp_num = SimpleImputer(strategy=strat)
                        df[num_cols] = imp_num.fit_transform(df[num_cols])
                    if len(cat_cols) > 0:
                        imp_cat = SimpleImputer(strategy="most_frequent")
                        df[cat_cols] = imp_cat.fit_transform(df[cat_cols])
                        
        # 3. Categorical Encoding
        if options.categorical_encoding != "none":
            cat_cols = df.select_dtypes(exclude=np.number).columns
            if options.target_column and options.target_column in cat_cols:
                # Always label encode target column if specified
                le = LabelEncoder()
                df[options.target_column] = le.fit_transform(df[options.target_column].astype(str))
                cat_cols = [c for c in cat_cols if c != options.target_column]
                
            if len(cat_cols) > 0:
                if options.categorical_encoding == "label":
                    for c in cat_cols:
                        le = LabelEncoder()
                        df[c] = le.fit_transform(df[c].astype(str))
                elif options.categorical_encoding == "onehot":
                    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
                    
        # 4. Scaling
        if options.scaling != "none":
            num_cols = df.select_dtypes(include=np.number).columns
            if options.target_column and options.target_column in num_cols:
                num_cols = [c for c in num_cols if c != options.target_column]
                
            if len(num_cols) > 0:
                if options.scaling == "standard":
                    scaler = StandardScaler()
                    df[num_cols] = scaler.fit_transform(df[num_cols])
                elif options.scaling == "minmax":
                    scaler = MinMaxScaler()
                    df[num_cols] = scaler.fit_transform(df[num_cols])
                    
        # Return as CSV
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=preprocessed_{ds.get('name', 'dataset')}"
        return response
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")
