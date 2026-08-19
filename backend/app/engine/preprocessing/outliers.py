import pandas as pd
import numpy as np

class OutlierHandler:
    def __init__(self, detection="none", treatment="none"):
        self.detection = detection
        self.treatment = treatment
        self.num_cols = []
        # Stores (lower_bound, upper_bound) per column
        self.bounds = {}

    def fit(self, df: pd.DataFrame, num_cols: list):
        self.num_cols = [c for c in num_cols if c in df.columns]
        
        if not self.num_cols or self.detection == "none" or self.treatment == "none":
            return self
            
        for col in self.num_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue
                
            if self.detection == "iqr":
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                self.bounds[col] = (lower, upper)
            elif self.detection == "zscore":
                mean = series.mean()
                std = series.std()
                if std > 0:
                    self.bounds[col] = (mean - 3 * std, mean + 3 * std)
                    
        return self

    def transform(self, df: pd.DataFrame, is_train: bool = False) -> pd.DataFrame:
        df_out = df.copy()
        if not self.num_cols or self.detection == "none" or self.treatment == "none":
            return df_out
            
        if self.treatment == "clip":
            for col, (lower, upper) in self.bounds.items():
                if col in df_out.columns:
                    df_out[col] = df_out[col].clip(lower=lower, upper=upper)
        elif self.treatment == "remove" and is_train:
            # We ONLY remove outliers from training data, NOT test data
            mask = pd.Series(True, index=df_out.index)
            for col, (lower, upper) in self.bounds.items():
                if col in df_out.columns:
                    col_mask = (df_out[col] >= lower) & (df_out[col] <= upper) | df_out[col].isna()
                    mask = mask & col_mask
            df_out = df_out[mask]
            
        return df_out
