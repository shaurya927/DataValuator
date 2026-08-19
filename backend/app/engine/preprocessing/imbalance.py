import pandas as pd
import numpy as np

class ImbalanceHandler:
    def __init__(self, strategy="none", task_type="classification"):
        self.strategy = strategy
        self.task_type = task_type

    def transform_train(self, X: pd.DataFrame, y: pd.Series):
        if self.strategy == "none" or self.task_type != "classification":
            return X.copy(), y.copy()
            
        if self.strategy == "random_undersample":
            min_class_count = y.value_counts().min()
            X_resampled = []
            y_resampled = []
            for cls in y.unique():
                idx = y[y == cls].sample(n=min_class_count, random_state=42).index
                X_resampled.append(X.loc[idx])
                y_resampled.append(y.loc[idx])
            X_out = pd.concat(X_resampled).sample(frac=1, random_state=42)
            y_out = pd.concat(y_resampled).loc[X_out.index]
            return X_out, y_out
            
        elif self.strategy == "random_oversample":
            max_class_count = y.value_counts().max()
            X_resampled = []
            y_resampled = []
            for cls in y.unique():
                idx = y[y == cls].sample(n=max_class_count, replace=True, random_state=42).index
                X_resampled.append(X.loc[idx])
                y_resampled.append(y.loc[idx])
            X_out = pd.concat(X_resampled).sample(frac=1, random_state=42)
            y_out = pd.concat(y_resampled).loc[X_out.index]
            # When we oversample, index will have duplicates. Reset index to ensure uniqueness,
            # but wait, the pipeline expects us to maintain original indices where possible.
            # However, for SMOTE/Oversampling, new samples are generated. 
            # We will use negative indices to mark synthetic samples in pipeline.
            return X_out, y_out
            
        elif self.strategy == "smote":
            try:
                from imblearn.over_sampling import SMOTE
                # SMOTE requires all numerical data. We assume categorical encoding was done.
                # Find if any non-numeric columns remain
                if not X.select_dtypes(exclude=[np.number]).empty:
                    # SMOTE fails with string data. Fallback to none.
                    print("Warning: SMOTE requires all numeric data. Returning original.")
                    return X.copy(), y.copy()
                    
                # SMOTE also fails if there are NaNs.
                if X.isnull().values.any():
                    print("Warning: SMOTE requires no missing values. Returning original.")
                    return X.copy(), y.copy()
                
                # Check if we have at least 6 samples per class (default k_neighbors=5)
                min_class_count = y.value_counts().min()
                k_neighbors = min(5, min_class_count - 1)
                
                if k_neighbors < 1:
                    print("Warning: Not enough samples for SMOTE. Returning original.")
                    return X.copy(), y.copy()
                    
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_res, y_res = smote.fit_resample(X, y)
                
                # Assign negative indices for synthetic samples
                original_len = len(X)
                synthetic_len = len(X_res) - original_len
                
                X_out = pd.DataFrame(X_res, columns=X.columns)
                y_out = pd.Series(y_res, name=y.name)
                
                # Original index for real ones, negative for synthetic ones
                new_idx = list(X.index) + list(range(-1, -synthetic_len - 1, -1))
                X_out.index = new_idx
                y_out.index = new_idx
                
                return X_out, y_out
            except ImportError:
                print("Warning: imblearn not installed. Cannot perform SMOTE.")
                return X.copy(), y.copy()
                
        return X.copy(), y.copy()
