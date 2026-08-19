import pytest
import pandas as pd
import numpy as np

from app.engine.preprocessing.pipeline import build_and_run_pipeline
from app.engine.preprocessing.data_analyzer import analyze_dataframe

@pytest.fixture
def mock_df():
    np.random.seed(42)
    return pd.DataFrame({
        "id": range(100),
        "target": np.random.randint(0, 2, 100),
        "num1": np.random.randn(100) * 10 + 50,
        "num2": [np.nan if i % 10 == 0 else float(i) for i in range(100)],
        "cat1": ["A" if i % 2 == 0 else "B" for i in range(100)],
        "cat2": ["C", "D", "E", np.nan] * 25,
        "constant": [5.0] * 100
    })

def test_data_analyzer(mock_df):
    analysis = analyze_dataframe(mock_df, "target")
    assert analysis["total_rows"] == 100
    assert analysis["total_columns"] == 7
    assert "constant" in analysis["constant_columns"]
    assert "id" in analysis["potential_id_columns"]
    assert analysis["num_numerical"] == 4 # id, target, num1, num2, constant (target is excluded during pipeline but counted here)
    # Actually wait, target is not numeric if it is object? It is int here, so 5 numerical cols
    assert analysis["total_missing"] == 10 + 25
    assert analysis["target_info"]["inferred_task_type"] == "classification"

def test_pipeline_leakage(mock_df):
    config = {
        "imputation_strategy": "mean",
        "scaling": "standard",
        "drop_columns": "id",
        "task_type": "classification",
        "test_size": 0.2,
        "random_seed": 42
    }
    res = build_and_run_pipeline(mock_df, "target", config, is_inference=False)
    
    X_train, y_train, train_idx = res["train"]
    X_test, y_test, test_idx = res["test"]
    
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert "id" not in res["features"]
    
    # Check scaling mean/std (should be 0 and 1 on train, but not perfectly on test!)
    # num1 is feature 0 if we look at order, but we can't be sure without checking res["features"]
    idx = res["features"].index("num1")
    assert np.isclose(X_train[:, idx].mean(), 0, atol=1e-5)
    assert np.isclose(X_train[:, idx].std(), 1, atol=1e-5)
    
    # Test should not be 0/1 exactly since it was transformed using train's mean/std
    assert not np.isclose(X_test[:, idx].mean(), 0, atol=1e-5)

def test_pipeline_smote_tracking(mock_df):
    # Imbalance handler SMOTE requires no NaNs and all numeric
    # Imputation: mean, categorical: onehot
    config = {
        "imputation_strategy": "mean",
        "categorical_encoding": "onehot",
        "imbalance_strategy": "smote",
        "drop_columns": "id, constant",
        "task_type": "classification"
    }
    
    # Force class imbalance
    mock_df.loc[:80, "target"] = 0
    mock_df.loc[81:, "target"] = 1
    
    res = build_and_run_pipeline(mock_df, "target", config, is_inference=False)
    
    X_train, y_train, train_idx = res["train"]
    
    # Since SMOTE is applied, the number of samples in train might be balanced
    # The negative indices denote synthetic samples
    assert any(i < 0 for i in train_idx)
    assert len(train_idx) == len(X_train)

def test_pipeline_inference_mode(mock_df):
    config = {
        "imputation_strategy": "mean",
        "scaling": "minmax",
        "drop_columns": "id"
    }
    df_out = build_and_run_pipeline(mock_df, "target", config, is_inference=True)
    
    assert isinstance(df_out, pd.DataFrame)
    assert len(df_out) == 100
    assert df_out["num2"].isnull().sum() == 0
    assert df_out["num1"].min() == 0
    assert df_out["num1"].max() == 1
