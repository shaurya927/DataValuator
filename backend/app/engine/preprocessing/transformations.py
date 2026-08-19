import pandas as pd
import numpy as np
from sklearn.preprocessing import PowerTransformer

class FeatureTransformer:
    def __init__(self, strategy="none"):
        self.strategy = strategy
        self.num_cols = []
        self.transformer = None

    def fit(self, df: pd.DataFrame, num_cols: list):
        self.num_cols = [c for c in num_cols if c in df.columns]
        
        if not self.num_cols or self.strategy == "none":
            return self
            
        if self.strategy == "yeo-johnson":
            self.transformer = PowerTransformer(method='yeo-johnson')
            self.transformer.fit(df[self.num_cols])
            
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_out = df.copy()
        if not self.num_cols or self.strategy == "none":
            return df_out
            
        cols = [c for c in self.num_cols if c in df_out.columns]
        if not cols:
            return df_out
            
        if self.strategy == "log1p":
            # log1p is stateless, so we just apply it. We take abs to avoid negative value issues.
            # Usually applied to non-negative skewed features.
            # Clip at 0 for safety
            safe_values = np.clip(df_out[cols].values, a_min=0, a_max=None)
            df_out[cols] = np.log1p(safe_values)
        elif self.strategy == "yeo-johnson" and self.transformer:
            df_out[cols] = self.transformer.transform(df_out[cols])
            
        return df_out
