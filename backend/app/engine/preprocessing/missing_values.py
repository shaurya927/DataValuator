import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer

class MissingValueImputer:
    def __init__(self, strategy="none"):
        self.strategy = strategy
        self.num_imputer = None
        self.cat_imputer = None
        self.num_cols = []
        self.cat_cols = []
        
    def fit(self, df: pd.DataFrame, num_cols: list, cat_cols: list):
        self.num_cols = [c for c in num_cols if c in df.columns]
        self.cat_cols = [c for c in cat_cols if c in df.columns]
        
        if self.strategy == "none" or self.strategy == "drop":
            return self
            
        if self.strategy == "knn":
            if self.num_cols:
                self.num_imputer = KNNImputer(n_neighbors=5)
                self.num_imputer.fit(df[self.num_cols])
            if self.cat_cols:
                self.cat_imputer = SimpleImputer(strategy="most_frequent")
                self.cat_imputer.fit(df[self.cat_cols])
        else:
            if self.strategy in ["mean", "median", "most_frequent", "constant"]:
                num_strat = self.strategy if self.strategy in ["mean", "median", "most_frequent", "constant"] else "mean"
                cat_strat = self.strategy if self.strategy in ["most_frequent", "constant"] else "most_frequent"
                
                if self.num_cols:
                    fill_value = 0 if self.strategy == "constant" else None
                    self.num_imputer = SimpleImputer(strategy=num_strat, fill_value=fill_value)
                    self.num_imputer.fit(df[self.num_cols])
                if self.cat_cols:
                    fill_value = "missing" if self.strategy == "constant" else None
                    self.cat_imputer = SimpleImputer(strategy=cat_strat, fill_value=fill_value)
                    self.cat_imputer.fit(df[self.cat_cols])
        return self
        
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.strategy == "none":
            return df.copy()
            
        df_out = df.copy()
        
        if self.strategy == "drop":
            df_out = df_out.dropna()
            return df_out
            
        if self.strategy in ["ffill", "bfill"]:
            if self.strategy == "ffill":
                df_out = df_out.ffill()
            else:
                df_out = df_out.bfill()
            return df_out
            
        if self.num_imputer and self.num_cols:
            df_out[self.num_cols] = self.num_imputer.transform(df_out[self.num_cols])
            
        if self.cat_imputer and self.cat_cols:
            df_out[self.cat_cols] = self.cat_imputer.transform(df_out[self.cat_cols])
            
        return df_out
