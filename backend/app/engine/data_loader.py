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

def load_csv_dataset(path: str, target_col: str, task_type: str = "classification", prep_config: dict = None) -> Tuple[Tuple[np.ndarray, np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray], Dict[str, Any]]:
    """Loads and robustly preprocesses tabular dataset for any model type."""
    from app.engine.preprocessing import build_and_run_pipeline
    
    df = pd.read_csv(path)
    
    if not prep_config:
        prep_config = {}
        
    prep_config["task_type"] = task_type
    
    res = build_and_run_pipeline(df, target_col, prep_config, is_inference=False)
    
    X_train, y_train, train_idx = res["train"]
    X_val, y_val, val_idx = res["test"]
    
    dataset_info = {
        "num_samples": len(X_train),
        "num_classes": res["num_classes"],
        "class_names": res["classes"],
        "sample_shape": res["sample_shape"],
        "task_type": task_type,
        "features": res["features"]
    }
    
    return (X_train, y_train, train_idx), (X_val, y_val, val_idx), dataset_info
    
def load_image_csv(path: str, batch_size: int = 64) -> Tuple[DataLoader, DataLoader, Dict[str, Any]]:
    """Loads a CSV containing flattened images (like Fashion MNIST) and reshapes it to 3 channels."""
    df = pd.read_csv(path)
    
    # Assume first column or column named 'label' is the target
    if 'label' in df.columns:
        y = df['label'].values
        X = df.drop('label', axis=1).values
    else:
        y = df.iloc[:, 0].values
        X = df.iloc[:, 1:].values
        
    num_samples, num_features = X.shape
    # Calculate image dimension assuming square image
    img_size = int(np.sqrt(num_features))
    if img_size * img_size != num_features:
        raise ValueError(f"Cannot reshape {num_features} features into a square image.")
        
    # Reshape to (N, 1, H, W)
    X = X.reshape(-1, 1, img_size, img_size).astype(np.float32)
    # Normalize to 0-1
    if X.max() > 1.0:
        X = X / 255.0
        
    # Repeat channels to match CNN expectation (3 channels)
    X = np.repeat(X, 3, axis=1) # (N, 3, H, W)
    
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # We can use TabularDataset directly since it wraps torch.tensor
    class ImageCSVDataset(Dataset):
        def __init__(self, data, targets):
            self.data = torch.tensor(data, dtype=torch.float32)
            self.targets = torch.tensor(targets, dtype=torch.long)
        def __len__(self):
            return len(self.data)
        def __getitem__(self, idx):
            return self.data[idx], self.targets[idx]
            
    train_set = ImageCSVDataset(X_train, y_train)
    val_set = ImageCSVDataset(X_val, y_val)
    
    indexed_train = IndexedDataset(train_set)
    indexed_val = IndexedDataset(val_set)
    
    train_loader = DataLoader(indexed_train, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(indexed_val, batch_size=batch_size, shuffle=False)
    
    dataset_info = {
        "num_samples": len(X_train),
        "num_classes": len(np.unique(y_train)),
        "class_names": [str(c) for c in np.unique(y_train)],
        "sample_shape": (3, img_size, img_size)
    }
    
    return train_loader, val_loader, dataset_info
