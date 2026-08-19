import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from .missing_values import MissingValueImputer
from .categorical_encoding import CategoricalEncoder
from .scaling import NumericalScaler
from .transformations import FeatureTransformer
from .outliers import OutlierHandler
from .feature_selection import FeatureSelector
from .imbalance import ImbalanceHandler

def build_and_run_pipeline(df: pd.DataFrame, target_column: str, config: dict, is_inference=False):
    """
    Runs the preprocessing pipeline.
    If is_inference=False (default for training), we split into Train/Test, 
    fit transformers on Train, and transform both.
    If is_inference=True (for downloading preprocessed data), we fit on the entire dataset and return a single df.
    """
    df_raw = df.copy()
    
    # 1. Target Column
    if not target_column or target_column not in df_raw.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")
        
    df_raw = df_raw.dropna(subset=[target_column])
    
    # 2. Drop columns
    drop_cols = config.get("drop_columns", [])
    if isinstance(drop_cols, str):
        drop_cols = [c.strip() for c in drop_cols.split(",") if c.strip()]
    drop_cols = [c for c in drop_cols if c in df_raw.columns and c != target_column]
    if drop_cols:
        df_raw = df_raw.drop(columns=drop_cols)
        
    # 3. Duplicate handling
    if config.get("duplicate_handling") == "remove":
        df_raw = df_raw.drop_duplicates()
        
    # Keep track of original indices
    df_raw["__original_idx__"] = df_raw.index
    
    y_raw = df_raw[target_column]
    X_raw = df_raw.drop(columns=[target_column])
    
    task_type = config.get("task_type", "classification")
    
    if task_type == "classification":
        le = LabelEncoder()
        y_raw = pd.Series(le.fit_transform(y_raw), index=y_raw.index, name=y_raw.name)
        classes = list(le.classes_)
    else:
        y_raw = y_raw.astype(float)
        classes = []
        
    test_size = float(config.get("test_size", 0.2))
    random_seed = int(config.get("random_seed", 42))
    
    # Train / Test Split
    if is_inference:
        X_train = X_raw.copy()
        y_train = y_raw.copy()
        X_test = pd.DataFrame()
        y_test = pd.Series(dtype=float)
    else:
        split_strategy = config.get("split_strategy", "random")
        stratify = y_raw if (task_type == "classification" and split_strategy == "stratified") else None
        
        # Check if any class has less than 2 samples (stratify will fail)
        if stratify is not None:
            if stratify.value_counts().min() < 2:
                stratify = None
                
        X_train, X_test, y_train, y_test = train_test_split(
            X_raw, y_raw, test_size=test_size, random_state=random_seed, stratify=stratify
        )
        
    # Preprocessing components
    imputer = MissingValueImputer(strategy=config.get("imputation_strategy", "mean"))
    encoder = CategoricalEncoder(strategy=config.get("categorical_encoding", "onehot"))
    scaler = NumericalScaler(strategy=config.get("scaling", "standard"))
    transformer = FeatureTransformer(strategy=config.get("transformation", "none"))
    outlier_handler = OutlierHandler(
        detection=config.get("outlier_detection", "none"),
        treatment=config.get("outlier_treatment", "none")
    )
    feature_selector = FeatureSelector(
        strategy=config.get("feature_selection", "none"),
        task_type=task_type
    )
    imbalance_handler = ImbalanceHandler(
        strategy=config.get("imbalance_strategy", "none"),
        task_type=task_type
    )
    
    # Identify initial cols
    def get_col_types(X_df):
        num = X_df.select_dtypes(include=[np.number]).columns.tolist()
        num = [c for c in num if c != "__original_idx__"]
        cat = X_df.select_dtypes(exclude=[np.number]).columns.tolist()
        cat = [c for c in cat if c != "__original_idx__"]
        return num, cat
        
    # --- FIT AND TRANSFORM TRAIN ---
    # 1. Impute
    num_cols, cat_cols = get_col_types(X_train)
    X_train = imputer.fit(X_train, num_cols, cat_cols).transform(X_train)
    
    # 2. Outliers (Remove or clip)
    num_cols, cat_cols = get_col_types(X_train)
    X_train = outlier_handler.fit(X_train, num_cols).transform(X_train, is_train=True)
    # y_train must match X_train
    y_train = y_train.loc[X_train.index]
    
    # 3. Categorical encoding
    num_cols, cat_cols = get_col_types(X_train)
    X_train = encoder.fit(X_train, cat_cols, y_train).transform(X_train)
    
    # 4. Feature Transformations
    num_cols, cat_cols = get_col_types(X_train)
    X_train = transformer.fit(X_train, num_cols).transform(X_train)
    
    # 5. Scaling
    num_cols, cat_cols = get_col_types(X_train)
    X_train = scaler.fit(X_train, num_cols).transform(X_train)
    
    # 6. Feature Selection
    X_train = feature_selector.fit(X_train, y_train).transform(X_train)
    
    # 7. Imbalance (SMOTE, Over/Undersample)
    X_train, y_train = imbalance_handler.transform_train(X_train, y_train)
    
    # Extract training tracking indices and final arrays
    train_orig_idx = X_train["__original_idx__"].values.astype(int)
    X_train = X_train.drop(columns=["__original_idx__"])
    X_train_arr = X_train.values.astype(np.float32)
    y_train_arr = y_train.values
    if task_type == "classification":
        y_train_arr = y_train_arr.astype(int)
    else:
        y_train_arr = y_train_arr.astype(np.float32)
        
    # --- TRANSFORM TEST ---
    if not is_inference and len(X_test) > 0:
        X_test = imputer.transform(X_test)
        X_test = outlier_handler.transform(X_test, is_train=False) # clip only
        X_test = encoder.transform(X_test)
        X_test = transformer.transform(X_test)
        X_test = scaler.transform(X_test)
        X_test = feature_selector.transform(X_test)
        
        test_orig_idx = X_test["__original_idx__"].values.astype(int)
        X_test = X_test.drop(columns=["__original_idx__"])
        X_test_arr = X_test.values.astype(np.float32)
        y_test_arr = y_test.values
        if task_type == "classification":
            y_test_arr = y_test_arr.astype(int)
        else:
            y_test_arr = y_test_arr.astype(np.float32)
    else:
        X_test_arr = np.array([], dtype=np.float32)
        y_test_arr = np.array([], dtype=np.float32)
        test_orig_idx = np.array([], dtype=int)
        
    # Return structure
    res = {
        "train": (X_train_arr, y_train_arr, train_orig_idx),
        "test": (X_test_arr, y_test_arr, test_orig_idx),
        "features": list(X_train.columns),
        "classes": classes,
        "num_classes": len(classes) if task_type == "classification" else 1,
        "sample_shape": (X_train_arr.shape[1],) if X_train_arr.size > 0 else (0,)
    }
    
    # If downloading full inference dataframe
    if is_inference:
        df_out = X_train.copy()
        df_out[target_column] = y_train
        return df_out
        
    return res
