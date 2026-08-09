import torch
import torch.nn as nn
import torchvision.models as models

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
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.feature_layer_name = 'layer4'
    return model

class SimpleTabularNet(nn.Module):
    def __init__(self, input_dim: int, num_classes: int):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_classes)
        self.feature_layer_name = 'fc2'

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

def get_model(name: str, num_classes: int, **kwargs) -> nn.Module:
    """Registry function for models."""
    if name == 'simple_cnn':
        return SimpleCNN(num_classes)
    elif name == 'resnet18':
        return get_resnet18(num_classes, pretrained=kwargs.get('pretrained', False))
    elif name == 'tabular':
        input_dim = kwargs.get('input_dim')
        if input_dim is None:
            raise ValueError("input_dim must be provided for SimpleTabularNet")
        return SimpleTabularNet(input_dim, num_classes)
    else:
        raise ValueError(f"Unknown model name: {name}")
