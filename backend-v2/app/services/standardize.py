from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class ZScoreConfig:
    winsor: Optional[List[float]] = None  # [low, high] quantiles
    fill: str = "median"  # median|zero|drop
    by: List[str] = None  # grouping keys


def _winsorize(series: pd.Series, q_low: float, q_high: float) -> pd.Series:
    if series.empty:
        return series
    lo = series.quantile(q_low)
    hi = series.quantile(q_high)
    return series.clip(lower=lo, upper=hi)


def _fill_missing(series: pd.Series, method: str) -> pd.Series:
    if method == "median":
        return series.fillna(series.median())
    if method == "zero":
        return series.fillna(0.0)
    if method == "drop":
        return series  # handled by caller
    return series


def zscore_df(df: pd.DataFrame, value_col: str, by: List[str], winsor: Optional[List[float]], fill: str) -> pd.DataFrame:
    result = df.copy()
    def _one_group(s: pd.Series) -> pd.Series:
        x = s
        if winsor and len(winsor) == 2:
            x = _winsorize(x, float(winsor[0]), float(winsor[1]))
        if fill == "drop":
            x = x.dropna()
        else:
            x = _fill_missing(x, fill)
        mu = x.mean()
        sd = x.std(ddof=0)
        if sd == 0 or np.isnan(sd):
            return pd.Series(np.zeros(len(s)), index=s.index)
        # compute using original index; reindex dropped values to NaN then fill again
        z = (s - mu) / sd
        if fill != "drop":
            z = _fill_missing(z, fill)
        return z

    result[value_col] = result.groupby(by, dropna=False)[value_col].transform(_one_group)
    return result


def compute_diagnostics(series: pd.Series) -> Dict[str, Any]:
    s = series.dropna()
    if s.empty:
        return {"mean": None, "std": None, "skew": None, "kurt": None, "missing_rate": 1.0}
    return {
        "mean": float(s.mean()),
        "std": float(s.std(ddof=0)),
        "skew": float(s.skew()) if len(s) >= 3 else None,
        "kurt": float(s.kurt()) if len(s) >= 4 else None,
        "missing_rate": float(1.0 - len(s) / series.shape[0]) if series.shape[0] > 0 else None,
    }
