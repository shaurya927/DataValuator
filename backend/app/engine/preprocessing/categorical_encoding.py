import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

class CategoricalEncoder:
    def __init__(self, strategy="none"):
        self.strategy = strategy
        self.cat_cols = []
        self.encoder = None
        # Used for frequency encoding
        self.freq_maps = {}
        # Used for target encoding
        self.target_maps = {}
        self.global_target_mean = 0

    def fit(self, df: pd.DataFrame, cat_cols: list, y: pd.Series = None):
        self.cat_cols = [c for c in cat_cols if c in df.columns]
        if not self.cat_cols or self.strategy == "none":
            return self

        if self.strategy == "onehot":
            self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            self.encoder.fit(df[self.cat_cols].astype(str))
        elif self.strategy == "ordinal":
            # handle_unknown='use_encoded_value' is safe for unseen categories
            self.encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            self.encoder.fit(df[self.cat_cols].astype(str))
        elif self.strategy == "frequency":
            for col in self.cat_cols:
                self.freq_maps[col] = df[col].value_counts(normalize=True).to_dict()
        elif self.strategy == "target" and y is not None:
            self.global_target_mean = y.mean() if pd.api.types.is_numeric_dtype(y) else 0
            for col in self.cat_cols:
                if pd.api.types.is_numeric_dtype(y):
                    mapping = y.groupby(df[col]).mean().to_dict()
                else:
                    # Binary classification approximation: probability of most common class
                    most_common = y.mode()[0]
                    mapping = (y == most_common).groupby(df[col]).mean().to_dict()
                self.target_maps[col] = mapping

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_out = df.copy()
        if not self.cat_cols or self.strategy == "none":
            return df_out

        if self.strategy == "onehot":
            encoded = self.encoder.transform(df_out[self.cat_cols].astype(str))
            encoded_df = pd.DataFrame(encoded, columns=self.encoder.get_feature_names_out(self.cat_cols), index=df_out.index)
            df_out = df_out.drop(columns=self.cat_cols).join(encoded_df)
        elif self.strategy == "ordinal":
            encoded = self.encoder.transform(df_out[self.cat_cols].astype(str))
            df_out[self.cat_cols] = encoded
        elif self.strategy == "frequency":
            for col in self.cat_cols:
                # Fill unseen with 0
                df_out[col] = df_out[col].map(self.freq_maps[col]).fillna(0.0)
        elif self.strategy == "target":
            for col in self.cat_cols:
                df_out[col] = df_out[col].map(self.target_maps[col]).fillna(self.global_target_mean)

        return df_out
