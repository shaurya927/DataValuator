from .base import BaseModel
from .pytorch_models import get_pytorch_model
from .sklearn_models import get_sklearn_model

def get_model(name: str, task_type: str = "classification", **kwargs) -> BaseModel:
    """Registry factory for all models."""
    if name in ["logistic_regression", "linear_regression", "decision_tree", "random_forest"]:
        return get_sklearn_model(name, task_type, **kwargs)
    elif name in ["simple_cnn", "resnet18", "tabular"]:
        return get_pytorch_model(name, task_type, **kwargs)
    else:
        raise ValueError(f"Unknown model architecture: {name}")
