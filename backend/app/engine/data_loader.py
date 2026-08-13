import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, transforms
from typing import Tuple, Dict, Any

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
    def __init__(self, data: np.ndarray, targets: np.ndarray):
        self.data = torch.tensor(data, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.data[idx], self.targets[idx]

def load_csv_dataset(path: str, target_col: str, batch_size: int = 64) -> Tuple[DataLoader, DataLoader, Dict[str, Any]]:
    """Loads tabular dataset from CSV."""
    df = pd.read_csv(path)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in numeric_cols:
        numeric_cols.remove(target_col)
    
    X = df[numeric_cols].values
    
    y = df[target_col].astype('category').cat.codes.values
    classes = df[target_col].astype('category').cat.categories.tolist()

    rng = np.random.RandomState(42)
    indices = rng.permutation(len(X))
    split_idx = int(0.8 * len(X))
    train_idx, val_idx = indices[:split_idx], indices[split_idx:]

    train_set = TabularDataset(X[train_idx], y[train_idx])
    val_set = TabularDataset(X[val_idx], y[val_idx])

    indexed_train = IndexedDataset(train_set)
    indexed_val = IndexedDataset(val_set)

    train_loader = DataLoader(indexed_train, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(indexed_val, batch_size=batch_size, shuffle=False)

    dataset_info = {
        "num_samples": len(train_set),
        "num_classes": len(classes),
        "class_names": classes,
        "sample_shape": (len(numeric_cols),)
    }

    return train_loader, val_loader, dataset_info
