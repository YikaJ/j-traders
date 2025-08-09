from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from .selection import SelectionSpec


class CodegenRequest(BaseModel):
    selection_slug: Optional[str] = None
    selection: Optional[SelectionSpec] = None
    user_factor_spec: str
    coding_prefs: Optional[Dict[str, Any]] = None


class CodegenResponse(BaseModel):
    code_text: str
    fields_used: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ValidateRequest(BaseModel):
    code_text: str
    required_fields: Optional[List[str]] = None
    selection: Optional[SelectionSpec] = None


class ValidateResponse(BaseModel):
    ok: bool
    fields_used: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TestNormalization(BaseModel):
    method: Literal["zscore", "robust_zscore", "rank", "minmax"] = "zscore"
    winsor: Optional[List[float]] = Field(default_factory=lambda: [0.01, 0.99])
    fill: Literal["median", "zero", "drop"] = "median"
    by: List[str] = Field(default_factory=lambda: ["date"])  # MVP placeholder


class TestRequest(BaseModel):
    selection_slug: Optional[str] = None
    selection: Optional[SelectionSpec] = None
    code_text: str
    params: Dict[str, Any] = Field(default_factory=dict)
    ts_codes: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    normalization: Optional[TestNormalization] = None
    top_n: int = 5


class TestDiagnosis(BaseModel):
    mean: Optional[float] = None
    std: Optional[float] = None
    skew: Optional[float] = None
    kurt: Optional[float] = None
    missing_rate: Optional[float] = None


class TestResponse(BaseModel):
    sample_rows: List[Dict[str, Any]]
    diagnosis: Dict[str, Any]


class SampleRequest(BaseModel):
    selection_slug: Optional[str] = None
    selection: Optional[SelectionSpec] = None
    ts_codes: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_n: int = 10


class SampleResponse(BaseModel):
    data: Dict[str, List[Dict[str, Any]]]
    notes: Optional[str] = None
