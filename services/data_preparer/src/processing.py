import pandas as pd
from typing import List, Dict, Any
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from .schemas import PipelineStep

class DataProcessor:
    def process(self, df: pd.DataFrame, steps: List[PipelineStep]) -> pd.DataFrame:
        df_processed = df.copy()
        
        for step in steps:
            df_processed = self._apply_step(df_processed, step)
            
        return df_processed

    def _apply_step(self, df: pd.DataFrame, step: PipelineStep) -> pd.DataFrame:
        op = step.operator.lower()
        params = step.params or {}
        
        if op == "fillna":
            value = params.get("value", 0)
            value = params.get("value", 0)
            return df.fillna(value)

        elif op == "imputer":
            strategy = params.get("strategy", "most_frequent")
            
            if strategy == "most_frequent":
                # Apply to non-numeric columns (categorical)
                cat_cols = df.select_dtypes(include=['object', 'category']).columns
                if not cat_cols.empty:
                    imputer = SimpleImputer(strategy='most_frequent')
                    df[cat_cols] = imputer.fit_transform(df[cat_cols])
            
            elif strategy in ["mean", "median"]:
                # Apply to numeric columns
                num_cols = df.select_dtypes(include=['number']).columns
                if not num_cols.empty:
                    imputer = SimpleImputer(strategy=strategy)
                    df[num_cols] = imputer.fit_transform(df[num_cols])

            elif strategy == "constant_zero":
                 # Apply 0 to numeric columns only
                num_cols = df.select_dtypes(include=['number']).columns
                if not num_cols.empty:
                    df[num_cols] = df[num_cols].fillna(0)
            
            return df
            
        elif op == "drop_na":
            return df.dropna(**params)
            
        elif op == "standard_scaler":
            # Apply to numeric columns only
            scaler = StandardScaler(**params)
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if not numeric_cols.empty:
                df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            return df
            
        elif op == "minmax_scaler":
            scaler = MinMaxScaler(**params)
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if not numeric_cols.empty:
                df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            return df
            
        elif op == "get_dummies" or op == "one_hot":
            return pd.get_dummies(df, **params)
            
        else:
            print(f"Warning: Unknown operator {op}")
            return df

processor = DataProcessor()
