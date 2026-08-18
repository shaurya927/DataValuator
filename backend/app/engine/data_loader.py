import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, transforms
from typing import Tuple, Dict, Any, Optional
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

class IndexedDataset(Dataset):
    """Wrapper dataset that yields (index, data, target) tuples."""
    def __init__(self, base_dataset: Dataset):
        self.base_dataset = base_dataset

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, idx: int) -> Tuple[int, Any, Any]:
        data, target = self.base_dataset[idx]
        return idx, data, target

def load_cifar10(data_dir: str, batch_size: int = 128) -> Tuple[DataLoader, DataLoader, Dict[str, Any]]:
    """Loads CIFAR-10 dataset."""
    train_transform = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    val_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    train_set = datasets.CIFAR10(root=data_dir, train=True, download=True, transform=train_transform)
    val_set = datasets.CIFAR10(root=data_dir, train=False, download=True, transform=val_transform)

    indexed_train = IndexedDataset(train_set)
    indexed_val = IndexedDataset(val_set)

    train_loader = DataLoader(indexed_train, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(indexed_val, batch_size=batch_size, shuffle=False, num_workers=0)

    dataset_info = {
        "num_samples": len(train_set),
        "num_classes": 10,
        "class_names": train_set.classes,
        "sample_shape": (3, 32, 32)
    }

    return train_loader, val_loader, dataset_info

def load_image_folder(path: str, batch_size: int = 64, img_size: int = 32) -> Tuple[DataLoader, DataLoader, Dict[str, Any]]:
    """Loads images from a folder with class subfolders."""
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(img_size),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    val_transform = transforms.Compose([
        transforms.Resize(img_size + 4),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    train_dir = os.path.join(path, "train")
    val_dir = os.path.join(path, "val")
    
    if not os.path.exists(val_dir):
        dataset = datasets.ImageFolder(path, transform=train_transform)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])
    else:
        train_set = datasets.ImageFolder(train_dir, transform=train_transform)
        val_set = datasets.ImageFolder(val_dir, transform=val_transform)

    indexed_train = IndexedDataset(train_set)
    indexed_val = IndexedDataset(val_set)

    train_loader = DataLoader(indexed_train, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(indexed_val, batch_size=batch_size, shuffle=False, num_workers=0)

    classes = train_set.dataset.classes if hasattr(train_set, 'dataset') else train_set.classes
    dataset_info = {
        "num_samples": len(train_set),
        "num_classes": len(classes),
        "class_names": classes,
        "sample_shape": (3, img_size, img_size)
    }

    return train_loader, val_loader, dataset_info

class TabularDataset(Dataset):
    def __init__(self, data: np.ndarray, targets: np.ndarray, task_type: str = "classification"):
        self.data = torch.tensor(data, dtype=torch.float32)
        if task_type == "classification":
            self.targets = torch.tensor(targets, dtype=torch.long)
        else:
            self.targets = torch.tensor(targets, dtype=torch.float32).unsqueeze(1)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.data[idx], self.targets[idx]

def create_pytorch_dataloaders(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, task_type: str = "classification", batch_size: int = 64) -> Tuple[DataLoader, DataLoader]:
    """Helper to convert numpy arrays into PyTorch DataLoaders with IndexedDataset."""
    train_set = TabularDataset(X_train, y_train, task_type)
    val_set = TabularDataset(X_val, y_val, task_type)
    
    indexed_train = IndexedDataset(train_set)
    indexed_val = IndexedDataset(val_set)
    
    train_loader = DataLoader(indexed_train, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(indexed_val, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader

def load_csv_dataset(path: str, target_col: str, task_type: str = "classification") -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray], Dict[str, Any]]:
    """Loads and robustly preprocesses tabular dataset for any model type."""
    df = pd.read_csv(path)
    
    # Drop rows where target is NaN
    if target_col in df.columns:
        df = df.dropna(subset=[target_col])
    else:
        # Fallback if target_col is somehow missing, just pick the last column
        target_col = df.columns[-1]
        df = df.dropna(subset=[target_col])
        
    y_raw = df[target_col].values
    X_df = df.drop(columns=[target_col])
    
    # Identify column types
    numeric_cols = X_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X_df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # Create preprocessing pipelines
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_cols),
            ('cat', categorical_transformer, categorical_cols)
        ]
    )
    
    X = preprocessor.fit_transform(X_df)
    
    # Process target
    if task_type == "classification":
        le = LabelEncoder()
        y = le.fit_transform(y_raw)
        classes = list(le.classes_)
        num_classes = len(classes)
    else:
        y = y_raw.astype(np.float32)
        classes = []
        num_classes = 1
        
    # Split 80/20 deterministically
    rng = np.random.RandomState(42)
    indices = rng.permutation(len(X))
    split_idx = int(0.8 * len(X))
    train_idx, val_idx = indices[:split_idx], indices[split_idx:]
    
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    
    dataset_info = {
        "num_samples": len(X_train),
        "num_classes": num_classes,
        "class_names": classes,
        "sample_shape": (X.shape[1],),
        "task_type": task_type
    }
    
    return (X_train, y_train), (X_val, y_val), dataset_info
