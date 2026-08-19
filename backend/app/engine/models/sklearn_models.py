import numpy as np
from typing import Any, Dict, Optional
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from .base import BaseModel



class SklearnModelAdapter(BaseModel):
    def __init__(self, model, task_type: str):
        self.model = model
        self.task_type = task_type
        self.name = model.__class__.__name__
        
    def train(self, train_data: Any, val_data: Optional[Any] = None, config: Optional[Dict] = None, progress_callback=None, cancel_event=None) -> Dict[str, Any]:
        if isinstance(train_data, tuple):
            if len(train_data) == 3:
                X_train, y_train, train_idx = train_data
                if val_data is not None:
                    X_val, y_val, val_idx = val_data
            else:
                X_train, y_train = train_data
                if val_data is not None:
                    X_val, y_val = val_data
        
        if progress_callback:
            progress_callback(0, 0.0, 0.0, f"Training {self.name}...")
            
        self.model.fit(X_train, y_train)
        
        train_metric = self.evaluate(X_train, y_train)
        val_metric = 0.0
        if val_data:
            if isinstance(val_data, tuple) and len(val_data) == 3:
                X_val, y_val, val_idx = val_data
            else:
                X_val, y_val = val_data
            val_metric = self.evaluate(X_val, y_val)
            
        if progress_callback:
            progress_callback(1, 0.0, val_metric, "Training completed.")
            
        return {
            "model": self,
            "final_train_loss": 0.0,
            "final_val_accuracy": val_metric,
            "forgetting_counts": np.zeros(len(X_train), dtype=np.int32),
            "avg_loss": np.zeros(len(X_train), dtype=np.float32),
            "aum_scores": np.zeros(len(X_train), dtype=np.float32),
        }
        
    def predict(self, X: Any) -> Any:
        return self.model.predict(X)
        
    def evaluate(self, X: Any, y: Any) -> float:
        from sklearn.metrics import accuracy_score, r2_score
        preds = self.predict(X)
        if self.task_type == "classification":
            return float(accuracy_score(y, preds))
        else:
            return float(max(0.0, r2_score(y, preds)))
            
    @property
    def supported_valuation_method(self) -> str:
        return "leave_one_out_approx"

def get_sklearn_model(name: str, task_type: str, **kwargs) -> BaseModel:
    if name == "logistic_regression" and task_type == "classification":
        return SklearnModelAdapter(LogisticRegression(max_iter=1000), task_type)
    elif name == "linear_regression" and task_type == "regression":
        return SklearnModelAdapter(LinearRegression(), task_type)
    elif name == "decision_tree":
        if task_type == "classification":
            return SklearnModelAdapter(DecisionTreeClassifier(max_depth=10, random_state=42), task_type)
        else:
            return SklearnModelAdapter(DecisionTreeRegressor(max_depth=10, random_state=42), task_type)
    elif name == "random_forest":
        if task_type == "classification":
            return SklearnModelAdapter(RandomForestClassifier(n_estimators=100, random_state=42), task_type)
        else:
            return SklearnModelAdapter(RandomForestRegressor(n_estimators=100, random_state=42), task_type)

    else:
        raise ValueError(f"Unknown sklearn model {name} for task {task_type}")
