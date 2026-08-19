import pandas as pd
import numpy as np

def _is_potential_id(col_name: str, series: pd.Series) -> bool:
    name_lower = col_name.lower()
    if any(k in name_lower for k in ['id', 'uuid', 'guid', 'key', 'index']):
        return True
    
    # If categorical/object, and completely unique strings (or almost)
    if not pd.api.types.is_numeric_dtype(series):
        if series.nunique() == len(series):
            return True
        if len(series) > 0 and series.nunique() / len(series) > 0.95:
            return True
            
    # If numeric, and completely unique sequential or distinct values
    if pd.api.types.is_numeric_dtype(series):
        if series.nunique() == len(series) and series.dtype in [np.int32, np.int64]:
            # Maybe it's just an index
            if series.min() == 0 or series.min() == 1:
                if series.max() - series.min() == len(series) - 1:
                    return True
    return False

def analyze_dataframe(df: pd.DataFrame, target_column: str = None) -> dict:
    total_rows = len(df)
    total_columns = len(df.columns)
    
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    missing_by_col = df.isnull().sum()
    total_missing = int(missing_by_col.sum())
    cols_with_missing = int((missing_by_col > 0).sum())
    duplicate_rows = int(df.duplicated().sum())
    
    constant_columns = []
    potential_id_columns = []
    high_cardinality_cols = []
    
    columns_info = []
    for col in df.columns:
        series = df[col]
        n_unique = int(series.nunique(dropna=True))
        
        if n_unique <= 1:
            constant_columns.append(col)
            
        if _is_potential_id(col, series):
            potential_id_columns.append(col)
            
        if col in cat_cols and n_unique > 50 and n_unique < total_rows * 0.95:
            high_cardinality_cols.append(col)
            
        col_type = "numerical" if col in num_cols else "categorical"
        columns_info.append({
            "name": col,
            "type": col_type,
            "dtype": str(series.dtype),
            "missing": int(missing_by_col[col]),
            "unique": n_unique
        })
        
    analysis = {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "num_numerical": len(num_cols),
        "num_categorical": len(cat_cols),
        "total_missing": total_missing,
        "cols_with_missing": cols_with_missing,
        "duplicate_rows": duplicate_rows,
        "constant_columns": constant_columns,
        "potential_id_columns": potential_id_columns,
        "high_cardinality_cols": high_cardinality_cols,
        "columns": columns_info,
        "target_info": None
    }
    
    if target_column and target_column in df.columns:
        target_series = df[target_column]
        target_missing = int(target_series.isnull().sum())
        clean_target = target_series.dropna()
        n_unique_target = int(clean_target.nunique())
        
        # Infer task type
        # If numeric and many unique values -> regression, else classification
        task_type = "classification"
        if pd.api.types.is_numeric_dtype(clean_target) and n_unique_target > 20:
            task_type = "regression"
            
        target_info = {
            "name": target_column,
            "missing": target_missing,
            "inferred_task_type": task_type
        }
        
        if task_type == "classification":
            value_counts = clean_target.value_counts()
            total_clean = len(clean_target)
            
            classes = []
            for val, count in value_counts.items():
                classes.append({
                    "class": str(val),
                    "count": int(count),
                    "percentage": round(float(count) / total_clean * 100, 2)
                })
                
            imbalance_warning = False
            if len(classes) >= 2:
                # If smallest class is less than 10%
                if classes[-1]["percentage"] < 10.0:
                    imbalance_warning = True
                    
            target_info["num_classes"] = n_unique_target
            target_info["classes"] = classes
            target_info["imbalance_warning"] = imbalance_warning
        else:
            # Regression stats
            target_info["min"] = float(clean_target.min())
            target_info["max"] = float(clean_target.max())
            target_info["mean"] = float(clean_target.mean())
            target_info["median"] = float(clean_target.median())
            target_info["std"] = float(clean_target.std())
            
        analysis["target_info"] = target_info
        
    return analysis
