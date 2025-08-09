from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class EndpointParam(BaseModel):
    name: str
    type: Literal["string", "int", "float", "date"]
    required: bool = False
    desc: Optional[str] = None


class EndpointField(BaseModel):
    name: str
    dtype: Literal["string", "int", "float", "date"]
    role: Literal["identifier", "timestamp", "measure", "attribute"]
    desc: Optional[str] = None
    measure_kind: Optional[str] = None
    unit: Optional[str] = None
    sign: Optional[Literal["higher_better", "lower_better", "ambivalent"]] = None
    tags: List[str] = Field(default_factory=list)


class RateLimit(BaseModel):
    qps: int = 8
    burst: int = 16


class EndpointMeta(BaseModel):
    name: str
    description: Optional[str] = None
    update_time: Optional[str] = None
    notes: Optional[str] = None
    source: str
    sdk: dict
    axis: str
    frequency: Literal["daily", "quarterly", "annual", "adhoc"]
    ids: List[str]
    params: List[EndpointParam]
    fields: List[EndpointField]
    rate_limit: Optional[RateLimit] = None
    examples: Optional[dict] = None
    # per-endpoint flags
    cache_enabled: bool = True
    rate_limit_enabled: bool = True


class RegistryEntry(BaseModel):
    name: str
    file: str


class Registry(BaseModel):
    version: str
    endpoints: List[RegistryEntry]
