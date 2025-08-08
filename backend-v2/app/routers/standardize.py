from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.standardize import zscore_df, compute_diagnostics


class ZscoreRequest(BaseModel):
    by: List[str] = Field(default_factory=lambda: ["date"])  # MVP default
    winsor: Optional[List[float]] = Field(default_factory=lambda: [0.01, 0.99])
    fill: str = "median"  # median|zero|drop
    value_col: str = "factor"
    data: List[Dict[str, Any]]


class ZscoreResponse(BaseModel):
    data: List[Dict[str, Any]]
    diagnosis: Dict[str, Any]


router = APIRouter(prefix="/standardize", tags=["standardize"])


@router.post("/zscore", response_model=ZscoreResponse)
def zscore_endpoint(req: ZscoreRequest) -> Any:
    df = pd.DataFrame(req.data)
    if df.empty:
        return ZscoreResponse(data=[], diagnosis={})
    df = zscore_df(df, value_col=req.value_col, by=req.by, winsor=req.winsor, fill=req.fill)
    diag = compute_diagnostics(df[req.value_col])
    return ZscoreResponse(data=df.to_dict(orient="records"), diagnosis=diag)
