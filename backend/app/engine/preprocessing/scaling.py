import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

class NumericalScaler:
    def __init__(self, strategy="none"):
        self.strategy = strategy
        self.scaler = None
        self.num_cols = []

    def fit(self, df: pd.DataFrame, num_cols: list):
        # In case OneHot added columns, we want to scale all current numeric columns,
        # but typical ML practice is to NOT scale OneHot columns.
        # So we only scale the original numeric columns that are still present.
        self.num_cols = [c for c in num_cols if c in df.columns]
        
        if not self.num_cols or self.strategy == "none":
            return self
            
        if self.strategy == "standard":
            self.scaler = StandardScaler()
        elif self.strategy == "minmax":
            self.scaler = MinMaxScaler()
        elif self.strategy == "robust":
            self.scaler = RobustScaler()
            
        if self.scaler:
            self.scaler.fit(df[self.num_cols])
            
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_out = df.copy()
        if not self.num_cols or not self.scaler or self.strategy == "none":
            return df_out
            
        cols = [c for c in self.num_cols if c in df_out.columns]
        if cols:
            df_out[cols] = self.scaler.transform(df_out[cols])
            
        return df_out
