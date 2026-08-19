import pandas as pd
import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif, f_regression, mutual_info_classif, mutual_info_regression

class FeatureSelector:
    def __init__(self, strategy="none", task_type="classification", threshold=0.95, k=10):
        self.strategy = strategy
        self.task_type = task_type
        self.threshold = threshold
        self.k = k
        self.kept_features = []

    def fit(self, df: pd.DataFrame, y: pd.Series):
        if self.strategy == "none":
            self.kept_features = df.columns.tolist()
            return self
            
        if self.strategy == "constant":
            # Remove constant and near-constant (variance = 0)
            kept = []
            for col in df.columns:
                if df[col].nunique(dropna=True) > 1:
                    kept.append(col)
            self.kept_features = kept
            
        elif self.strategy == "correlation":
            # Remove highly correlated numerical features
            num_df = df.select_dtypes(include=[np.number])
            if not num_df.empty:
                corr_matrix = num_df.corr().abs()
                upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                to_drop = [column for column in upper.columns if any(upper[column] > self.threshold)]
                self.kept_features = [c for c in df.columns if c not in to_drop]
            else:
                self.kept_features = df.columns.tolist()
                
        elif self.strategy in ["selectkbest", "mutual_info"]:
            num_df = df.select_dtypes(include=[np.number])
            cat_cols = [c for c in df.columns if c not in num_df.columns]
            
            if not num_df.empty and y is not None:
                n_features = min(self.k, len(num_df.columns))
                
                # Impute missing values in numerical features just for selection
                from sklearn.impute import SimpleImputer
                imp = SimpleImputer(strategy="mean")
                X_temp = imp.fit_transform(num_df)
                
                if self.strategy == "selectkbest":
                    score_func = f_classif if self.task_type == "classification" else f_regression
                else: # mutual_info
                    score_func = mutual_info_classif if self.task_type == "classification" else mutual_info_regression
                    
                selector = SelectKBest(score_func=score_func, k=n_features)
                selector.fit(X_temp, y)
                
                selected_num = num_df.columns[selector.get_support()].tolist()
                self.kept_features = selected_num + cat_cols
            else:
                self.kept_features = df.columns.tolist()
                
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.strategy == "none" or not self.kept_features:
            return df.copy()
            
        cols_to_keep = [c for c in self.kept_features if c in df.columns]
        return df[cols_to_keep].copy()
