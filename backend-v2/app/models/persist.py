from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FactorCreate(BaseModel):
    name: str
    desc: Optional[str] = None
    code_text: str
    fields_used: List[str] = Field(default_factory=list)
    normalization: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    selection: Optional[Dict[str, Any]] = None


class FactorRecord(FactorCreate):
    id: int
    created_at: str


class StrategyCreate(BaseModel):
    name: str
    normalization: Optional[Dict[str, Any]] = None


class StrategyRecord(BaseModel):
    id: int
    name: str
    normalization: Optional[Dict[str, Any]] = None
    created_at: str
    weights: List[Dict[str, float]] = Field(default_factory=list)


class WeightItem(BaseModel):
    factor_id: int
    weight: float


class WeightsUpdate(BaseModel):
    weights: List[WeightItem]
    normalization: Optional[Dict[str, Any]] = None


class NormalizationUpdate(BaseModel):
    normalization: Dict[str, Any]
