import torch
import torch.nn as nn
import torchvision.models as torchvision_models
from typing import Any, Dict, Optional
import numpy as np

from .base import BaseModel
from app.engine.trainer import DataValuatorTrainer
from app.engine.data_loader import create_pytorch_dataloaders

class SimpleCNN(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc1 = nn.Linear(128, 128)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, num_classes)
        
        self.feature_layer_name = 'fc1'

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = torch.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

def get_resnet18(num_classes: int, pretrained: bool = False) -> nn.Module:
    weights = torchvision_models.ResNet18_Weights.DEFAULT if pretrained else None
    model = torchvision_models.resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.feature_layer_name = 'layer4'
    return model

class SimpleTabularNet(nn.Module):
    def __init__(self, input_dim: int, num_classes: int, task_type: str = "classification"):
        super().__init__()
        self.task_type = task_type
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        out_dim = num_classes if task_type == "classification" else 1
        self.fc3 = nn.Linear(64, out_dim)
        self.feature_layer_name = 'fc2'

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class PyTorchModelAdapter(BaseModel):
    def __init__(self, model: nn.Module, task_type: str):
        self.model = model
        self.task_type = task_type
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def train(self, train_data: Any, val_data: Optional[Any] = None, config: Optional[Dict] = None, progress_callback=None, cancel_event=None) -> Dict[str, Any]:
        if isinstance(train_data, tuple) and isinstance(train_data[0], np.ndarray):
            if len(train_data) == 3:
                X_train, y_train, train_idx = train_data
                X_val, y_val, val_idx = val_data
            else:
                X_train, y_train = train_data
                X_val, y_val = val_data
            train_loader, val_loader = create_pytorch_dataloaders(X_train, y_train, X_val, y_val, self.task_type)
            original_num_samples = len(X_train)
        else:
            train_loader = train_data
            val_loader = val_data
            original_num_samples = len(train_loader.dataset)
            
        config = config or {}
        config.setdefault("original_num_samples", original_num_samples)
        
        # We need to adapt the trainer's criterion based on task_type if it's regression, 
        # but current trainer hardcodes nn.CrossEntropyLoss(reduction="none"). 
        # We will modify trainer.py directly for regression support soon, but for now 
        # trainer will use CrossEntropy which is bad for regression.
        # I'll create a quick monkey-patch or configure trainer.py later.
        
        trainer = DataValuatorTrainer(
            model=self.model,
            train_loader=train_loader,
            val_loader=val_loader,
            config=config,
            device=str(self.device),
            progress_callback=progress_callback,
            cancel_event=cancel_event
        )
        
        if self.task_type == "regression":
            trainer.criterion = nn.MSELoss(reduction="none")
            
        results = trainer.train()
        results["model"] = self
        return results

    def predict(self, X: Any) -> Any:
        self.model.eval()
        self.model.to(self.device)
        with torch.no_grad():
            if isinstance(X, np.ndarray):
                X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
            else:
                X_t = X.to(self.device)
            out = self.model(X_t)
            
            if self.task_type == "classification":
                return out.argmax(dim=1).cpu().numpy()
            else:
                return out.cpu().numpy()
                
    def evaluate(self, X: Any, y: Any) -> float:
        preds = self.predict(X)
        if self.task_type == "classification":
            from sklearn.metrics import accuracy_score
            return float(accuracy_score(y, preds))
        else:
            from sklearn.metrics import r2_score
            return float(max(0.0, r2_score(y, preds)))
            
    @property
    def supported_valuation_method(self) -> str:
        return "tracin"

def get_pytorch_model(name: str, task_type: str, **kwargs) -> BaseModel:
    if name == 'simple_cnn':
        return PyTorchModelAdapter(SimpleCNN(kwargs.get('num_classes', 10)), task_type)
    elif name == 'resnet18':
        return PyTorchModelAdapter(get_resnet18(kwargs.get('num_classes', 10), pretrained=kwargs.get('pretrained', False)), task_type)
    elif name == 'tabular':
        input_dim = kwargs.get('input_dim')
        if input_dim is None:
            raise ValueError("input_dim must be provided for SimpleTabularNet")
        return PyTorchModelAdapter(SimpleTabularNet(input_dim, kwargs.get('num_classes', 2), task_type), task_type)
    else:
        raise ValueError(f"Unknown PyTorch model: {name}")
